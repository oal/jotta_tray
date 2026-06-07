"""
Autostart management for jotta-tray.

Handles XDG autostart desktop file installation/removal.
"""

import logging
import shutil
import subprocess
import sys
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


def _resolve_exec_path() -> str:
    """
    Resolve the absolute path to the jotta-tray executable.

    Tries multiple strategies to find a reliable absolute path that will work
    in an XDG autostart environment (which may have a minimal PATH):

    1. ``shutil.which()`` — works if the install location is on PATH.
    2. **uv tool install** — check ``~/.local/bin/jotta-tray`` explicitly
       (the default target of ``uv tool install``).
    3. **pip editable / venv** — look next to the running interpreter
       (``.venv/bin/jotta-tray``).

    Falls back to the bare command name (``jotta-tray``) if nothing resolves.

    Returns:
        Absolute path to the executable, or ``"jotta-tray"`` as a last resort.
    """
    # Strategy 1: standard which lookup
    found = shutil.which("jotta-tray")
    if found:
        logger.debug(f"Resolved jotta-tray via shutil.which: {found}")
        return found

    # Strategy 2: uv tool install default location
    uv_tool_path = Path.home() / ".local" / "bin" / "jotta-tray"
    if uv_tool_path.exists():
        logger.debug(f"Resolved jotta-tray via uv tool path: {uv_tool_path}")
        return str(uv_tool_path)

    # Strategy 3: pip editable / venv — executable sits next to the interpreter
    venv_bin = Path(sys.executable).parent / "jotta-tray"
    if venv_bin.exists():
        logger.debug(f"Resolved jotta-tray via venv bin: {venv_bin}")
        return str(venv_bin)

    # Strategy 4: try to discover the entry-point script via site-packages metadata
    #    pip installs create a console-script wrapper whose shebang points into the
    #    right virtualenv.  We can probe the package metadata for the entry point.
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", "jotta-tray"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            # pip show doesn't give us the script path directly, but if we got
            # here the venv strategy already covered the common case.
            pass
    except Exception:
        pass

    logger.warning("Could not resolve absolute path for jotta-tray; falling back to bare command name")
    return "jotta-tray"


def _inject_exec_path(content: str, exec_path: str) -> str:
    """Replace the Exec= line in a desktop-file template."""
    lines = content.splitlines(keepends=True)
    updated = []
    for line in lines:
        if line.startswith("Exec="):
            updated.append(f"Exec={exec_path}\n")
        else:
            updated.append(line)
    return "".join(updated)


def install_autostart() -> Tuple[bool, str]:
    """
    Install the autostart desktop file.

    Reads the bundled desktop-file template, resolves the absolute path to the
    ``jotta-tray`` executable, injects it into the ``Exec=`` line, and writes
    the result to ``~/.config/autostart/``.

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

        # Resolve absolute path to the executable
        exec_path = _resolve_exec_path()
        logger.info(f"Using Exec path: {exec_path}")

        # Read template, inject Exec path, and write
        template = source.read_text()
        content = _inject_exec_path(template, exec_path)
        dest.write_text(content)
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
