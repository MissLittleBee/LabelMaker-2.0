import logging

from flask import Blueprint, jsonify, render_template, request
from flask.typing import ResponseReturnValue
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.db import db
from app.models import Form, Label
from app.utils import translate_db_error

logger = logging.getLogger(__name__)
bp = Blueprint("forms", __name__)

# Mapping of sort parameter to Form model column
_FORM_SORT_COLUMNS = {
    "name": Form.name,
    "short": Form.short_name,
}


def _get_sorted_forms(sort_by: str) -> list[Form]:
    """Return forms sorted by the given column key.

    Args:
        sort_by: Sort key from query string ('name' or 'short').

    Returns:
        List of Form records in requested order.
    """
    column = _FORM_SORT_COLUMNS.get(sort_by, Form.name)
    return Form.query.order_by(column.asc()).all()


@bp.route("/forms", methods=["GET"])
def list_forms() -> str:
    """Render forms management page."""
    logger.info("Rendering forms management page")
    sort_by = request.args.get("sort", "name")
    forms = _get_sorted_forms(sort_by)
    logger.debug(f"Loaded {len(forms)} forms for listing")
    return render_template(
        "forms/list_forms.html", forms=forms, sort_by=sort_by, active_page="forms"
    )


@bp.route("/api/form", methods=["POST"])
def create_form() -> ResponseReturnValue:
    """Create a new form."""
    try:
        logger.info("Received request to create new form")
        data = request.get_json()

        if not data:
            logger.warning("No JSON data provided in create form request")
            return jsonify({"error": "No JSON data provided"}), 400

        name = data.get("name", "").strip()
        short_name = data.get("short_name", "").strip()
        unit = data.get("unit", "").strip()

        missing_fields = [f for f in ["name", "short_name", "unit"] if not locals()[f]]
        if missing_fields:
            logger.warning(f"Missing required fields: {', '.join(missing_fields)}")
            return jsonify(
                {"error": f"Missing required fields: {', '.join(missing_fields)}"}
            ), 400

        form = Form(name=name, short_name=short_name, unit=unit)
        db.session.add(form)
        db.session.commit()
        logger.info(
            f"Form created successfully: {name} (short_name: {short_name}, unit: {unit})"
        )

        return jsonify(
            {"message": "Form created successfully", "form": form.to_dict()}
        ), 201

    except IntegrityError as e:
        logger.error(f"Integrity error creating form: {e}", exc_info=True)
        db.session.rollback()
        message, status_code = translate_db_error(e)
        return jsonify({"error": message}), status_code
    except SQLAlchemyError as e:
        logger.error(f"Database error creating form: {e}", exc_info=True)
        db.session.rollback()
        message, status_code = translate_db_error(e)
        return jsonify({"error": message}), status_code


@bp.route("/api/form", methods=["PUT"])
def update_form() -> ResponseReturnValue:
    """Edit form record."""
    try:
        logger.info("Received request to update form")
        data = request.get_json()

        if not data:
            logger.warning("No JSON data provided in update form request")
            return jsonify({"error": "No JSON data provided"}), 400

        name = data.get("name", "").strip()
        short_name = data.get("short_name", "").strip()
        unit = data.get("unit", "").strip()

        missing_fields = [f for f in ["name", "short_name", "unit"] if not locals()[f]]
        if missing_fields:
            logger.warning(f"Missing required fields: {', '.join(missing_fields)}")
            return jsonify(
                {"error": f"Missing required fields: {', '.join(missing_fields)}"}
            ), 400

        form = db.session.get(Form, name)
        if not form:
            logger.warning(f"Form not found: {name}")
            return jsonify({"error": "Form not found"}), 404

        logger.debug(f"Updating form {name}: short_name={short_name}, unit={unit}")
        form.short_name = short_name
        form.unit = unit
        db.session.commit()
        logger.info(f"Form updated successfully: {name}")

        return jsonify(
            {"message": "Form updated successfully", "form": form.to_dict()}
        ), 200

    except IntegrityError as e:
        logger.error(f"Integrity error updating form: {e}", exc_info=True)
        db.session.rollback()
        message, status_code = translate_db_error(e)
        return jsonify({"error": message}), status_code
    except SQLAlchemyError as e:
        logger.error(f"Database error updating form: {e}", exc_info=True)
        db.session.rollback()
        message, status_code = translate_db_error(e)
        return jsonify({"error": message}), status_code


@bp.route("/api/form", methods=["GET"])
def get_forms() -> ResponseReturnValue:
    """Get all forms."""
    try:
        logger.info("Fetching all forms")
        sort_by = request.args.get("sort", "name")
        forms = _get_sorted_forms(sort_by)
        logger.debug(f"Found {len(forms)} forms in database")
        forms_list = [form.to_dict() for form in forms]
        return jsonify({"forms": forms_list}), 200
    except SQLAlchemyError as e:
        logger.error(f"Error fetching forms: {e}", exc_info=True)
        message, status_code = translate_db_error(e)
        return jsonify({"error": message}), status_code


@bp.route("/api/form", methods=["DELETE"])
def delete_form() -> ResponseReturnValue:
    """Delete form record."""
    try:
        data = request.get_json()
        form_name = data.get("name")
        logger.info(f"Deleting form: {form_name}")

        form = db.session.get(Form, form_name)
        if not form:
            logger.warning(f"Form not found for deletion: {form_name}")
            return jsonify({"error": "Form not found"}), 404

        label_count = Label.query.filter_by(form=form.short_name).count()
        if label_count > 0:
            logger.warning(
                f"Cannot delete form '{form_name}': used by {label_count} label(s)"
            )
            return jsonify(
                {
                    "error": f"Nelze smazat formu '{form_name}' \u2014 je pou\u017e\u00edv\u00e1na {label_count} cenovkou/ami. "
                    f"Nejprve odstra\u0148te nebo p\u0159e\u0159a\u010fte p\u0159\u00edslu\u0161n\u00e9 cenovky."
                }
            ), 409

        db.session.delete(form)
        db.session.commit()
        logger.info(f"Form deleted successfully: {form_name}")
        return jsonify({"message": "Form deleted successfully"}), 200

    except SQLAlchemyError as e:
        logger.error(f"Error deleting form: {e}", exc_info=True)
        db.session.rollback()
        message, status_code = translate_db_error(e)
        return jsonify({"error": message}), status_code
