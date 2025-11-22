"""System tray widget implementation using GTK and AppIndicator."""

import gi
import logging
import os
import webbrowser
from pathlib import Path
from typing import Optional

gi.require_version('Gtk', '3.0')
gi.require_version('AppIndicator3', '0.1')

from gi.repository import Gtk, GLib, AppIndicator3

from .status_monitor import SyncStatus
from .cli_interface import CLIInterface, JottaCLIError
from .utils import format_quota, format_file_count
from . import autostart

logger = logging.getLogger(__name__)


class TrayWidget:
    """System tray widget for displaying Jotta Cloud sync status."""

    # Icon state mapping
    ICON_STATES = {
        "idle": "jotta-idle",
        "syncing": "jotta-syncing",
        "paused": "jotta-paused",
        "error": "jotta-error",
        "offline": "jotta-offline",
    }

    def __init__(self, cli: CLIInterface, icon_path: Optional[Path] = None):
        """
        Initialize tray widget.

        Args:
            cli: CLIInterface instance for executing commands
            icon_path: Path to icon directory (default: auto-detect)
        """
        self.cli = cli
        self.icon_path = icon_path or self._find_icon_path()

        # State
        self._current_state = "idle"
        self._current_status: Optional[SyncStatus] = None

        # UI components
        self.indicator: Optional[AppIndicator3.Indicator] = None
        self.status_icon: Optional[Gtk.StatusIcon] = None
        self.menu: Optional[Gtk.Menu] = None

        # Initialize the tray icon
        self._init_tray()

        logger.info(f"TrayWidget initialized with icons from: {self.icon_path}")

    def _find_icon_path(self) -> Path:
        """
        Auto-detect icon directory path.

        Returns:
            Path to icon directory
        """
        # Try relative to this file (new location: src/jotta_tray/icons/)
        module_dir = Path(__file__).parent
        icon_dir = module_dir / "icons"

        if icon_dir.exists():
            return icon_dir

        # Try installed location
        import sys
        for path in sys.path:
            candidate = Path(path) / "jotta_tray" / "icons"
            if candidate.exists():
                return candidate

        # Fallback to current directory
        logger.warning("Icon directory not found, using current directory")
        return Path.cwd()

    def _init_tray(self) -> None:
        """Initialize system tray icon using AppIndicator3."""
        self._init_appindicator()

    def _init_appindicator(self) -> None:
        """Initialize AppIndicator3 system tray icon."""
        logger.info("Using AppIndicator3 for system tray")

        # Get absolute path to initial icon (required for Waybar compatibility)
        initial_icon = str(self._get_icon_path("idle").resolve())
        logger.info(f"Using icon path: {initial_icon}")

        # Create indicator with absolute icon path
        self.indicator = AppIndicator3.Indicator.new(
            "jotta-tray",
            initial_icon,
            AppIndicator3.IndicatorCategory.APPLICATION_STATUS
        )

        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)

        # Build menu
        self.menu = self._build_menu()
        self.indicator.set_menu(self.menu)

    def _build_menu(self) -> Gtk.Menu:
        """
        Build context menu for tray icon.

        Returns:
            Gtk.Menu with all menu items
        """
        menu = Gtk.Menu()

        # Storage info (non-clickable)
        self.storage_item = Gtk.MenuItem(label="Loading...")
        self.storage_item.set_sensitive(False)
        menu.append(self.storage_item)

        # Separator
        menu.append(Gtk.SeparatorMenuItem())

        # Pause/Resume (dynamic label)
        self.pause_resume_item = Gtk.MenuItem(label="Pause Backup")
        self.pause_resume_item.connect("activate", self._on_pause_resume)
        menu.append(self.pause_resume_item)

        # Open Web
        open_web_item = Gtk.MenuItem(label="Open Jottacloud Web")
        open_web_item.connect("activate", self._on_open_web)
        menu.append(open_web_item)

        # View Logs
        view_logs_item = Gtk.MenuItem(label="View Logs")
        view_logs_item.connect("activate", self._on_view_logs)
        menu.append(view_logs_item)

        # Settings
        settings_item = Gtk.MenuItem(label="Settings")
        settings_item.connect("activate", self._on_settings)
        menu.append(settings_item)

        # Separator
        menu.append(Gtk.SeparatorMenuItem())

        # About
        about_item = Gtk.MenuItem(label="About")
        about_item.connect("activate", self._on_about)
        menu.append(about_item)

        # Quit
        quit_item = Gtk.MenuItem(label="Quit")
        quit_item.connect("activate", self._on_quit)
        menu.append(quit_item)

        menu.show_all()
        return menu

    def update_status(self, status: SyncStatus) -> None:
        """
        Update tray icon and tooltip based on new status.

        Args:
            status: New status snapshot
        """
        self._current_status = status

        # Update icon if state changed
        if status.state != self._current_state:
            self.update_icon(status.state)
            self._current_state = status.state

        # Update tooltip
        self.update_tooltip(status)

        # Update storage info in menu
        self._update_storage_menu_item(status)

        # Update pause/resume button
        self._update_pause_resume_item(status)

    def update_icon(self, state: str) -> None:
        """
        Change tray icon based on sync state.

        Args:
            state: One of "idle", "syncing", "paused", "error", "offline"
        """
        icon_file = self._get_icon_path(state)

        if self.indicator:
            # Use absolute path for Waybar compatibility
            icon_path = str(icon_file.resolve())
            self.indicator.set_icon_full(icon_path, f"Jotta Cloud: {state}")
            logger.debug(f"AppIndicator icon updated to: {icon_path}")
        elif self.status_icon:
            if icon_file.exists():
                self.status_icon.set_from_file(str(icon_file))
                logger.debug(f"StatusIcon updated to: {icon_file}")
            else:
                logger.warning(f"Icon file not found: {icon_file}")

    def update_tooltip(self, status: SyncStatus) -> None:
        """
        Update tooltip text with current status information.

        Args:
            status: Status snapshot
        """
        # Format storage quota
        quota_str, quota_pct = format_quota(status.used_bytes, status.total_bytes)

        # Build tooltip text
        lines = [
            f"Jotta Cloud",
            f"Storage: {quota_str}",
        ]

        # Add sync status
        if status.state == "syncing":
            if status.uploading_count > 0:
                lines.append(f"Uploading {format_file_count(status.uploading_count)}")
            if status.downloading_count > 0:
                lines.append(f"Downloading {format_file_count(status.downloading_count)}")
        elif status.state == "idle":
            lines.append("All backed up")
        elif status.state == "paused":
            lines.append("Backup paused")
        elif status.state == "error":
            lines.append("Sync error")
        elif status.state == "offline":
            lines.append("Daemon offline")

        tooltip = "\n".join(lines)

        # Set tooltip
        if self.status_icon:
            self.status_icon.set_tooltip_text(tooltip)
        # Note: AppIndicator doesn't support tooltips directly

        logger.debug(f"Tooltip updated: {tooltip}")

    def _update_storage_menu_item(self, status: SyncStatus) -> None:
        """Update the storage info menu item."""
        quota_str, _ = format_quota(status.used_bytes, status.total_bytes)
        self.storage_item.set_label(f"Storage: {quota_str}")

    def _update_pause_resume_item(self, status: SyncStatus) -> None:
        """Update pause/resume menu item label based on state."""
        if status.state == "paused":
            self.pause_resume_item.set_label("Resume Backup")
        else:
            self.pause_resume_item.set_label("Pause Backup")

    def _get_icon_name(self, state: str) -> str:
        """Get icon name for state."""
        return self.ICON_STATES.get(state, "jotta-idle")

    def _get_icon_path(self, state: str) -> Path:
        """Get full path to icon file."""
        icon_name = self._get_icon_name(state)
        return self.icon_path / f"{icon_name}.svg"

    # Event handlers

    def _on_pause_resume(self, menuitem):
        """Handle pause/resume menu action."""
        try:
            if self._current_status and self._current_status.state == "paused":
                self.cli.run_resume()
                logger.info("Resume requested")
            else:
                self.cli.run_pause()
                logger.info("Pause requested")
        except JottaCLIError as e:
            logger.error(f"Pause/Resume failed: {e}")
            self._show_error_dialog("Action Failed", str(e))

    def _on_open_web(self, menuitem):
        """Handle open web menu action."""
        url = "https://jottacloud.com/web"
        try:
            webbrowser.open(url)
            logger.info(f"Opened web browser: {url}")
        except Exception as e:
            logger.error(f"Failed to open browser: {e}")

    def _on_view_logs(self, menuitem):
        """Handle view logs menu action."""
        try:
            logfile = self.cli.get_logfile_path()
            if logfile and logfile.exists():
                # Open with default text editor
                webbrowser.open(f"file://{logfile}")
                logger.info(f"Opened log file: {logfile}")
            else:
                self._show_error_dialog("Log File Not Found",
                                      "Unable to locate Jotta log file.")
        except JottaCLIError as e:
            logger.error(f"Failed to get log file: {e}")
            self._show_error_dialog("Error", str(e))

    def _on_settings(self, menuitem):
        """Handle settings menu action."""
        self._show_settings_dialog()

    def _show_settings_dialog(self):
        """Show settings dialog with autostart checkbox and other options."""
        # Create dialog
        dialog = Gtk.Dialog(
            title="Jotta Tray Settings",
            parent=None,
            flags=0
        )
        dialog.set_default_size(400, 200)

        # Add buttons
        dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
        dialog.add_button("Save", Gtk.ResponseType.OK)

        # Get content area
        content_area = dialog.get_content_area()
        content_area.set_spacing(12)
        content_area.set_border_width(12)

        # Create autostart checkbox
        autostart_check = Gtk.CheckButton(label="Start automatically at login")
        autostart_check.set_active(autostart.is_autostart_enabled())
        content_area.pack_start(autostart_check, False, False, 0)

        # Add separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        content_area.pack_start(separator, False, False, 6)

        # Add button to open config file
        config_button = Gtk.Button(label="Open configuration file")
        config_button.connect("clicked", self._on_open_config_file)
        content_area.pack_start(config_button, False, False, 0)

        # Show all widgets
        content_area.show_all()

        # Run dialog
        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            # Save autostart setting
            new_autostart_state = autostart_check.get_active()
            current_state = autostart.is_autostart_enabled()

            if new_autostart_state != current_state:
                if new_autostart_state:
                    success, message = autostart.install_autostart()
                else:
                    success, message = autostart.uninstall_autostart()

                if success:
                    logger.info(f"Autostart setting changed: {new_autostart_state}")
                    self._show_info_dialog("Settings Saved", message)
                else:
                    logger.error(f"Failed to change autostart: {message}")
                    self._show_error_dialog("Error", message)

        dialog.destroy()

    def _on_open_config_file(self, button):
        """Open the configuration file in the default text editor."""
        try:
            # Configuration file path
            config_dir = Path.home() / ".config" / "jotta-tray"
            config_file = config_dir / "config.ini"

            # Create config directory if it doesn't exist
            config_dir.mkdir(parents=True, exist_ok=True)

            # Create a template config file if it doesn't exist
            if not config_file.exists():
                config_file.write_text("""# Jotta Tray Configuration
#
# This file controls the behavior of the Jotta Cloud system tray widget.

[monitoring]
# Status polling interval in seconds when idle
poll_interval_idle = 10

# Status polling interval in seconds when syncing
poll_interval_active = 2

# Status polling interval in seconds when daemon is offline
poll_interval_offline = 30

[notifications]
# Enable desktop notifications (true/false)
enabled = true

# Show notification when sync completes
notify_on_sync_complete = true

# Show notification when daemon goes offline
notify_on_daemon_offline = true

# Show notification when approaching quota limit
notify_on_quota_warning = true

# Quota warning threshold (percentage)
quota_warning_threshold = 90
""")
                logger.info(f"Created template config file: {config_file}")

            # Open config file in default text editor
            webbrowser.open(f"file://{config_file}")
            logger.info(f"Opened config file: {config_file}")

        except Exception as e:
            logger.error(f"Failed to open config file: {e}")
            self._show_error_dialog("Error", f"Failed to open configuration file: {e}")

    def _on_about(self, menuitem):
        """Handle about menu action."""
        dialog = Gtk.AboutDialog()
        dialog.set_program_name("Jottacloud Tray")
        dialog.set_version("0.1.0")
        dialog.set_comments("System tray widget for Jotta Cloud sync monitoring")
        dialog.set_website("https://github.com/oal/jotta_tray")

        # Load and set logo
        try:
            from gi.repository import GdkPixbuf
            logo_path = self.icon_path / "jotta-idle.svg"
            if logo_path.exists():
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(str(logo_path), 64, 64)
                dialog.set_logo(pixbuf)
        except Exception as e:
            logger.warning(f"Failed to load logo for about dialog: {e}")

        dialog.run()
        dialog.destroy()

    def _on_quit(self, menuitem):
        """Handle quit menu action."""
        logger.info("Quit requested")
        Gtk.main_quit()

    def _show_error_dialog(self, title: str, message: str) -> None:
        """Show error message dialog."""
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

    def _show_info_dialog(self, title: str, message: str) -> None:
        """Show info message dialog."""
        dialog = Gtk.MessageDialog(
            parent=None,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=title
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()

    def run(self) -> None:
        """Start GTK main loop."""
        logger.info("Starting GTK main loop")
        Gtk.main()

    def quit(self) -> None:
        """Quit the application."""
        Gtk.main_quit()
