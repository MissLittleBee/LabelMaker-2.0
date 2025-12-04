import os
from pathlib import Path


class Config:
    """Base configuration."""

    BASE_DIR = Path(__file__).parent.parent

    # Build database path - use env var if provided, otherwise use default
    _db_path = os.getenv("DATABASE_URL")
    if _db_path:
        SQLALCHEMY_DATABASE_URI = _db_path
    else:
        # Default: instance/labelmaker.db
        # SQLite URL: sqlite:////absolute/path (4 slashes: sqlite:// + /path)
        db_file = BASE_DIR / "instance" / "labelmaker.db"
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{db_file}"

    LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")
    DEBUG = os.getenv("DEBUG", "true").lower() in ("true", "1", "yes")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
