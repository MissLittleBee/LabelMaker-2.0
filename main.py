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
    logger.debug(f"Checking database path: {db_path}")

    if not db_path.exists():
        logger.info("Database not found, creating new database...")
        logger.debug(f"Creating directory: {db_path.parent}")
        db_path.parent.mkdir(parents=True, exist_ok=True)

        # Import and initialize
        logger.debug("Importing Flask application")
        sys.path.insert(0, str(app_dir))
        from app import create_app

        app = create_app()
        logger.debug("Flask app created, initializing database tables")

        with app.app_context():
            from app.db import db

            db.create_all()
        logger.info("✓ Database created successfully at: %s", db_path)
    else:
        logger.info("✓ Database already exists at: %s", db_path)


def main():
    """Main launcher."""
    logger.info("=" * 60)
    logger.info("LabelMaker 2.0")
    logger.info("=" * 60)
    logger.info("Starting application...")
    
    try:
        create_database()

        # Start Flask app
        logger.info("Starting Flask development server...")
        logger.info("Server URL: http://localhost:5000")
        logger.info("Press CTRL+C to stop the server")
        logger.info("-" * 60)
        
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
    except KeyboardInterrupt:
        logger.info("\n" + "=" * 60)
        logger.info("Server stopped by user")
        logger.info("=" * 60)
    except Exception as e:
        logger.error("Failed to start application: %s", str(e), exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
