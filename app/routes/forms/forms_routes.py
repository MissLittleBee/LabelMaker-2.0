import logging

from flask import Blueprint, jsonify, render_template, request

from app.db import db
from app.models import Form

logger = logging.getLogger(__name__)
bp = Blueprint("forms", __name__)


@bp.route("/forms", methods=["GET"])
def list_forms():
    """Render forms management page."""
    logger.info("Rendering forms management page")

    # Get sorting parameter from query string
    sort_by = request.args.get("sort", "name")  # Default: name
    logger.debug(f"Sorting forms by: {sort_by}")

    # Build query based on sorting option
    if sort_by == "name":
        forms = Form.query.order_by(Form.name).all()
    elif sort_by == "short":
        forms = Form.query.order_by(Form.short_name).all()
    else:
        forms = Form.query.order_by(Form.name).all()

    logger.debug(f"Loaded {len(forms)} forms for listing")
    return render_template("forms/list_forms.html", forms=forms, sort_by=sort_by)


@bp.route("/api/form", methods=["POST"])
def create_form():
    """Create a new form."""
    try:
        logger.info("Received request to create new form")
        data = request.get_json()
        logger.debug(f"Request data: {data}")

        # Validate input
        if not data:
            logger.warning("No JSON data provided in create form request")
            return jsonify({"error": "No JSON data provided"}), 400

        name = data.get("name", "").strip()
        short_name = data.get("short_name", "").strip()
        unit = data.get("unit", "").strip()

        # Check for missing fields and report which ones
        missing_fields = []
        if not name:
            missing_fields.append("name")
        if not short_name:
            missing_fields.append("short_name")
        if not unit:
            missing_fields.append("unit")

        if missing_fields:
            logger.warning(f"Missing required fields: {', '.join(missing_fields)}")
            return jsonify(
                {"error": f"Missing required fields: {', '.join(missing_fields)}"}
            ), 400

        # Create form record
        form = Form(
            name=name,
            short_name=short_name,
            unit=unit,
        )
        db.session.add(form)
        db.session.commit()
        logger.info(
            f"Form created successfully: {name} (short_name: {short_name}, unit: {unit})"
        )

        return jsonify(
            {"message": "Form created successfully", "form": form.to_dict()}
        ), 201

    except Exception as e:
        logger.error(f"Error creating form: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@bp.route("/api/form", methods=["PUT"])
def update_form():
    """Edit form record."""
    try:
        logger.info("Received request to update form")
        data = request.get_json()
        logger.debug(f"Update data: {data}")

        # Validate input
        if not data:
            logger.warning("No JSON data provided in update form request")
            return jsonify({"error": "No JSON data provided"}), 400

        name = data.get("name", "").strip()
        short_name = data.get("short_name", "").strip()
        unit = data.get("unit", "").strip()

        # Check for missing fields and report which ones
        missing_fields = []
        if not name:
            missing_fields.append("name")
        if not short_name:
            missing_fields.append("short_name")
        if not unit:
            missing_fields.append("unit")

        if missing_fields:
            logger.warning(f"Missing required fields: {', '.join(missing_fields)}")
            return jsonify(
                {"error": f"Missing required fields: {', '.join(missing_fields)}"}
            ), 400

        # Find and update form
        form = Form.query.get(name)
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

    except Exception as e:
        logger.error(f"Error updating form: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@bp.route("/api/form", methods=["GET"])
def get_forms():
    """Get all forms."""
    try:
        logger.info("Fetching all forms")

        # Get sorting parameter from query string
        sort_by = request.args.get("sort", "name")  # Default: name
        logger.debug(f"Sorting forms by: {sort_by}")

        # Build query based on sorting option
        if sort_by == "name":
            forms = Form.query.order_by(Form.name.asc()).all()
        elif sort_by == "short":
            forms = Form.query.order_by(Form.short_name.asc()).all()
        else:
            forms = Form.query.order_by(Form.name.asc()).all()

        logger.debug(f"Found {len(forms)} forms in database")
        forms_list = [form.to_dict() for form in forms]
        return jsonify({"forms": forms_list}), 200
    except Exception as e:
        logger.error(f"Error fetching forms: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@bp.route("/api/form", methods=["DELETE"])
def delete_form():
    """Delete form record."""
    try:
        data = request.get_json()
        form_name = data.get("name")
        logger.info(f"Deleting form: {form_name}")

        form = Form.query.get(form_name)
        if not form:
            logger.warning(f"Form not found for deletion: {form_name}")
            return jsonify({"error": "Form not found"}), 404

        db.session.delete(form)
        db.session.commit()
        logger.info(f"Form deleted successfully: {form_name}")
        return jsonify({"message": "Form deleted successfully"}), 200

    except Exception as e:
        logger.error(f"Error deleting form: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
