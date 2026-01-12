import logging
import sys
import webbrowser
from pathlib import Path
from threading import Timer

from app import create_app
from app.db import db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Logic for paths in EXE vs Script
if getattr(sys, "frozen", False):
    # Path where the .exe is located
    base_dir = Path(sys.executable).parent
    # Path where bundled files (templates/static) are temporarily extracted
    bundle_dir = Path(sys._MEIPASS)
else:
    base_dir = Path(__file__).parent
    bundle_dir = base_dir


def open_browser():
    """Opens the default web browser after a short delay."""
    webbrowser.open_new("http://127.0.0.1:5000/")


def setup_app():
    """Prepare and return the app instance with correct paths."""
    db_path = base_dir / "instance" / "labelmaker.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Force database URI to point to the file next to EXE
    app = create_app()
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"

    with app.app_context():
        db.create_all()
        logger.info(f"✓ Database ready at: {db_path}")

    return app


def main():
    logger.info("Starting LabelMaker 2.0...")

    try:
        app = setup_app()

        # Start timer to open browser
        Timer(1.5, open_browser).start()

        # Run Flask directly (NOT via subprocess)
        # In EXE mode, debug must be False
        app.run(host="127.0.0.1", port=5000, debug=False)

    except Exception as e:
        logger.error("Failed to start application: %s", str(e), exc_info=True)
        # Keep window open if it crashes so user can see the error
        input("Press Enter to exit...")
        sys.exit(1)


if __name__ == "__main__":
    main()
