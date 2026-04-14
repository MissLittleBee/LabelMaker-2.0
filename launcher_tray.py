"""
System tray launcher for LabelMaker 2.0.

Entry point for the packaged Windows executable.
Starts the Flask web server in a background thread,
opens the default browser, and provides a system tray icon
for controlling the application lifecycle.
"""

from __future__ import annotations

import logging
import socket
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path
from threading import Lock, Thread
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
SINGLE_INSTANCE_HOST = "127.0.0.1"
SINGLE_INSTANCE_PORT = 51234
HEARTBEAT_TIMEOUT_SECONDS = 20.0
HEARTBEAT_GRACE_SECONDS = 45.0

_instance_lock_socket: socket.socket | None = None
_heartbeat_lock = Lock()
_last_heartbeat_monotonic = time.monotonic()


def _show_info_popup(title: str, message: str) -> None:
    """Show an informational popup window for users."""
    if sys.platform.startswith("win"):
        try:
            import ctypes

            ctypes.windll.user32.MessageBoxW(0, message, title, 0x40)
            return
        except Exception:
            logger.warning("Windows popup failed, falling back to tkinter popup")

    try:
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo(title, message)
        root.destroy()
    except Exception:
        logger.info("%s: %s", title, message)


def _acquire_single_instance_lock() -> bool:
    """Acquire a process-level single-instance lock using localhost socket binding."""
    global _instance_lock_socket

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.bind((SINGLE_INSTANCE_HOST, SINGLE_INSTANCE_PORT))
        sock.listen(1)
    except OSError:
        sock.close()
        return False

    _instance_lock_socket = sock
    return True


def _release_single_instance_lock() -> None:
    """Release the instance lock socket during normal shutdown."""
    global _instance_lock_socket

    if _instance_lock_socket is None:
        return

    try:
        _instance_lock_socket.close()
    except OSError:
        pass
    finally:
        _instance_lock_socket = None


def _mark_heartbeat() -> None:
    """Update the last seen browser heartbeat timestamp."""
    global _last_heartbeat_monotonic

    with _heartbeat_lock:
        _last_heartbeat_monotonic = time.monotonic()


def _seconds_since_heartbeat() -> float:
    """Get elapsed seconds since the most recent browser heartbeat."""
    with _heartbeat_lock:
        last = _last_heartbeat_monotonic
    return time.monotonic() - last


def _request_server_shutdown(token: str) -> None:
    """Attempt graceful Flask shutdown via internal endpoint."""
    req = urllib.request.Request(
        f"{URL}internal/shutdown",
        method="POST",
        data=b"",
        headers={"X-LabelMaker-Shutdown-Token": token},
    )
    try:
        with urllib.request.urlopen(req, timeout=2):
            logger.info("Shutdown endpoint acknowledged")
    except (urllib.error.URLError, TimeoutError) as exc:
        logger.warning("Shutdown endpoint unavailable: %s", exc)


# Resolve paths depending on whether running from .exe or source
if getattr(sys, "frozen", False):
    # Path where the .exe is located (persistent storage next to exe)
    base_dir = Path(sys.executable).parent
    # Path where bundled files (templates/static) are temporarily extracted
    bundle_dir = Path(getattr(sys, "_MEIPASS", ""))
else:
    base_dir = Path(__file__).parent
    bundle_dir = base_dir


def _create_icon_image() -> "Image.Image":
    """Create a simple tray icon image programmatically."""
    from PIL import Image, ImageDraw

    size = 64
    image = Image.new("RGB", (size, size), color=(41, 128, 185))
    draw = ImageDraw.Draw(image)
    draw.rectangle((4, 4, size - 4, size - 4), outline="white", width=2)
    draw.text((14, 16), "LM", fill="white")
    return image


def _setup_app() -> "Flask":
    """Prepare and return the Flask app with correct database path."""
    from app import create_app
    from app.db import db

    db_path = base_dir / "instance" / "labelmaker.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    database_uri = f"sqlite:///{db_path}"

    shutdown_token = f"lm-{time.time_ns()}"
    app = create_app(
        database_uri=database_uri,
        on_heartbeat=_mark_heartbeat,
        shutdown_token=shutdown_token,
    )

    with app.app_context():
        db.create_all()
        logger.info("Database ready at: %s", db_path)

    # Store for local watchdog thread so it can request graceful shutdown.
    app.config["_SHUTDOWN_TOKEN_LOCAL"] = shutdown_token
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

    if not _acquire_single_instance_lock():
        message = (
            "LabelMaker is already running in the background.\n"
            "Opening the existing app in your browser."
        )
        _show_info_popup("LabelMaker", message)
        _open_browser()
        return

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

        def _watch_browser_heartbeat() -> None:
            start = time.monotonic()
            while True:
                elapsed_from_start = time.monotonic() - start
                elapsed_from_heartbeat = _seconds_since_heartbeat()
                if (
                    elapsed_from_start > HEARTBEAT_GRACE_SECONDS
                    and elapsed_from_heartbeat > HEARTBEAT_TIMEOUT_SECONDS
                ):
                    logger.info(
                        "No browser heartbeat for %.1fs, stopping application",
                        elapsed_from_heartbeat,
                    )
                    _request_server_shutdown(
                        app.config.get("_SHUTDOWN_TOKEN_LOCAL", "")
                    )
                    icon.stop()
                    return
                time.sleep(2.0)

        heartbeat_thread = Thread(target=_watch_browser_heartbeat, daemon=True)
        heartbeat_thread.start()

        # icon.run() blocks until icon.stop() is called via the Quit menu
        icon.run()

    except Exception as e:
        logger.error("Failed to start application: %s", str(e), exc_info=True)
        if getattr(sys, "frozen", False):
            input("Press Enter to exit...")
        sys.exit(1)
    finally:
        _release_single_instance_lock()

    sys.exit(0)


if __name__ == "__main__":
    main()
