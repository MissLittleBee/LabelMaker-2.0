"""
Windows launcher with System Tray support for LabelMaker application.

This launcher:
- Starts the Flask server in the background
- Automatically opens the default web browser
- Provides a system tray icon for control and safe shutdown
- No console window (runs silently in background)
"""

import logging
import signal
import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

# Try to import pystray for system tray support
try:
    from PIL import Image, ImageDraw
    from pystray import Icon, Menu, MenuItem

    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False
    print("Warning: pystray not available. Install with: pip install pystray pillow")

# Setup logging to file instead of console
log_file = Path.home() / "LabelMaker.log"
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(),  # Still log to console for debugging
    ],
)
logger = logging.getLogger(__name__)

# Configuration
HOST = "127.0.0.1"
PORT = 5000
APP_URL = f"http://{HOST}:{PORT}"

# Global variables
flask_process = None
running = True
tray_icon = None


def is_port_available(port):
    """Check if a port is available."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind((HOST, port))
        sock.close()
        return True
    except OSError:
        return False


def wait_for_server(timeout=30):
    """Wait for Flask server to be ready."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect((HOST, PORT))
            sock.close()
            return True
        except (socket.error, ConnectionRefusedError):
            time.sleep(0.5)
    return False


def start_flask_server():
    """Start Flask server as subprocess."""
    global flask_process

    logger.info("Starting Flask server...")

    # Get the directory where the launcher is located
    if getattr(sys, "frozen", False):
        # Running as compiled executable
        app_dir = Path(sys.executable).parent
    else:
        # Running as script
        app_dir = Path(__file__).parent

    try:
        # Start Flask server
        startupinfo = None
        if sys.platform == "win32":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE

        flask_process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "flask",
                "--app",
                "app:create_app",
                "run",
                "--host",
                HOST,
                "--port",
                str(PORT),
            ],
            cwd=str(app_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            startupinfo=startupinfo,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )

        logger.info(f"Flask server starting on {APP_URL}")

        # Wait for server to be ready
        if wait_for_server():
            logger.info("✓ Flask server is ready")
            return True
        else:
            logger.error("✗ Flask server failed to start within timeout")
            return False

    except Exception as e:
        logger.error(f"Error starting Flask server: {e}")
        return False


def open_browser(icon=None, item=None):
    """Open default web browser."""
    logger.info(f"Opening browser at {APP_URL}")
    try:
        webbrowser.open(APP_URL)
    except Exception as e:
        logger.error(f"Error opening browser: {e}")


def shutdown_server():
    """Shutdown Flask server gracefully."""
    global flask_process, running

    logger.info("Shutting down application...")
    running = False

    if flask_process:
        try:
            # Send termination signal
            flask_process.terminate()

            # Wait for graceful shutdown (max 5 seconds)
            try:
                flask_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning("Server didn't stop gracefully, forcing shutdown...")
                flask_process.kill()
                flask_process.wait()

            logger.info("✓ Server stopped")
        except Exception as e:
            logger.error(f"Error stopping server: {e}")


def quit_app(icon=None, item=None):
    """Quit application from tray."""
    logger.info("Quit requested from tray icon")
    shutdown_server()
    if icon:
        icon.stop()
    global running
    running = False


def create_tray_icon():
    """Create a simple icon image."""
    # Create a simple green circle icon
    width = 64
    height = 64
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)

    # Draw green circle with white border
    draw.ellipse(
        [4, 4, width - 4, height - 4], fill="#4CAF50", outline="white", width=2
    )

    # Draw "L" in the center
    draw.text((22, 18), "L", fill="white", font=None)

    return image


def setup_tray_icon():
    """Setup system tray icon."""
    global tray_icon

    if not TRAY_AVAILABLE:
        logger.warning("System tray not available")
        return None

    try:
        # Create menu
        menu = Menu(
            MenuItem("Open Browser", open_browser, default=True),
            MenuItem("Quit", quit_app),
        )

        # Create icon
        icon_image = create_tray_icon()
        tray_icon = Icon(
            "LabelMaker", icon_image, "LabelMaker 2.0\nClick to open", menu
        )

        return tray_icon
    except Exception as e:
        logger.error(f"Error creating tray icon: {e}")
        return None


def run_tray_icon():
    """Run system tray icon (blocking)."""
    if tray_icon:
        logger.info("Starting system tray icon")
        tray_icon.run()


def signal_handler(signum, frame):
    """Handle shutdown signals."""
    logger.info("Received shutdown signal")
    quit_app()
    sys.exit(0)


def main():
    """Main launcher function."""
    logger.info("=" * 60)
    logger.info("LabelMaker 2.0 - Lékárenský systém pro správu cenovek")
    logger.info("=" * 60)
    logger.info(f"Log file: {log_file}")

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Check if port is available
    if not is_port_available(PORT):
        logger.error(f"Port {PORT} is already in use!")
        logger.error("Another instance might be running or port is blocked.")
        if not TRAY_AVAILABLE:
            input("Press Enter to exit...")
        sys.exit(1)

    # Start Flask server
    if not start_flask_server():
        logger.error("Failed to start Flask server")
        if not TRAY_AVAILABLE:
            input("Press Enter to exit...")
        sys.exit(1)

    # Open browser automatically
    time.sleep(1)  # Small delay to ensure server is fully ready
    open_browser()

    logger.info("-" * 60)
    logger.info("Application is running!")
    logger.info(f"Access the application at: {APP_URL}")

    # Setup and run system tray icon
    if TRAY_AVAILABLE:
        logger.info("Setting up system tray icon...")
        icon = setup_tray_icon()
        if icon:
            logger.info("Right-click tray icon to quit")
            logger.info("-" * 60)

            # Run tray icon (blocking - will run until quit)
            try:
                run_tray_icon()
            except KeyboardInterrupt:
                logger.info("\nReceived keyboard interrupt")
            finally:
                shutdown_server()
        else:
            # Fallback if tray fails
            logger.info("Running without tray icon")
            logger.info("Press CTRL+C to stop")
            logger.info("-" * 60)
            try:
                while running and flask_process and flask_process.poll() is None:
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("\nReceived keyboard interrupt")
            finally:
                shutdown_server()
    else:
        # No tray available - use console mode
        logger.info("Press CTRL+C to stop the server")
        logger.info("-" * 60)
        try:
            while running and flask_process and flask_process.poll() is None:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("\nReceived keyboard interrupt")
        finally:
            shutdown_server()

    logger.info("Application closed")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
