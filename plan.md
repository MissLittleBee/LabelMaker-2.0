# Bug Fix Plan — LabelMaker 2.0

---

## Bug 1: Label text overflows the label box when user chooses bigger font size

**Root cause:** In `app/pdf_generator.py`, the `draw_label()` method uses hard-coded Y positions calculated with `mm` units but doesn't account for how `price_font_size` or `text_font_size` affect the vertical space needed. When the user increases font sizes, text elements overlap each other or spill outside the 35mm label boundary. There's also no horizontal clipping — long product names or large price text can exceed the 48mm width.

**Fix (3 changes in `app/pdf_generator.py`):**

1. **Add text clipping to the label boundary** — Before drawing any text, set a clipping rectangle matching the label box (`x, y, LABEL_WIDTH, LABEL_HEIGHT`). This prevents any overflow from being visible outside the label.

2. **Auto-scale font sizes to fit** — After drawing text, measure its width using `pdf_canvas.stringWidth()`. If the rendered text exceeds `LABEL_WIDTH - 2*padding`, reduce the font size iteratively until it fits. Apply this to:
   - Product name lines (top section)
   - Price text (middle section)
   - Unit price text (bottom section)

3. **Dynamic vertical positioning** — Replace the hard-coded `mm`-based Y offsets with positions calculated relative to actual font metrics. Divide the label into 3 zones (top ~30%, middle ~40%, bottom ~30%) and center each text block within its zone based on the actual `text_font_size` and `price_font_size`.

**Files to modify:** `app/pdf_generator.py`

---

## Bug 2: No protection when deleting a Form that is used by Labels

**Root cause:** The `delete_form()` route in `app/routes/forms/forms_routes.py` deletes the form without checking if any `Label` records reference it via the `form` foreign key. This creates orphaned labels with broken references.

**Fix (2 changes):**

1. **Add dependency check before deletion** — In `delete_form()`, query `Label.query.filter_by(form=form.short_name).count()` before deleting. If count > 0, return a `409 Conflict` with a user-friendly message like:
   `"Cannot delete form '{name}' — it is used by {count} label(s). Remove or reassign those labels first."`

2. **Frontend confirmation with warning** — In `static/js/forms.js`, when the backend returns a 409, display the error in the toast notification so the user understands why deletion was blocked.

**Files to modify:** `app/routes/forms/forms_routes.py`, `static/js/forms.js`

---

## Bug 3: Raw database error messages shown to user (e.g. unique constraint)

**Root cause:** All route `except Exception` blocks in `app/routes/labels/label_routes.py` and `app/routes/forms/forms_routes.py` return `str(e)` directly, which exposes raw SQLAlchemy/SQLite error strings like:
`"UNIQUE constraint failed: label.product_name, label.form, label.amount"`

**Fix (2 changes):**

1. **Add an error translation helper** — Create a helper function `translate_db_error(error: Exception) -> str` in `app/utils.py` that pattern-matches common database errors and returns user-friendly messages:

   | Raw error | User-friendly message |
   |-----------|----------------------|
   | `UNIQUE constraint failed: label.product_name, label.form, label.amount` | `"Cenovka se stejným názvem, formou a množstvím již existuje."` |
   | `UNIQUE constraint failed: form.short_name` | `"Forma s touto zkratkou již existuje."` |
   | `UNIQUE constraint failed: form.name` | `"Forma s tímto názvem již existuje."` |
   | `FOREIGN KEY constraint` | `"Odkazovaný záznam neexistuje."` |
   | Fallback | `"Došlo k neočekávané chybě. Zkuste to prosím znovu."` |

2. **Use the helper in all route error handlers** — Replace `return jsonify({"error": str(e)}), 500` with `return jsonify({"error": translate_db_error(e)}), 409` (for constraint violations) or `500` (for others) in:
   - `create_label()`, `update_label()` in `app/routes/labels/label_routes.py`
   - `create_form()`, `update_form()` in `app/routes/forms/forms_routes.py`

**Files to modify:** `app/utils.py`, `app/routes/labels/label_routes.py`, `app/routes/forms/forms_routes.py`

---

## Bug 4: Web app is not responsive to browser window size

> **Context:** The application is used exclusively on **Windows PCs** — not on mobile phones or tablets. However, users may have older or smaller monitors (e.g. 1024×768 or 1280×1024), so the layout must adapt gracefully to smaller desktop screen resolutions. Mobile-specific patterns (hamburger menus, touch targets) are out of scope.

**Root cause:** The sidebar has a fixed 280px width and does not adapt to smaller desktop resolutions. Tables don't scroll horizontally when the viewport is too narrow. The `forms.css` and `home.css` files have their own conflicting `body` and layout styles that don't follow the main layout system.

**Fix (3 changes):**

1. **Improve sidebar responsive behavior for smaller desktop resolutions** in `static/css/main.css`:
   - At `≤1280px`: reduce sidebar width to ~220px
   - At `≤1024px`: reduce sidebar width to ~180px with smaller font/icon sizes, so the main content area retains enough usable space

2. **Make tables horizontally scrollable** — The `.table-container` already has `overflow-x: auto`, but ensure all table wrappers use this class. Add `min-width` to tables so columns don't collapse at lower resolutions.

3. **Unify CSS across pages** — Remove the duplicate `body`, `*`, `.container` styles from `static/css/forms.css` and `static/css/home.css` that conflict with `static/css/main.css`. These pages should inherit the shared layout and only add page-specific overrides.

**Files to modify:** `static/css/main.css`, `static/css/forms.css`, `static/css/home.css`, `static/css/labels.css`, all HTML templates that contain the sidebar

---

## Bug 5: Frontend XSS risk from unsafe HTML rendering in JS

> **Context:** Even as a localhost Windows desktop app, XSS is still relevant (malicious pasted/imported data, browser extensions, local malware, or manipulated local requests).

**Root cause:** Some frontend code inserts untrusted values into `innerHTML` without escaping. In particular:
- `static/js/forms.js` uses `unitDisplay[form.unit] || form.unit` directly in table row HTML.
- Toast rendering in `forms.js`, `list_labels.js`, `new_label.js` uses `toast.innerHTML` with message strings that may include backend-provided `data.error` text.

**Fix (3 changes):**

1. **Escape all dynamic table values before HTML insertion** — In `forms.js`, wrap `form.unit` with `escapeHtml()` before rendering fallback text.

2. **Replace toast `innerHTML` usage with safe DOM API** — Build toast content with `createElement()` and assign `textContent` for message and icon fields.

3. **Standardize safe notification helper** — Ensure all `showNotification()` implementations in `forms.js`, `list_labels.js`, and `new_label.js` use text-only rendering.

**Files to modify:** `static/js/forms.js`, `static/js/list_labels.js`, `static/js/new_label.js`

---

## Bug 6: Database integrity enforcement is incomplete (FK behavior + reference validation)

**Root cause:** Form deletion currently relies only on route-level logic. SQLite foreign key behavior can be inconsistent if foreign keys are not explicitly enabled per connection. Also, label create/update paths do not explicitly verify that `form` exists before commit.

**Fix (3 changes):**

1. **Enable SQLite foreign keys on each DB connection** — Add SQLAlchemy engine event hook to execute `PRAGMA foreign_keys = ON`.

2. **Validate form existence in label create/update routes** — In `create_label()` and `update_label()`, check `Form.query.filter_by(short_name=form).first()`; return `400` (or `404`) with a clear message if missing.

3. **Keep delete dependency check from Bug 2 as business rule** — Retain friendly `409` message on form delete attempts when labels depend on it.

**Files to modify:** `app/db.py` (or app init where engine events are configured), `app/routes/labels/label_routes.py`, `app/routes/forms/forms_routes.py`

---

## Bug 7: Unbounded PDF font size inputs can degrade performance

**Root cause:** `price_font_size` and `text_font_size` are parsed from request/query without strict min/max validation. Very large or negative values can cause poor rendering behavior, expensive layout loops, or unreadable output.

**Fix (3 changes):**

1. **Add strict bounds on backend** — Validate and clamp values, e.g.:
   - `price_font_size`: 12–48
   - `text_font_size`: 8–24

2. **Fail fast on invalid payload** — Return `400` with user-friendly validation errors instead of accepting out-of-range values.

3. **Guard auto-fit loop in PDF renderer** — Add max iteration cap and minimum font fallback when shrinking text.

**Files to modify:** `app/routes/labels/label_routes.py`, `app/pdf_generator.py`, optionally `templates/labels/print_labels.html` and related JS to limit UI inputs.

---

## Bug 8: Excessive request payload logging can leak data in logs

**Root cause:** Routes currently log full JSON payloads (`Request data: {data}`, `Update data: {data}`) at debug level. These logs may contain operational or sensitive content and persist in log files.

**Fix (2 changes):**

1. **Remove raw payload logs** — Replace with minimal structured metadata (e.g., field presence, counts, resource IDs).

2. **Mask sensitive/error-prone values** — Keep logs useful while avoiding storing free-form user input directly.

**Files to modify:** `app/routes/forms/forms_routes.py`, `app/routes/labels/label_routes.py`

---

## Summary & Priority

| # | Bug | Severity | Effort | Files |
|---|-----|----------|--------|-------|
| 1 | Text overflow in PDF labels | High | Medium | `app/pdf_generator.py` |
| 2 | Form delete breaks labels | High | Low | `app/routes/forms/forms_routes.py`, `static/js/forms.js` |
| 3 | Raw DB errors shown to user | Medium | Low | `app/utils.py`, `app/routes/labels/label_routes.py`, `app/routes/forms/forms_routes.py` |
| 4 | Not responsive | Medium | High | All CSS files, all HTML templates |
| 5 | Frontend XSS risk (unsafe `innerHTML`) | High | Medium | `static/js/forms.js`, `static/js/list_labels.js`, `static/js/new_label.js` |
| 6 | DB integrity enforcement incomplete | High | Medium | `app/db.py`, `app/routes/labels/label_routes.py`, `app/routes/forms/forms_routes.py` |
| 7 | Unbounded PDF font inputs | Medium | Low | `app/routes/labels/label_routes.py`, `app/pdf_generator.py` |
| 8 | Excessive payload logging | Low | Low | `app/routes/forms/forms_routes.py`, `app/routes/labels/label_routes.py` |
