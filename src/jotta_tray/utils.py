"""Utility functions for formatting and data conversion."""

from typing import Tuple
from datetime import datetime


def format_bytes(bytes_value: int, decimal_places: int = 1) -> str:
    """
    Format bytes into human-readable string (KB, MB, GB, TB).

    Args:
        bytes_value: Number of bytes
        decimal_places: Number of decimal places to display (default: 1)

    Returns:
        Formatted string like "45.2 GB" or "1.5 TB"

    Examples:
        >>> format_bytes(1024)
        '1.0 KB'
        >>> format_bytes(1536)
        '1.5 KB'
        >>> format_bytes(1073741824)
        '1.0 GB'
    """
    if bytes_value < 0:
        return "0 B"

    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    unit_index = 0

    value = float(bytes_value)

    while value >= 1024.0 and unit_index < len(units) - 1:
        value /= 1024.0
        unit_index += 1

    if unit_index == 0:  # Bytes - no decimal places
        return f"{int(value)} {units[unit_index]}"
    else:
        return f"{value:.{decimal_places}f} {units[unit_index]}"


def format_quota(used: int, total: int) -> Tuple[str, float]:
    """
    Format storage quota as readable string and percentage.

    Args:
        used: Bytes used
        total: Total capacity in bytes

    Returns:
        Tuple of (formatted_string, percentage)
        e.g., ("45.2 GB / 100 GB (45%)", 45.2)

    Examples:
        >>> format_quota(48318382080, 107374182400)
        ('45.0 GB / 100.0 GB (45%)', 45.0)
    """
    if total == 0:
        return ("Unknown quota", 0.0)

    percentage = (used / total) * 100.0
    used_str = format_bytes(used)
    total_str = format_bytes(total)

    formatted = f"{used_str} / {total_str} ({percentage:.0f}%)"

    return (formatted, percentage)


def format_transfer_speed(bytes_per_second: float, decimal_places: int = 1) -> str:
    """
    Format transfer speed into human-readable string.

    Args:
        bytes_per_second: Transfer speed in bytes/second
        decimal_places: Number of decimal places

    Returns:
        Formatted string like "3.2 MB/s" or "128 KB/s"

    Examples:
        >>> format_transfer_speed(1048576)
        '1.0 MB/s'
        >>> format_transfer_speed(3355443.2)
        '3.2 MB/s'
    """
    if bytes_per_second < 0:
        return "0 B/s"

    units = ["B/s", "KB/s", "MB/s", "GB/s"]
    unit_index = 0
    value = float(bytes_per_second)

    while value >= 1024.0 and unit_index < len(units) - 1:
        value /= 1024.0
        unit_index += 1

    if unit_index == 0:
        return f"{int(value)} {units[unit_index]}"
    else:
        return f"{value:.{decimal_places}f} {units[unit_index]}"


def format_file_count(count: int) -> str:
    """
    Format file count with appropriate singular/plural.

    Args:
        count: Number of files

    Returns:
        Formatted string like "1 file" or "42 files"
    """
    if count == 1:
        return "1 file"
    else:
        return f"{count} files"


def milliseconds_to_datetime(ms: int) -> datetime:
    """
    Convert milliseconds since epoch to datetime object.

    Args:
        ms: Milliseconds since Unix epoch

    Returns:
        datetime object
    """
    return datetime.fromtimestamp(ms / 1000.0)


def parse_sync_state(state_data: dict) -> str:
    """
    Determine sync state from jotta-cli status State object.

    Args:
        state_data: State dictionary from jotta-cli status

    Returns:
        One of: "idle", "syncing", "paused", "error", "offline"
    """
    # Check if uploading or downloading
    uploading = state_data.get("Uploading", {})
    downloading = state_data.get("Downloading", {})

    has_uploads = len(uploading) > 0 if isinstance(uploading, dict) else False
    has_downloads = len(downloading) > 0 if isinstance(downloading, dict) else False

    if has_uploads or has_downloads:
        return "syncing"

    # Default to idle if no active transfers
    return "idle"


def detect_quota_warning(used: int, total: int, threshold_percent: float = 90.0) -> bool:
    """
    Detect if storage quota exceeds warning threshold.

    Args:
        used: Bytes used
        total: Total capacity in bytes
        threshold_percent: Warning threshold percentage (default: 90%)

    Returns:
        True if usage exceeds threshold
    """
    if total == 0:
        return False

    usage_percent = (used / total) * 100.0
    return usage_percent >= threshold_percent
