import os
from pathlib import Path


class Config:
    """Base configuration."""

    BASE_DIR: Path = Path(__file__).parent.parent

    # Build database path - use env var if provided, otherwise use default
    _db_path = os.getenv("DATABASE_URL")
    if _db_path:
        SQLALCHEMY_DATABASE_URI = _db_path
    else:
        # Default: instance/labelmaker.db
        # SQLite URL: sqlite:////absolute/path (4 slashes: sqlite:// + /path)
        db_file = BASE_DIR / "instance" / "labelmaker.db"
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{db_file}"

    # Logging configuration
    DEBUG: bool = os.getenv("DEBUG", "true").lower() in ("true", "1", "yes")
    # If LOG_LEVEL not set, use DEBUG when DEBUG=true, otherwise INFO
    LOG_LEVEL: str = os.getenv("LOG_LEVEL") or ("DEBUG" if DEBUG else "INFO")

    # SQLAlchemy configuration
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SQLALCHEMY_ECHO: bool = DEBUG  # Log SQL queries in debug mode
