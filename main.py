import logging
import subprocess
import sys
from pathlib import Path

# Configure basic logging for launcher
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Get the app directory
app_dir = Path(__file__).parent


def create_database():
    """Initialize database if it doesn't exist."""
    db_path = app_dir / "database" / "labelmaker.db"

    if not db_path.exists():
        logger.info("Creating database...")
        db_path.parent.mkdir(parents=True, exist_ok=True)

        # Import and initialize
        sys.path.insert(0, str(app_dir))
        from app import create_app

        app = create_app()

        with app.app_context():
            from app.db import db

            db.create_all()
        logger.info("✓ Database created successfully")
    else:
        logger.info("✓ Database already exists")


def main():
    """Main launcher."""
    logger.info("LabelMaker 2.0 - Starting...")
    create_database()

    # Start Flask app
    logger.info("Starting Flask server on http://localhost:5000")
    subprocess.run(
        [
            sys.executable,
            "-m",
            "flask",
            "--app",
            "app:create_app",
            "run",
            "--host",
            "127.0.0.1",
        ],
        cwd=str(app_dir),
    )


if __name__ == "__main__":
    main()
