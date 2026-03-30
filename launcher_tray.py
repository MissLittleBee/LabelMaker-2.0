"""
System tray launcher for LabelMaker 2.0.

Entry point for the packaged Windows executable.
Starts the Flask web server in a background thread,
opens the default browser, and provides a system tray icon
for controlling the application lifecycle.
"""

from __future__ import annotations

import logging
import sys
import webbrowser
from pathlib import Path
from threading import Thread
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from flask import Flask
    from PIL import Image

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

HOST = "127.0.0.1"
PORT = 5000
URL = f"http://{HOST}:{PORT}/"

# Resolve paths depending on whether running from .exe or source
if getattr(sys, "frozen", False):
    # Path where the .exe is located (persistent storage next to exe)
    base_dir = Path(sys.executable).parent
    # Path where bundled files (templates/static) are temporarily extracted
    bundle_dir = Path(sys._MEIPASS)  # noqa: SLF001
else:
    base_dir = Path(__file__).parent
    bundle_dir = base_dir


def _create_icon_image() -> "Image.Image":
    """Create a simple tray icon image programmatically."""
    from PIL import Image, ImageDraw

    size = 64
    image = Image.new("RGB", (size, size), color=(41, 128, 185))
    draw = ImageDraw.Draw(image)
    draw.rectangle([4, 4, size - 4, size - 4], outline="white", width=2)
    draw.text((14, 16), "LM", fill="white")
    return image


def _setup_app() -> "Flask":
    """Prepare and return the Flask app with correct database path."""
    from app import create_app
    from app.db import db

    db_path = base_dir / "instance" / "labelmaker.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)

    app = create_app()
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"

    with app.app_context():
        db.create_all()
        logger.info("Database ready at: %s", db_path)

    return app


def _run_server(app: "Flask") -> None:
    """Run the Flask development server in a thread."""
    app.run(host=HOST, port=PORT, debug=False, use_reloader=False)


def _open_browser() -> None:
    """Open the default web browser to the application URL."""
    webbrowser.open_new(URL)


def main() -> None:
    """Start LabelMaker 2.0 with system tray icon."""
    logger.info("Starting LabelMaker 2.0...")

    try:
        app = _setup_app()

        # Start Flask server in a daemon thread (killed on exit)
        server_thread = Thread(target=_run_server, args=(app,), daemon=True)
        server_thread.start()
        logger.info("Server started at %s", URL)

        # Open browser immediately
        _open_browser()

        # Build system tray icon with menu
        import pystray

        icon = pystray.Icon(
            name="LabelMaker",
            icon=_create_icon_image(),
            title="LabelMaker 2.0",
            menu=pystray.Menu(
                pystray.MenuItem(
                    "Open in Browser",
                    lambda _icon, _item: _open_browser(),
                    default=True,
                ),
                pystray.MenuItem(
                    "Quit",
                    lambda _icon, _item: _icon.stop(),
                ),
            ),
        )

        # icon.run() blocks until icon.stop() is called via the Quit menu
        icon.run()

    except Exception as e:
        logger.error("Failed to start application: %s", str(e), exc_info=True)
        if getattr(sys, "frozen", False):
            input("Press Enter to exit...")
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
