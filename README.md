# LabelMaker 2.0

Modern web application primary for Czech pharmacy to generate price labels with czech language localization.

## 🎯 Features

- **Label Management** - Create, edit, and delete price labels
- **Form Management** - Manage pharmaceutical forms (tablets, drops, ointments, ...)
- **PDF Generation** - Print labels per A4 page (48×35mm, 0mm gaps)
- **Czech Support** - Full support for Czech characters (č, ř, ž, Č, Ř, Ž)
- **Smart Text Wrapping** - Automatic wrapping of long product names (max 25 chars/line)
- **Sorting** - Sort by name, date, or print status
- **Bulk Operations** - Mark/unmark all labels for printing

## 📋 Requirements

- Python 3.9 or newer
- Web browser (Chrome, Firefox, Edge, Safari)

## 🚀 Instalation

### Step 1: clone this repo

```bash
git clone <repository-url>
cd "LabelMaker 2.0"
```

### Step 2: Create venv (recommended)

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Run the application

```bash
python main.py
```

The application will:
- Start Flask server on **http://127.0.0.1:5000**
- Automatically open your default browser
- Create the SQLite database and logs automatically

**Output example:**
```
[2026-01-12 20:40:15] INFO     Starting LabelMaker 2.0...
[2026-01-12 20:40:15] INFO     LabelMaker application initialized successfully
 * Serving Flask app 'app.app'
 * Running on http://127.0.0.1:5000
```

## 🖨️ Usage

### Adding a pharmaceutical form
1. Click on "Lékové formy" (Forms)
2. Fill in name (e.g., "Tablety"), short name (e.g., "tbl"), and unit (e.g., "ks")
3. Click "Přidat formu" (Add form)

### Creating a label
1. Click on "Nová cenovka" (New label)
2. Fill in:
   - **Product name** - e.g., "Paralen 500mg"
   - **Pharmaceutical form** - select from dropdown
   - **Amount** - e.g., 24 (pieces)
   - **Price** - e.g., 89.50 Kč
3. Check "Označit k tisku" (Mark for printing) if you want to print immediately
4. Click "Přidat cenovku" (Add label)

### Printing labels
1. On the "Cenovky" (Labels) page, check the labels you want to print
2. Click "Tisknout označené" (Print marked)
3. Review the preview and click "Stáhnout PDF" (Download PDF)
4. Print the PDF on colored A4 paper

### Printing tips
- **Paper**: A4 colored paper (48×35mm labels)
- **Orientation**: Portrait
- **Margins**: 0mm (full bleed)
- **Scale**: 100% (no scaling)
- **Layout**: 32 labels (4 columns × 8 rows)

## 🛠️ Technologies

- **Backend**: Flask 3.0+ (Python web framework)
- **Database**: SQLite + SQLAlchemy ORM
- **PDF**: ReportLab with DejaVu Sans fonts
- **Frontend**: Vanilla JavaScript + CSS
- **Templating**: Jinja2

## 📦 Windows EXE Version

For creating a standalone Windows EXE file that users can double-click to run:

### Prerequisites
- Windows machine (or Windows CI runner like GitHub Actions)
- Python 3.9+ installed

### Build Steps

```bash
# 1. Create virtual environment
python -m venv venv
venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Build the EXE
python build_exe.py
```

**Output:** `dist\LabelMaker.exe` (single file, ~150MB)

### How it works
- **One-file bundle**: All Python code, templates, and static files embedded in the EXE
- **Auto-launch**: Double-clicking opens the app in default browser, starts Flask server
- **System tray**: Icon in Windows system tray to control and close the app
- **Persistent data**: Database stored in `%APPDATA%\LabelMaker\instance\` (survives reinstalls)

### Distribution
- Copy `dist\LabelMaker.exe` to users
- No Python installation required on user's PC
- Works on Windows 7+ (with modern OS)

**Note:** First run takes 5-10 seconds (extracting files to temp folder). Subsequent runs are faster.

## 🔧 Configuration

### Environment Variables (`.env` file)

Create a `.env` file in the project root:

```bash
# Debug mode (optional, default=true)
DEBUG=true

# Logging level (optional)
# When DEBUG=true: defaults to DEBUG
# When DEBUG=false: defaults to INFO
LOG_LEVEL=DEBUG  # Options: DEBUG, INFO, WARNING, ERROR

# Database path (optional, defaults to instance/labelmaker.db)
DATABASE_URL=sqlite:///path/to/custom.db

# Flask port (set in main.py instead)
PORT=5000
```

### Log Output
- **Console**: Real-time logs while running (see terminal output)
- **File**: Saved to `instance/logs/labelmaker.log` (rotating, max 2MB)

**Log levels:**
- `DEBUG` - Detailed info, SQL queries, form lookups (development)
- `INFO` - Application flow, user actions (default)
- `WARNING` - Potential issues
- `ERROR` - Errors that occurred

### Changing Port

Edit `main.py`, find this line:
```python
app.run(host="127.0.0.1", port=5000, debug=False)
```

Change `5000` to your desired port (e.g., `8080`).

## 🐛 Troubleshooting

### Port already in use
```bash
# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:5000 | xargs kill -9
```

### Database errors
```bash
# Delete database and start fresh
rm -rf instance/labelmaker.db
python main.py
```

### No DEBUG messages visible
- Check `.env` has `DEBUG=true`
- Restart the app after changing `.env`
- Logs are in `instance/logs/labelmaker.log`

### Foreign key constraint errors
- Delete database and recreate: `rm -rf instance/labelmaker.db`
- Ensure you create pharmaceutical forms before labels

### Form lookup shows "ks" instead of actual unit
- Delete database (schema changed): `rm -rf instance/labelmaker.db`
- Recreate forms and labels

### Czech characters not displaying in PDF
- The application uses DejaVu Sans fonts with full Czech support
- If missing, reinstall: `pip install reportlab --upgrade`

### Application won't start
```bash
# Check Python version (must be 3.9+)
python --version

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### EXE build fails
- Ensure you're on Windows (or use GitHub Actions to build)
- Delete `build/` and `dist/` folders and try again
- Check that all dependencies are installed: `pip install -r requirements.txt`

## 📝 Database Schema

### Table: `label` (Price Labels)
- `id` - Primary key (auto-increment)
- `product_name` - Product name
- `form` - Pharmaceutical form (foreign key)
- `amount` - Amount/quantity
- `price` - Price
- `unit_price` - Price per unit (auto-calculated)
- `marked_to_print` - Marked for printing (boolean)
- `created_at` - Creation date

### Table: `form` (Pharmaceutical Forms)
- `name` - Form name (primary key)
- `short_name` - Abbreviation (unique)
- `unit` - Unit (ks, ml, g, ...)

## 🤝 Contributing

1. Fork the project
2. Create your feature branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -m 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Open a Pull Request

## 📄 License

MIT

## 👨‍💻 Author

Barbora Hůlová

---

**Version**: 2.0  
**Date**: December 2025  
