import logging
from typing import Callable, cast

from flask import Blueprint, current_app, jsonify, render_template, request
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
    return render_template("home.html", active_page="home")


@bp.route("/heartbeat", methods=["POST"])
def heartbeat() -> ResponseReturnValue:
    """Receive browser keepalive pings for launcher auto-shutdown logic."""
    callback = current_app.config.get("HEARTBEAT_CALLBACK")
    if callable(callback):
        cast(Callable[[], None], callback)()
    return jsonify({"status": "ok"}), 200


@bp.route("/internal/shutdown", methods=["POST"])
def internal_shutdown() -> ResponseReturnValue:
    """Shutdown development server when launcher decides to exit."""
    expected_token = current_app.config.get("SHUTDOWN_TOKEN", "")
    provided_token = request.headers.get("X-LabelMaker-Shutdown-Token", "")

    if not expected_token or provided_token != expected_token:
        return jsonify({"error": "forbidden"}), 403

    shutdown_func = request.environ.get("werkzeug.server.shutdown")
    if callable(shutdown_func):
        shutdown_func()
        return jsonify({"status": "shutting_down"}), 200

    return jsonify({"status": "not_supported"}), 503
