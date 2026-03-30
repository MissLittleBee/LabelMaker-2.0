import logging

from flask import Blueprint, jsonify, render_template, request, send_file
from flask.typing import ResponseReturnValue
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.constants import (
    LABEL_NOT_FOUND,
    PRICE_FONT_SIZE_MAX,
    PRICE_FONT_SIZE_MIN,
    TEXT_FONT_SIZE_MAX,
    TEXT_FONT_SIZE_MIN,
)
from app.db import db
from app.models import Form, Label
from app.pdf_generator import generate_labels_pdf
from app.utils import (
    calculate_unit_price,
    load_font_settings,
    save_font_settings,
    translate_db_error,
)

bp = Blueprint("labels", __name__, url_prefix="/labels")
logger = logging.getLogger(__name__)

# Mapping of sort parameter to Label query ordering
_LABEL_SORT_OPTIONS = {
    "name": lambda: Label.query.order_by(Label.product_name),
    "date": lambda: Label.query.order_by(Label.created_at.desc()),
    "marked": lambda: Label.query.order_by(
        Label.marked_to_print.desc(), Label.product_name
    ),
}


def _get_sorted_labels(sort_by: str) -> list[Label]:
    """Return labels sorted by the given column key.

    Args:
        sort_by: Sort key from query string ('name', 'date', or 'marked').

    Returns:
        List of Label records in requested order.
    """
    query_fn = _LABEL_SORT_OPTIONS.get(sort_by, _LABEL_SORT_OPTIONS["name"])
    return query_fn().all()


def _clamp(value: int, min_val: int, max_val: int) -> int:
    """Clamp an integer value between min and max bounds.

    Args:
        value: The value to clamp.
        min_val: Minimum allowed value.
        max_val: Maximum allowed value.

    Returns:
        Value clamped to [min_val, max_val].
    """
    return max(min_val, min(max_val, value))


def _enrich_label_with_unit(label_dict: dict, form_short_name: str) -> dict:
    """Enrich a label dict with unit from its form.

    Args:
        label_dict: Label data dictionary.
        form_short_name: The form's short_name to look up.

    Returns:
        Label dict with 'unit' field added.
    """
    form = Form.query.filter_by(short_name=form_short_name).first()
    if form:
        label_dict["unit"] = form.unit
    else:
        logger.warning(
            f"Form not found for short_name '{form_short_name}', defaulting to 'ks'"
        )
        label_dict["unit"] = "ks"
    return label_dict


# Route for /labels (list labels)
@bp.route("/", methods=["GET"])
def list_labels() -> str:
    """Show labels list page."""
    logger.info("Rendering labels list page")
    sort_by = request.args.get("sort", "name")
    labels = _get_sorted_labels(sort_by)
    forms = Form.query.all()
    logger.debug(f"Loaded {len(forms)} forms and {len(labels)} labels for listing")
    return render_template(
        "labels/list_labels.html",
        forms=forms,
        labels=labels,
        sort_by=sort_by,
        active_page="labels",
    )


@bp.route("/new", methods=["GET"])
def new_label_form() -> str:
    """Show form to create new label."""
    logger.info("Rendering new label form")
    forms = Form.query.all()
    logger.debug(f"Loaded {len(forms)} forms for new label form")
    return render_template(
        "labels/new_label.html", forms=forms, active_page="new_label"
    )


@bp.route("/api/label", methods=["POST"])
def create_label() -> ResponseReturnValue:
    """Create a new label."""
    try:
        logger.info("Received request to create new label")
        data = request.get_json()

        # Validate input
        if not data:
            logger.warning("No JSON data provided in create label request")
            return jsonify({"error": "No JSON data provided"}), 400

        product_name = data.get("product_name", "").strip()
        form = data.get("form", "").strip()
        amount = data.get("amount")
        price = data.get("price")
        marked_to_print = data.get("marked_to_print", False)

        # Check for missing fields and report which ones
        missing_fields = []
        if not product_name:
            missing_fields.append("product_name")
        if not form:
            missing_fields.append("form")
        if amount is None:
            missing_fields.append("amount")
        if price is None:
            missing_fields.append("price")

        if missing_fields:
            logger.warning(f"Missing required fields: {', '.join(missing_fields)}")
            return jsonify(
                {"error": f"Missing required fields: {', '.join(missing_fields)}"}
            ), 400

        # Validate and convert to float
        try:
            price = float(price)
            amount = float(amount)
            if amount <= 0:
                logger.warning(f"Invalid amount: {amount} (must be > 0)")
                return jsonify({"error": "Amount must be greater than 0"}), 400
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid number format: {e}")
            return jsonify({"error": "Price and amount must be valid numbers"}), 400

        # Validate form exists
        form_record = Form.query.filter_by(short_name=form).first()
        if not form_record:
            logger.warning(f"Form not found: short_name={form}")
            return jsonify({"error": f"Léková forma '{form}' neexistuje."}), 400

        # Calculate unit price
        unit_price = calculate_unit_price(amount, price)
        logger.debug(
            f"Calculated unit_price: {unit_price} for amount={amount}, price={price}"
        )

        # Create label
        label = Label(
            product_name=product_name,
            price=price,
            form=form,
            amount=amount,
            unit_price=unit_price,
            marked_to_print=marked_to_print,
        )
        db.session.add(label)
        db.session.commit()
        logger.info(
            f"Created label: {product_name} (ID: {label.id}, form: {form}, marked: {marked_to_print})"
        )

        return jsonify(
            {"message": "Label created successfully", "label": label.to_dict()}
        ), 201

    except IntegrityError as e:
        logger.error(f"Integrity error creating label: {e}", exc_info=True)
        db.session.rollback()
        message, status_code = translate_db_error(e)
        return jsonify({"error": message}), status_code
    except SQLAlchemyError as e:
        logger.error(f"Database error creating label: {e}", exc_info=True)
        db.session.rollback()
        message, status_code = translate_db_error(e)
        return jsonify({"error": message}), status_code


@bp.route("/api/labels", methods=["GET"])
def get_labels_api() -> ResponseReturnValue:
    """List all labels (API)."""
    try:
        logger.info("Fetching all labels")
        sort_by = request.args.get("sort", "name")
        labels = _get_sorted_labels(sort_by)
        logger.debug(f"Found {len(labels)} labels in database")
        labels_data = [label.to_dict() for label in labels]
        logger.info(f"Returning {len(labels_data)} labels.")
        return jsonify({"count": len(labels_data), "labels": labels_data}), 200
    except SQLAlchemyError as e:
        logger.error(f"Error fetching labels: {e}", exc_info=True)
        message, status_code = translate_db_error(e)
        return jsonify({"error": message}), status_code


@bp.route("/api/label/<int:label_id>", methods=["PUT"])
def update_label(label_id: int) -> ResponseReturnValue:
    """Update label information."""
    try:
        logger.info(f"Updating label ID: {label_id}")
        label = db.session.get(Label, label_id)
        if not label:
            logger.warning(f"{LABEL_NOT_FOUND}: ID {label_id}")
            return jsonify({"error": LABEL_NOT_FOUND}), 404

        data = request.get_json()
        if not data:
            logger.warning("No JSON data provided for label update")
            return jsonify({"error": "No JSON data provided"}), 400

        # Update fields if provided
        updated_fields = []
        if "product_name" in data:
            label.product_name = data["product_name"].strip()
            updated_fields.append("product_name")
        if "form" in data:
            new_form = data["form"].strip()
            form_record = Form.query.filter_by(short_name=new_form).first()
            if not form_record:
                logger.warning(f"Form not found: short_name={new_form}")
                return jsonify({"error": f"Léková forma '{new_form}' neexistuje."}), 400
            label.form = new_form
            updated_fields.append("form")
        if "amount" in data:
            label.amount = float(data["amount"])
            updated_fields.append("amount")
        if "price" in data:
            label.price = float(data["price"])
            updated_fields.append("price")

        # Recalculate unit price if price or amount changed
        if "price" in data or "amount" in data:
            label.unit_price = calculate_unit_price(label.amount, label.price)

        if "marked_to_print" in data:
            label.marked_to_print = data["marked_to_print"]
            updated_fields.append("marked_to_print")

        db.session.commit()
        logger.info(
            f"Label {label_id} updated successfully. Fields: {', '.join(updated_fields)}"
        )
        return jsonify(
            {"message": "Label updated successfully", "label": label.to_dict()}
        ), 200

    except IntegrityError as e:
        logger.error(f"Integrity error updating label {label_id}: {e}", exc_info=True)
        db.session.rollback()
        message, status_code = translate_db_error(e)
        return jsonify({"error": message}), status_code
    except SQLAlchemyError as e:
        logger.error(f"Database error updating label {label_id}: {e}", exc_info=True)
        db.session.rollback()
        message, status_code = translate_db_error(e)
        return jsonify({"error": message}), status_code


@bp.route("/api/label/<int:label_id>/toggle-print", methods=["POST"])
def toggle_print_mark(label_id: int) -> ResponseReturnValue:
    """Toggle print mark for a label."""
    try:
        logger.info(f"Toggling print mark for label ID: {label_id}")
        label = db.session.get(Label, label_id)
        if not label:
            logger.warning(f"{LABEL_NOT_FOUND} for toggle: ID {label_id}")
            return jsonify({"error": LABEL_NOT_FOUND}), 404

        old_value = label.marked_to_print
        label.marked_to_print = not label.marked_to_print
        db.session.commit()
        logger.info(
            f"Label {label_id} print mark toggled: {old_value} -> {label.marked_to_print}"
        )

        return jsonify(
            {"message": "Print mark toggled", "marked_to_print": label.marked_to_print}
        ), 200

    except SQLAlchemyError as e:
        logger.error(
            f"Error toggling print mark for label {label_id}: {e}", exc_info=True
        )
        db.session.rollback()
        message, status_code = translate_db_error(e)
        return jsonify({"error": message}), status_code


@bp.route("/api/labels/unmark-all", methods=["POST"])
def unmark_all_labels() -> ResponseReturnValue:
    """Unmark all labels from printing."""
    try:
        logger.debug("Unmarking all labels from printing")
        marked_labels = Label.query.filter_by(marked_to_print=True).all()
        count = len(marked_labels)

        for label in marked_labels:
            label.marked_to_print = False

        db.session.commit()
        logger.debug(f"Successfully unmarked {count} labels from printing")

        return jsonify(
            {"message": f"{count} cenovek odznačeno z tisku", "count": count}
        ), 200

    except SQLAlchemyError as e:
        logger.error(f"Error unmarking all labels: {e}", exc_info=True)
        db.session.rollback()
        message, status_code = translate_db_error(e)
        return jsonify({"error": message}), status_code


@bp.route("/api/label/<int:label_id>", methods=["DELETE"])
def delete_label(label_id: int) -> ResponseReturnValue:
    """Delete a label."""
    try:
        logger.info(f"Deleting label ID: {label_id}")
        label = db.session.get(Label, label_id)
        if not label:
            logger.warning(f"{LABEL_NOT_FOUND} for deletion: ID {label_id}")
            return jsonify({"error": LABEL_NOT_FOUND}), 404

        label_name = label.product_name
        db.session.delete(label)
        db.session.commit()
        logger.info(f"Label deleted successfully: ID {label_id}, Name: {label_name}")

        return jsonify({"message": "Label deleted successfully"}), 200

    except SQLAlchemyError as e:
        logger.error(f"Error deleting label {label_id}: {e}", exc_info=True)
        db.session.rollback()
        message, status_code = translate_db_error(e)
        return jsonify({"error": message}), status_code


@bp.route("/api/label/<int:label_id>", methods=["GET"])
def get_label(label_id: int) -> ResponseReturnValue:
    """Get a specific label by ID."""
    try:
        logger.debug(f"Fetching label ID: {label_id}")
        label = db.session.get(Label, label_id)
        if not label:
            logger.warning(f"{LABEL_NOT_FOUND}: ID {label_id}")
            return jsonify({"error": LABEL_NOT_FOUND}), 404
        logger.debug(f"Found label: {label.product_name}")
        return jsonify(label.to_dict()), 200
    except SQLAlchemyError as e:
        logger.error(f"Error fetching label {label_id}: {e}", exc_info=True)
        message, status_code = translate_db_error(e)
        return jsonify({"error": message}), status_code


@bp.route("/print", methods=["GET"])
def print_labels_page() -> str:
    """Show print labels page with preview."""
    logger.info("Rendering print labels page")
    # Get all labels marked for printing
    marked_labels = Label.query.filter_by(marked_to_print=True).all()
    logger.debug(f"Found {len(marked_labels)} labels marked for printing")
    font_settings = load_font_settings()
    return render_template(
        "labels/print_labels.html",
        labels=marked_labels,
        active_page="print",
        **font_settings,
    )


@bp.route("/api/pdf-font-settings", methods=["POST"])
def update_pdf_font_settings() -> ResponseReturnValue:
    """Update and persist PDF font size settings."""
    try:
        data = request.get_json() or {}
        price_font_size = int(data.get("price_font_size", 32))
        text_font_size = int(data.get("text_font_size", 14))

        if not (PRICE_FONT_SIZE_MIN <= price_font_size <= PRICE_FONT_SIZE_MAX):
            return jsonify(
                {
                    "error": f"Velikost písma ceny musí být {PRICE_FONT_SIZE_MIN}–{PRICE_FONT_SIZE_MAX}."
                }
            ), 400
        if not (TEXT_FONT_SIZE_MIN <= text_font_size <= TEXT_FONT_SIZE_MAX):
            return jsonify(
                {
                    "error": f"Velikost písma textu musí být {TEXT_FONT_SIZE_MIN}–{TEXT_FONT_SIZE_MAX}."
                }
            ), 400

        save_font_settings(price_font_size, text_font_size)
        return jsonify({"message": "Font settings updated."}), 200
    except (ValueError, TypeError) as e:
        logger.error(f"Invalid font settings: {e}", exc_info=True)
        return jsonify({"error": "Neplatné hodnoty písma."}), 400


@bp.route("/api/labels/pdf", methods=["GET"])
def generate_pdf_all_marked() -> ResponseReturnValue:
    """Generate PDF with all labels marked for printing."""
    try:
        logger.info("Generating PDF for all marked labels")

        # Get all labels marked for printing
        marked_labels = Label.query.filter_by(marked_to_print=True).all()

        if not marked_labels:
            logger.warning("No labels marked for printing")
            return jsonify({"error": "No labels marked for printing"}), 400

        logger.info(f"Generating PDF with {len(marked_labels)} marked labels")

        # Get global font size settings from query params (with defaults)
        # Load persistent font settings as defaults
        font_settings = load_font_settings()
        price_font_size = _clamp(
            int(request.args.get("price_font_size", font_settings["price_font_size"])),
            PRICE_FONT_SIZE_MIN,
            PRICE_FONT_SIZE_MAX,
        )
        text_font_size = _clamp(
            int(request.args.get("text_font_size", font_settings["text_font_size"])),
            TEXT_FONT_SIZE_MIN,
            TEXT_FONT_SIZE_MAX,
        )

        label_data = []
        for label in marked_labels:
            data = _enrich_label_with_unit(label.to_dict(), label.form)
            data["price_font_size"] = price_font_size
            data["text_font_size"] = text_font_size
            label_data.append(data)

        # Generate PDF
        pdf_buffer = generate_labels_pdf(label_data)

        if not pdf_buffer:
            logger.error("PDF generation failed")
            return jsonify({"error": "Failed to generate PDF"}), 500

        logger.info("PDF generated successfully, sending file")

        # Send PDF file
        return send_file(
            pdf_buffer,
            mimetype="application/pdf",
            as_attachment=True,
            download_name="price_labels.pdf",
        )

    except SQLAlchemyError as e:
        logger.error(f"Error generating PDF: {e}", exc_info=True)
        message, status_code = translate_db_error(e)
        return jsonify({"error": message}), status_code


@bp.route("/api/label/<int:label_id>/pdf", methods=["GET"])
def generate_pdf_single(label_id: int) -> ResponseReturnValue:
    """Generate PDF for a single label."""
    try:
        logger.info(f"Generating PDF for single label ID: {label_id}")

        label = db.session.get(Label, label_id)
        if not label:
            logger.warning(f"{LABEL_NOT_FOUND}: ID {label_id}")
            return jsonify({"error": LABEL_NOT_FOUND}), 404

        # Enrich label with form unit information
        data = _enrich_label_with_unit(label.to_dict(), label.form)

        # Generate PDF
        pdf_buffer = generate_labels_pdf([data])

        if not pdf_buffer:
            logger.error(f"PDF generation failed for label {label_id}")
            return jsonify({"error": "Failed to generate PDF"}), 500

        logger.info(f"PDF generated successfully for label {label_id}")

        # Send PDF file
        return send_file(
            pdf_buffer,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"label_{label_id}.pdf",
        )

    except SQLAlchemyError as e:
        logger.error(f"Error generating PDF for label {label_id}: {e}", exc_info=True)
        message, status_code = translate_db_error(e)
        return jsonify({"error": message}), status_code
