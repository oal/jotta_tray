#!/usr/bin/env python3
"""Main entry point for Jotta Cloud System Tray Widget."""

import sys
import logging
import argparse
import signal
from pathlib import Path

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

from .cli_interface import CLIInterface, CLINotFoundError
from .status_monitor import StatusMonitor
from .tray_widget import TrayWidget

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
    ]
)

logger = logging.getLogger(__name__)


class JottaTrayApp:
    """Main application class."""

    def __init__(self, args: argparse.Namespace):
        """
        Initialize application.

        Args:
            args: Parsed command-line arguments
        """
        self.args = args

        # Set logging level
        if args.debug:
            logging.getLogger().setLevel(logging.DEBUG)
            logger.debug("Debug logging enabled")

        # Initialize components
        self.cli = CLIInterface()
        self.monitor = StatusMonitor(self.cli)
        self.tray = TrayWidget(self.cli)

        # Register signal handlers for clean shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.shutdown()
        sys.exit(0)

    def start(self) -> None:
        """Start the application."""
        logger.info("Starting Jotta Cloud Tray Widget")

        # Check if jotta-cli is available
        try:
            if not self.cli.check_available():
                logger.error("jotta-cli is not available or daemon is offline")
                # Continue anyway - widget will show offline state
        except CLINotFoundError:
            logger.error("jotta-cli not found in PATH")
            self._show_error_and_exit(
                "Jotta CLI Not Found",
                "jotta-cli is not installed or not in PATH.\n"
                "Please install Jotta CLI before using this widget."
            )
            return

        # Connect monitor to tray widget
        self.monitor.add_callback(self._on_status_change)

        # Start monitoring
        self.monitor.start()

        # Show initial status
        initial_status = self.monitor.get_current_status()
        if initial_status:
            self.tray.update_status(initial_status)

        logger.info("Application started successfully")

        # Run GTK main loop
        self.tray.run()

    def _on_status_change(self, status) -> None:
        """
        Handle status changes from monitor.

        This runs in the monitor thread, so we need to use GLib.idle_add
        to update the UI in the main thread.

        Args:
            status: SyncStatus object
        """
        GLib.idle_add(self.tray.update_status, status)

    def shutdown(self) -> None:
        """Clean shutdown of all components."""
        logger.info("Shutting down...")

        # Stop monitor
        if self.monitor:
            self.monitor.stop()

        # Quit GTK
        if self.tray:
            self.tray.quit()

        logger.info("Shutdown complete")

    def _show_error_and_exit(self, title: str, message: str) -> None:
        """Show error dialog and exit."""
        dialog = Gtk.MessageDialog(
            parent=None,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=title
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()
        sys.exit(1)


def main():
    """Main entry point."""
    # Parse arguments
    parser = argparse.ArgumentParser(
        description="Jotta Cloud System Tray Widget",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  jotta-tray              # Start with default settings
  jotta-tray --debug      # Start with debug logging

For more information, visit: https://www.jottacloud.com
        """
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )

    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0"
    )

    args = parser.parse_args()

    # Create and run app
    try:
        app = JottaTrayApp(args)
        app.start()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
