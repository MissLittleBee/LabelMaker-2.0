import logging

from flask import Blueprint, jsonify, render_template, request, send_file

from app.db import db
from app.models import Form, Label
from app.pdf_generator import generate_labels_pdf
from app.utils import calculate_unit_price

logger = logging.getLogger(__name__)
bp = Blueprint("labels", __name__)


@bp.route("/labels", methods=["GET"])
def list_labels():
    """Show labels list page."""
    logger.info("Rendering labels list page")

    # Get sorting parameter from query string
    sort_by = request.args.get("sort", "name")  # Default: name
    logger.debug(f"Sorting labels by: {sort_by}")

    # Build query based on sorting option
    if sort_by == "name":
        labels = Label.query.order_by(Label.product_name).all()
    elif sort_by == "date":
        labels = Label.query.order_by(Label.created_at.desc()).all()
    elif sort_by == "marked":
        labels = Label.query.order_by(
            Label.marked_to_print.desc(), Label.product_name
        ).all()
    else:
        labels = Label.query.order_by(Label.product_name).all()

    forms = Form.query.all()
    logger.debug(f"Loaded {len(forms)} forms and {len(labels)} labels for listing")
    return render_template(
        "labels/list_labels.html", forms=forms, labels=labels, sort_by=sort_by
    )


@bp.route("/labels/new", methods=["GET"])
def new_label_form():
    """Show form to create new label."""
    logger.info("Rendering new label form")
    forms = Form.query.all()
    logger.debug(f"Loaded {len(forms)} forms for new label form")
    return render_template("labels/new_label.html", forms=forms)


@bp.route("/api/label", methods=["POST"])
def create_label():
    """Create a new label"""
    try:
        logger.info("Received request to create new label")
        data = request.get_json()
        logger.debug(f"Request data: {data}")

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

    except Exception as e:
        logger.error(f"Error creating label: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@bp.route("/api/labels", methods=["GET"])
def get_labels_api():
    """List all labels (API)."""
    try:
        logger.info("Fetching all labels")

        # Get sorting parameter from query string
        sort_by = request.args.get("sort", "name")  # Default: name
        logger.debug(f"Sorting labels by: {sort_by}")

        # Build query based on sorting option
        if sort_by == "name":
            labels = Label.query.order_by(Label.product_name).all()
        elif sort_by == "date":
            labels = Label.query.order_by(Label.created_at.desc()).all()
        elif sort_by == "marked":
            labels = Label.query.order_by(
                Label.marked_to_print.desc(), Label.product_name
            ).all()
        else:
            labels = Label.query.order_by(Label.product_name).all()

        logger.debug(f"Found {len(labels)} labels in database")
        return jsonify(
            {"count": len(labels), "labels": [label.to_dict() for label in labels]}
        ), 200
    except Exception as e:
        logger.error(f"Error fetching labels: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@bp.route("/api/label/<int:label_id>", methods=["PUT"])
def update_label(label_id):
    """Update label information."""
    try:
        logger.info(f"Updating label ID: {label_id}")
        label = Label.query.get(label_id)
        if not label:
            logger.warning(f"Label not found: ID {label_id}")
            return jsonify({"error": "Label not found"}), 404

        data = request.get_json()
        logger.debug(f"Update data for label {label_id}: {data}")
        if not data:
            logger.warning("No JSON data provided for label update")
            return jsonify({"error": "No JSON data provided"}), 400

        # Update fields if provided
        updated_fields = []
        if "product_name" in data:
            label.product_name = data["product_name"].strip()
            updated_fields.append("product_name")
        if "form" in data:
            label.form = data["form"].strip()
            updated_fields.append("form")
        if "amount" in data:
            label.amount = float(data["amount"])
            updated_fields.append("amount")
        if "price" in data:
            label.price = float(data["price"])
            # Recalculate unit price if price or amount changed
            label.unit_price = calculate_unit_price(label.amount, label.price)
            updated_fields.append("price")
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

    except Exception as e:
        logger.error(f"Error updating label {label_id}: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@bp.route("/api/label/<int:label_id>/toggle-print", methods=["POST"])
def toggle_print_mark(label_id):
    """Toggle print mark for a label."""
    try:
        logger.info(f"Toggling print mark for label ID: {label_id}")
        label = Label.query.get(label_id)
        if not label:
            logger.warning(f"Label not found for toggle: ID {label_id}")
            return jsonify({"error": "Label not found"}), 404

        old_value = label.marked_to_print
        label.marked_to_print = not label.marked_to_print
        db.session.commit()
        logger.info(
            f"Label {label_id} print mark toggled: {old_value} -> {label.marked_to_print}"
        )

        return jsonify(
            {"message": "Print mark toggled", "marked_to_print": label.marked_to_print}
        ), 200

    except Exception as e:
        logger.error(
            f"Error toggling print mark for label {label_id}: {str(e)}", exc_info=True
        )
        db.session.rollback()


@bp.route("/api/labels/unmark-all", methods=["POST"])
def unmark_all_labels():
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

    except Exception as e:
        logger.error(f"Error unmarking all labels: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@bp.route("/api/label/<int:label_id>", methods=["DELETE"])
def delete_label(label_id):
    """Delete a label."""
    try:
        logger.info(f"Deleting label ID: {label_id}")
        label = Label.query.get(label_id)
        if not label:
            logger.warning(f"Label not found for deletion: ID {label_id}")
            return jsonify({"error": "Label not found"}), 404

        label_name = label.product_name
        db.session.delete(label)
        db.session.commit()
        logger.info(f"Label deleted successfully: ID {label_id}, Name: {label_name}")

        return jsonify({"message": "Label deleted successfully"}), 200

    except Exception as e:
        logger.error(f"Error deleting label {label_id}: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@bp.route("/api/label/<int:label_id>", methods=["GET"])
def get_label(label_id):
    """Get a specific label by ID."""
    try:
        logger.debug(f"Fetching label ID: {label_id}")
        label = Label.query.get(label_id)
        if not label:
            logger.warning(f"Label not found: ID {label_id}")
            return jsonify({"error": "Label not found"}), 404
        logger.debug(f"Found label: {label.product_name}")
        return jsonify(label.to_dict()), 200
    except Exception as e:
        logger.error(f"Error fetching label {label_id}: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@bp.route("/labels/print", methods=["GET"])
def print_labels_page():
    """Show print labels page with preview."""
    logger.info("Rendering print labels page")
    # Get all labels marked for printing
    marked_labels = Label.query.filter_by(marked_to_print=True).all()
    logger.debug(f"Found {len(marked_labels)} labels marked for printing")
    return render_template("labels/print_labels.html", labels=marked_labels)


@bp.route("/api/labels/pdf", methods=["GET"])
def generate_pdf_all_marked():
    """Generate PDF with all labels marked for printing."""
    try:
        logger.info("Generating PDF for all marked labels")

        # Get all labels marked for printing
        marked_labels = Label.query.filter_by(marked_to_print=True).all()

        if not marked_labels:
            logger.warning("No labels marked for printing")
            return jsonify({"error": "No labels marked for printing"}), 400

        logger.info(f"Generating PDF with {len(marked_labels)} marked labels")

        # Enrich labels with form unit information
        label_data = []
        for label in marked_labels:
            data = label.to_dict()
            # Get unit from form
            form = Form.query.get(label.form)
            if form:
                data["unit"] = form.unit
            else:
                data["unit"] = "ks"  # Default to pieces
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

    except Exception as e:
        logger.error(f"Error generating PDF: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@bp.route("/api/label/<int:label_id>/pdf", methods=["GET"])
def generate_pdf_single(label_id):
    """Generate PDF for a single label."""
    try:
        logger.info(f"Generating PDF for single label ID: {label_id}")

        label = Label.query.get(label_id)
        if not label:
            logger.warning(f"Label not found: ID {label_id}")
            return jsonify({"error": "Label not found"}), 404

        # Enrich label with form unit information
        data = label.to_dict()
        form = Form.query.get(label.form)
        if form:
            data["unit"] = form.unit
        else:
            data["unit"] = "ks"

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

    except Exception as e:
        logger.error(
            f"Error generating PDF for label {label_id}: {str(e)}", exc_info=True
        )
        return jsonify({"error": str(e)}), 500
