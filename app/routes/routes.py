from flask import Blueprint, jsonify, render_template

# Create Blueprint
bp = Blueprint("labels", __name__)


# Routes
@bp.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "service": "labelmaker"}), 200


@bp.route("/", methods=["GET"])
def index():
    """Home page with main options."""
    return render_template("home.html")
