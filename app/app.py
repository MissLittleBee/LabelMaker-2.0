import logging
from pathlib import Path
from typing import Optional

from flask import Flask

from app.central_logging import setup_logging


def create_app(database_uri: Optional[str] = None) -> Flask:
    """Create and configure the LabelMaker Flask application.

    Returns:
        Flask app instance.
    """
    # import db lazily to avoid circular import during module import
    from app.db import db

    # Set template and static folders to project root, not app package
    template_dir = Path(__file__).parent.parent / "templates"
    static_dir = Path(__file__).parent.parent / "static"
    app = Flask(
        __name__, template_folder=str(template_dir), static_folder=str(static_dir)
    )
    from app.config import Config

    app.config.from_object(Config)
    if database_uri:
        app.config["SQLALCHEMY_DATABASE_URI"] = database_uri

    # Setup logging
    setup_logging(app)
    logger = logging.getLogger(__name__)
    logger.info("Initializing LabelMaker application")

    # Ensure database directory exists (cross-platform)
    db_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
    if db_uri.startswith("sqlite:///"):
        # Extract path from sqlite:///path/to/db.db
        db_path = db_uri.replace("sqlite:///", "")
        db_file = Path(db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)
        logger.info("Database directory ensured: %s", db_file.parent)

    # Initialize database
    db.init_app(app)

    with app.app_context():
        # Import all models so db.create_all() knows about them
        from app import models  # noqa: F401

        db.create_all()
        logger.info("Database tables created/verified")

    # Register blueprints
    logger.info("Registering application blueprints")
    from app.routes.forms.forms_routes import bp as forms_bp
    from app.routes.labels.label_routes import bp as labels_bp
    from app.routes.routes import bp as main_bp

    app.register_blueprint(main_bp)
    logger.debug("Registered 'main' blueprint")
    app.register_blueprint(forms_bp)
    logger.debug("Registered 'forms' blueprint")
    app.register_blueprint(labels_bp)
    logger.debug("Registered 'labels' blueprint")
    logger.info("All blueprints registered successfully")

    # Register Jinja2 template filters for Czech number formatting
    @app.template_filter("czech_number")
    def czech_number_filter(value: float, decimals: int = 2) -> str:
        if value == int(value):
            return str(int(value))
        formatted = f"{value:.{decimals}f}".rstrip("0").rstrip(".")
        return formatted.replace(".", ",")

    @app.template_filter("czech_price")
    def czech_price_filter(value: float) -> str:
        if value == int(value):
            return f"{int(value)},-"
        return f"{value:.2f}".replace(".", ",")

    logger.info("LabelMaker application initialized successfully")
    return app
