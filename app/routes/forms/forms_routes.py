from flask import Blueprint, jsonify, render_template, request

from app.db import db
from app.models import Form

bp = Blueprint("forms", __name__)


@bp.route("/forms", methods=["GET"])
def list_forms():
    """Render forms management page."""
    return render_template("forms/list_forms.html")


@bp.route("/api/form", methods=["POST"])
def create_form():
    """Create a new form."""
    try:
        data = request.get_json()

        # Validate input
        if not data:
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

        return jsonify(
            {"message": "Form created successfully", "form": form.to_dict()}
        ), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@bp.route("/api/form", methods=["PUT"])
def update_form():
    """Edit form record."""
    try:
        data = request.get_json()

        # Validate input
        if not data:
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
            return jsonify(
                {"error": f"Missing required fields: {', '.join(missing_fields)}"}
            ), 400

        # Find and update form
        form = Form.query.get(name)
        if not form:
            return jsonify({"error": "Form not found"}), 404

        form.short_name = short_name
        form.unit = unit
        db.session.commit()

        return jsonify(
            {"message": "Form updated successfully", "form": form.to_dict()}
        ), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@bp.route("/api/form", methods=["DELETE"])
def delete_form():
    """Delete form record."""
    try:
        data = request.get_json()
        form_name = data.get("name")
        form = Form.query.get(form_name)
        db.session.delete(form)
        db.session.commit()
        return jsonify({"message": "Form deleted successfully"}), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
