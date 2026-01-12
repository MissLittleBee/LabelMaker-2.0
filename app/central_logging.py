import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from flask import Flask


def setup_logging(app: Flask) -> logging.Logger:
    """Configure logging for the application."""

    # Create logs directory (with parent directories)
    log_dir = Path(app.instance_path) / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    # Log level from config or environment
    log_level_str = getattr(app.config, "LOG_LEVEL", "INFO")
    # Convert string to logging level (DEBUG=10, INFO=20, WARNING=30, etc)
    log_level = getattr(logging, log_level_str.upper(), logging.INFO)

    # Format: timestamp | level | module | message
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)-8s [%(name)s] %(message)s",
        datefmt="%d-%m-%y %H:%M:%S",
    )

    # 1. Console handler (for development/debugging)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)

    # 2. File handler (for production logs)
    file_handler = RotatingFileHandler(
        log_dir / "labelmaker.log",
        maxBytes=2 * 1024 * 1024,
        backupCount=2,
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)

    # 3. Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # Reduce noise from werkzeug (Flask's WSGI server)
    logging.getLogger("werkzeug").setLevel(logging.WARNING)

    return root_logger
