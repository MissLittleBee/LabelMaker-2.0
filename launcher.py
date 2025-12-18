import logging
import signal
import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Configuration
HOST = "127.0.0.1"
PORT = 5001
APP_URL = f"http://{HOST}:{PORT}"

# Global variables
flask_process = None
running = True


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
    app_dir = Path(__file__).parent if hasattr(__file__, "__file__") else Path.cwd()

    try:
        # Start Flask server
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


def open_browser():
    """Open default web browser."""
    logger.info(f"Opening browser at {APP_URL}")
    try:
        webbrowser.open(APP_URL)
        return True
    except Exception as e:
        logger.error(f"Error opening browser: {e}")
        return False


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


def signal_handler(signum, frame):
    """Handle shutdown signals."""
    logger.info("Received shutdown signal")
    shutdown_server()
    sys.exit(0)


def main():
    """Main launcher function."""
    logger.info("=" * 60)
    logger.info("LabelMaker 2.0 - Lékárenský systém pro správu cenovek")
    logger.info("=" * 60)

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Check if port is available
    if not is_port_available(PORT):
        logger.error(f"Port {PORT} is already in use!")
        logger.error("Another instance might be running or port is blocked.")
        input("Press Enter to exit...")
        sys.exit(1)

    # Start Flask server
    if not start_flask_server():
        logger.error("Failed to start Flask server")
        input("Press Enter to exit...")
        sys.exit(1)

    # Open browser
    time.sleep(1)  # Small delay to ensure server is fully ready
    open_browser()

    # Keep the application running
    logger.info("-" * 60)
    logger.info("Application is running!")
    logger.info(f"Access the application at: {APP_URL}")
    logger.info("Press CTRL+C to stop the server")
    logger.info("-" * 60)

    try:
        # Keep main thread alive
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
        input("Press Enter to exit...")
        sys.exit(1)
