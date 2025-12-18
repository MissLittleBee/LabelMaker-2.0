import logging

from flask import Blueprint, jsonify, render_template
from flask.typing import ResponseReturnValue

logger = logging.getLogger(__name__)

# Create Blueprint
bp = Blueprint("main", __name__)


# Routes
@bp.route("/health", methods=["GET"])
def health() -> ResponseReturnValue:
    """Health check endpoint."""
    logger.debug("Health check endpoint accessed")
    return jsonify({"status": "healthy", "service": "labelmaker"}), 200


@bp.route("/", methods=["GET"])
def index() -> str:
    """Home page with main options."""
    logger.info("Rendering home page")
    return render_template("home.html")
