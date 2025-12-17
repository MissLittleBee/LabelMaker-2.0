# from canvas import A4, canvas
from flask import Blueprint, jsonify, render_template, request

from app.db import db
from app.models import Form, Label
from app.utils import calculate_unit_price

bp = Blueprint("labels", __name__)


@bp.route("/labels", methods=["GET"])
def list_labels():
    """Show labels list page."""
    forms = Form.query.all()
    return render_template("labels/list_labels.html", forms=forms)


@bp.route("/labels/new", methods=["GET"])
def new_label_form():
    """Show form to create new label."""
    forms = Form.query.all()
    return render_template("labels/new_label.html", forms=forms)


@bp.route("/api/label", methods=["POST"])
def create_label():
    """Create a new label"""
    try:
        data = request.get_json()

        # Validate input
        if not data:
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
            return jsonify(
                {"error": f"Missing required fields: {', '.join(missing_fields)}"}
            ), 400

        # Validate and convert to float
        try:
            price = float(price)
            amount = float(amount)
            if amount <= 0:
                return jsonify({"error": "Amount must be greater than 0"}), 400
        except (ValueError, TypeError):
            return jsonify({"error": "Price and amount must be valid numbers"}), 400

        # Calculate unit price
        unit_price = calculate_unit_price(amount, price)

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

        return jsonify(
            {"message": "Label created successfully", "label": label.to_dict()}
        ), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@bp.route("/api/labels", methods=["GET"])
def get_labels_api():
    """List all labels (API)."""
    try:
        labels = Label.query.all()
        return jsonify(
            {"count": len(labels), "labels": [label.to_dict() for label in labels]}
        ), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/api/label/<int:label_id>", methods=["PUT"])
def update_label(label_id):
    """Update label information."""
    try:
        label = Label.query.get(label_id)
        if not label:
            return jsonify({"error": "Label not found"}), 404

        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        # Update fields if provided
        if "product_name" in data:
            label.product_name = data["product_name"].strip()
        if "form" in data:
            label.form = data["form"].strip()
        if "amount" in data:
            label.amount = float(data["amount"])
        if "price" in data:
            label.price = float(data["price"])
            # Recalculate unit price if price or amount changed
            label.unit_price = calculate_unit_price(label.amount, label.price)
        if "marked_to_print" in data:
            label.marked_to_print = data["marked_to_print"]

        db.session.commit()
        return jsonify(
            {"message": "Label updated successfully", "label": label.to_dict()}
        ), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@bp.route("/api/label/<int:label_id>/toggle-print", methods=["POST"])
def toggle_print_mark(label_id):
    """Toggle print mark for a label."""
    try:
        label = Label.query.get(label_id)
        if not label:
            return jsonify({"error": "Label not found"}), 404

        label.marked_to_print = not label.marked_to_print
        db.session.commit()

        return jsonify(
            {"message": "Print mark toggled", "marked_to_print": label.marked_to_print}
        ), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@bp.route("/api/label/<int:label_id>", methods=["DELETE"])
def delete_label(label_id):
    """Delete a label."""
    try:
        label = Label.query.get(label_id)
        if not label:
            return jsonify({"error": "Label not found"}), 404

        db.session.delete(label)
        db.session.commit()

        return jsonify({"message": "Label deleted successfully"}), 200

    except Exception as e:
        db.session.rollback()
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


# @bp.route("/api/label/<int:label_id>/pdf", methods=["GET"])
# def generate_pdf(label_id):
#     """Generate a printable PDF label for a specific label."""
#     try:
#         label = Label.query.get(label_id)
#         if not label:
#             return jsonify({"error": "Label not found"}), 404

#         # Create PDF in memory
#         pdf_buffer = io.BytesIO()
#         pdf_canvas = canvas.Canvas(pdf_buffer, pagesize=A4)

#         pdf_canvas.save()

#         # Reset buffer position
#         pdf_buffer.seek(0)

#         return send_file(pdf_buffer, mimetype="application/pdf", as_attachment=True)

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500
