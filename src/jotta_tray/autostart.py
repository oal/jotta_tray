"""
Autostart management for jotta-tray.

Handles XDG autostart desktop file installation/removal.
"""

import logging
import shutil
from pathlib import Path
from typing import Tuple

logger = logging.getLogger(__name__)


class AutostartError(Exception):
    """Base exception for autostart-related errors."""
    pass


def get_desktop_file_path() -> Path:
    """
    Get the path to the bundled desktop file template.

    Returns:
        Path to jotta-tray.desktop in the module directory.

    Raises:
        AutostartError: If the desktop file template is not found.
    """
    # Desktop file should be in the same directory as this module
    desktop_file = Path(__file__).parent / "jotta-tray.desktop"

    if not desktop_file.exists():
        raise AutostartError(
            f"Desktop file template not found at {desktop_file}. "
            "This may indicate an incomplete installation."
        )

    return desktop_file


def get_autostart_dir() -> Path:
    """
    Get the XDG autostart directory path.

    Returns:
        Path to ~/.config/autostart/
    """
    # Follow XDG Base Directory specification
    config_home = Path.home() / ".config"
    return config_home / "autostart"


def get_autostart_file_path() -> Path:
    """
    Get the path where the autostart desktop file should be installed.

    Returns:
        Path to ~/.config/autostart/jotta-tray.desktop
    """
    return get_autostart_dir() / "jotta-tray.desktop"


def is_autostart_enabled() -> bool:
    """
    Check if autostart is currently enabled.

    Returns:
        True if the desktop file exists in autostart directory, False otherwise.
    """
    return get_autostart_file_path().exists()


def install_autostart() -> Tuple[bool, str]:
    """
    Install the autostart desktop file.

    Copies the desktop file template to ~/.config/autostart/

    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        # Get paths
        source = get_desktop_file_path()
        dest = get_autostart_file_path()

        # Create autostart directory if it doesn't exist
        autostart_dir = get_autostart_dir()
        autostart_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Autostart directory: {autostart_dir}")

        # Copy desktop file
        shutil.copy2(source, dest)
        logger.info(f"Installed autostart file to {dest}")

        return True, f"Autostart enabled successfully.\nDesktop file installed to:\n{dest}"

    except AutostartError as e:
        logger.error(f"Autostart installation failed: {e}")
        return False, str(e)
    except PermissionError as e:
        logger.error(f"Permission denied: {e}")
        return False, f"Permission denied: Unable to write to autostart directory.\n{e}"
    except Exception as e:
        logger.error(f"Unexpected error during autostart installation: {e}", exc_info=True)
        return False, f"Failed to install autostart:\n{e}"


def uninstall_autostart() -> Tuple[bool, str]:
    """
    Remove the autostart desktop file.

    Deletes the desktop file from ~/.config/autostart/

    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        dest = get_autostart_file_path()

        # Check if file exists
        if not dest.exists():
            logger.warning(f"Autostart file not found at {dest}")
            return True, "Autostart is already disabled."

        # Remove desktop file
        dest.unlink()
        logger.info(f"Removed autostart file from {dest}")

        return True, "Autostart disabled successfully."

    except PermissionError as e:
        logger.error(f"Permission denied: {e}")
        return False, f"Permission denied: Unable to remove autostart file.\n{e}"
    except Exception as e:
        logger.error(f"Unexpected error during autostart removal: {e}", exc_info=True)
        return False, f"Failed to remove autostart:\n{e}"


def get_autostart_status() -> str:
    """
    Get a human-readable status message about autostart configuration.

    Returns:
        Status message string.
    """
    enabled = is_autostart_enabled()
    autostart_file = get_autostart_file_path()

    if enabled:
        return f"✓ Autostart is ENABLED\nDesktop file: {autostart_file}"
    else:
        return f"✗ Autostart is DISABLED\nExpected location: {autostart_file}"
