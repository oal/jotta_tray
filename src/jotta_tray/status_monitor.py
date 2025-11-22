"""Background service for monitoring jotta-cli status."""

import threading
import time
import logging
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta

from .cli_interface import CLIInterface, DaemonOfflineError, JottaCLIError
from .utils import parse_sync_state, detect_quota_warning

logger = logging.getLogger(__name__)


@dataclass
class SyncStatus:
    """Represents current sync status snapshot."""

    state: str  # "idle", "syncing", "paused", "error", "offline"
    used_bytes: int
    total_bytes: int
    local_files: int
    remote_files: int
    uploading_count: int
    downloading_count: int
    last_update: datetime
    quota_warning: bool


class StatusMonitor:
    """Background service that polls jotta-cli and emits state change events."""

    # Polling intervals (seconds)
    IDLE_INTERVAL = 10
    ACTIVE_INTERVAL = 2
    OFFLINE_INTERVAL = 30

    # Quota cache TTL
    QUOTA_CACHE_TTL = 300  # 5 minutes

    def __init__(self, cli: CLIInterface):
        """
        Initialize status monitor.

        Args:
            cli: CLIInterface instance
        """
        self.cli = cli
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._callbacks: list[Callable[[SyncStatus], None]] = []

        # State tracking
        self._last_status: Optional[SyncStatus] = None
        self._last_quota_check = datetime.min
        self._cached_quota: Optional[tuple[int, int]] = None

        # Adaptive polling
        self._current_interval = self.IDLE_INTERVAL

    def add_callback(self, callback: Callable[[SyncStatus], None]) -> None:
        """
        Register a callback to be called when status changes.

        Args:
            callback: Function that takes SyncStatus as argument
        """
        self._callbacks.append(callback)
        logger.debug(f"Registered callback: {callback.__name__}")

    def start(self) -> None:
        """Start the background monitoring thread."""
        if self._running:
            logger.warning("StatusMonitor already running")
            return

        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True, name="StatusMonitor")
        self._thread.start()
        logger.info("StatusMonitor started")

    def stop(self) -> None:
        """Stop the background monitoring thread."""
        if not self._running:
            return

        logger.info("Stopping StatusMonitor...")
        self._running = False

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)

        logger.info("StatusMonitor stopped")

    def get_current_status(self) -> Optional[SyncStatus]:
        """
        Get the most recent status snapshot.

        Returns:
            Last known status, or None if not yet available
        """
        return self._last_status

    def _monitor_loop(self) -> None:
        """Main monitoring loop (runs in background thread)."""
        logger.debug("Monitor loop started")

        while self._running:
            try:
                # Fetch current status
                status = self._fetch_status()

                # Compare with previous status
                if self._has_changed(status):
                    logger.info(f"Status changed: {status.state}")
                    self._last_status = status

                    # Notify all callbacks
                    for callback in self._callbacks:
                        try:
                            callback(status)
                        except Exception as e:
                            logger.error(f"Callback error in {callback.__name__}: {e}")

                else:
                    # Update last status even if unchanged
                    self._last_status = status

                # Adjust polling interval based on state
                self._adjust_interval(status.state)

            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")

            # Sleep until next check
            time.sleep(self._current_interval)

        logger.debug("Monitor loop exited")

    def _fetch_status(self) -> SyncStatus:
        """
        Fetch current status from jotta-cli.

        Returns:
            SyncStatus object

        Raises:
            JottaCLIError: If status fetch fails
        """
        try:
            # Get status JSON
            status_data = self.cli.run_status()

            # Parse state
            state = self._determine_state(status_data)

            # Extract quota information (with caching)
            used, total = self._get_quota(status_data)

            # Extract sync info
            sync_data = status_data.get("Sync", {})
            local_count = sync_data.get("Count", {})
            remote_count = sync_data.get("RemoteCount", {})

            # Extract transfer counts
            state_data = status_data.get("State", {})
            uploading = state_data.get("Uploading", {})
            downloading = state_data.get("Downloading", {})

            upload_count = len(uploading) if isinstance(uploading, dict) else 0
            download_count = len(downloading) if isinstance(downloading, dict) else 0

            # Check quota warning
            quota_warning = detect_quota_warning(used, total)

            # Create status snapshot
            return SyncStatus(
                state=state,
                used_bytes=used,
                total_bytes=total,
                local_files=local_count.get("Files", 0),
                remote_files=remote_count.get("Files", 0),
                uploading_count=upload_count,
                downloading_count=download_count,
                last_update=datetime.now(),
                quota_warning=quota_warning,
            )

        except DaemonOfflineError:
            logger.warning("Daemon offline")
            # Return offline state with cached quota if available
            used, total = self._cached_quota if self._cached_quota else (0, 0)
            return SyncStatus(
                state="offline",
                used_bytes=used,
                total_bytes=total,
                local_files=0,
                remote_files=0,
                uploading_count=0,
                downloading_count=0,
                last_update=datetime.now(),
                quota_warning=False,
            )

    def _determine_state(self, status_data: Dict[str, Any]) -> str:
        """
        Determine sync state from status data.

        Args:
            status_data: Parsed status JSON

        Returns:
            State string: "idle", "syncing", "paused", "error", "offline"
        """
        # Check if sync is enabled
        sync_data = status_data.get("Sync", {})
        sync_enabled = sync_data.get("Enabled", True)

        if not sync_enabled:
            return "paused"

        # Check transfer state
        state_data = status_data.get("State", {})
        state = parse_sync_state(state_data)

        return state

    def _get_quota(self, status_data: Dict[str, Any]) -> tuple[int, int]:
        """
        Get quota information with caching.

        Args:
            status_data: Parsed status JSON

        Returns:
            Tuple of (used_bytes, total_bytes)
        """
        now = datetime.now()

        # Return cached value if still fresh
        if (self._cached_quota is not None and
            now - self._last_quota_check < timedelta(seconds=self.QUOTA_CACHE_TTL)):
            return self._cached_quota

        # Fetch fresh quota data
        user_data = status_data.get("User", {})
        account_info = user_data.get("AccountInfo", {})

        used = account_info.get("Usage", 0)
        total = account_info.get("Capacity", 0)

        # Update cache
        self._cached_quota = (used, total)
        self._last_quota_check = now

        logger.debug(f"Quota updated: {used}/{total} bytes")

        return (used, total)

    def _has_changed(self, new_status: SyncStatus) -> bool:
        """
        Check if status has changed significantly.

        Args:
            new_status: New status snapshot

        Returns:
            True if status changed
        """
        if self._last_status is None:
            return True

        # Compare key fields
        changed = (
            new_status.state != self._last_status.state or
            new_status.uploading_count != self._last_status.uploading_count or
            new_status.downloading_count != self._last_status.downloading_count or
            new_status.quota_warning != self._last_status.quota_warning
        )

        return changed

    def _adjust_interval(self, state: str) -> None:
        """
        Adjust polling interval based on current state.

        Args:
            state: Current sync state
        """
        if state == "syncing":
            new_interval = self.ACTIVE_INTERVAL
        elif state == "offline":
            new_interval = self.OFFLINE_INTERVAL
        else:
            new_interval = self.IDLE_INTERVAL

        if new_interval != self._current_interval:
            logger.debug(f"Adjusting polling interval: {self._current_interval}s → {new_interval}s")
            self._current_interval = new_interval
