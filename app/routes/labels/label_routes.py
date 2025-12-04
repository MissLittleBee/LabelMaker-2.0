import io

from canvas import A4, canvas
from flask import Blueprint, jsonify, request, send_file

from app.db import db
from app.models import Label

bp = Blueprint("labels", __name__)


@bp.route("/api/label", methods=["POST"])
def create_label():
    """Create a new label with product info."""
    try:
        data = request.get_json()

        # Validate input
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        product_name = data.get("product_name", "").strip()
        price = data.get("price")

        if not product_name or price is None:
            return jsonify(
                {"error": "Missing required fields: product_name, price )"}
            ), 400

        try:
            price = float(price)
        except (ValueError, TypeError):
            return jsonify({"error": "Price must be a valid number"}), 400

        # Create label
        label = Label(
            product_name=product_name,
            price=price,
        )
        db.session.add(label)
        db.session.commit()

        return jsonify(
            {"message": "Label created successfully", "label": label.to_dict()}
        ), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@bp.route("/api/labels", methods=["GET"])
def list_labels():
    """List all labels."""
    try:
        labels = Label.query.all()
        return jsonify(
            {"count": len(labels), "labels": [label.to_dict() for label in labels]}
        ), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/api/label/<int:label_id>", methods=["GET"])
def get_label(label_id):
    """Get a specific label by ID."""
    try:
        label = Label.query.get(label_id)
        if not label:
            return jsonify({"error": "Label not found"}), 404
        return jsonify(label.to_dict()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/api/label/<int:label_id>/pdf", methods=["GET"])
def generate_pdf(label_id):
    """Generate a printable PDF label for a specific label."""
    try:
        label = Label.query.get(label_id)
        if not label:
            return jsonify({"error": "Label not found"}), 404

        # Create PDF in memory
        pdf_buffer = io.BytesIO()
        pdf_canvas = canvas.Canvas(pdf_buffer, pagesize=A4)

        pdf_canvas.save()

        # Reset buffer position
        pdf_buffer.seek(0)

        return send_file(pdf_buffer, mimetype="application/pdf", as_attachment=True)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
