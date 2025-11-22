"""Interface for interacting with jotta-cli command-line tool."""

import json
import subprocess
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class JottaCLIError(Exception):
    """Base exception for jotta-cli related errors."""
    pass


class DaemonOfflineError(JottaCLIError):
    """Raised when jotta daemon is not reachable."""
    pass


class CLINotFoundError(JottaCLIError):
    """Raised when jotta-cli executable is not found."""
    pass


class CLIInterface:
    """Wrapper for jotta-cli commands with JSON output parsing."""

    def __init__(self, cli_path: str = "jotta-cli", timeout: int = 5):
        """
        Initialize CLI interface.

        Args:
            cli_path: Path to jotta-cli executable (default: "jotta-cli" from PATH)
            timeout: Command timeout in seconds (default: 5)
        """
        self.cli_path = cli_path
        self.timeout = timeout

    def _run_command(self, args: list[str], timeout: Optional[int] = None) -> subprocess.CompletedProcess:
        """
        Run a jotta-cli command and return the result.

        Args:
            args: Command arguments (excluding 'jotta-cli')
            timeout: Override default timeout

        Returns:
            CompletedProcess with stdout, stderr, and returncode

        Raises:
            CLINotFoundError: If jotta-cli is not found
            subprocess.TimeoutExpired: If command exceeds timeout
        """
        if timeout is None:
            timeout = self.timeout

        cmd = [self.cli_path] + args

        try:
            logger.debug(f"Running command: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False  # We'll handle errors manually
            )
            return result

        except FileNotFoundError:
            raise CLINotFoundError(f"jotta-cli not found at: {self.cli_path}")
        except subprocess.TimeoutExpired as e:
            logger.error(f"Command timed out after {timeout}s: {' '.join(cmd)}")
            raise

    def run_status(self) -> Dict[str, Any]:
        """
        Execute 'jotta-cli status --json' and parse the output.

        Returns:
            Parsed JSON status dictionary with fields:
            - User: User information and account details
            - Sync: Sync folder status and file counts
            - State: Current transfer state

        Raises:
            DaemonOfflineError: If daemon is not running
            CLINotFoundError: If jotta-cli is not found
            JottaCLIError: For other CLI errors
        """
        try:
            result = self._run_command(["status", "--json"])

            # Check for daemon offline error
            if result.returncode != 0:
                error_msg = result.stderr.strip()
                if "connection refused" in error_msg.lower() or "not running" in error_msg.lower():
                    raise DaemonOfflineError("Jotta daemon is not running")
                else:
                    raise JottaCLIError(f"jotta-cli status failed: {error_msg}")

            # Parse JSON output
            try:
                status_data = json.loads(result.stdout)
                logger.debug(f"Status retrieved successfully")
                return status_data

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse status JSON: {e}")
                logger.debug(f"Raw output: {result.stdout}")
                raise JottaCLIError(f"Invalid JSON from jotta-cli: {e}")

        except subprocess.TimeoutExpired:
            raise JottaCLIError("Status command timed out - daemon may be unresponsive")

    def run_pause(self) -> bool:
        """
        Execute 'jotta-cli pause' to pause backup/sync.

        Returns:
            True if successful

        Raises:
            JottaCLIError: If pause command fails
        """
        try:
            result = self._run_command(["pause"])

            if result.returncode != 0:
                raise JottaCLIError(f"Pause failed: {result.stderr.strip()}")

            logger.info("Backup paused successfully")
            return True

        except subprocess.TimeoutExpired:
            raise JottaCLIError("Pause command timed out")

    def run_resume(self) -> bool:
        """
        Execute 'jotta-cli resume' to resume backup/sync.

        Returns:
            True if successful

        Raises:
            JottaCLIError: If resume command fails
        """
        try:
            result = self._run_command(["resume"])

            if result.returncode != 0:
                raise JottaCLIError(f"Resume failed: {result.stderr.strip()}")

            logger.info("Backup resumed successfully")
            return True

        except subprocess.TimeoutExpired:
            raise JottaCLIError("Resume command timed out")

    def get_logfile_path(self) -> Optional[Path]:
        """
        Execute 'jotta-cli logfile' to get the log file location.

        Returns:
            Path to log file, or None if not found

        Raises:
            JottaCLIError: If command fails
        """
        try:
            result = self._run_command(["logfile"])

            if result.returncode != 0:
                raise JottaCLIError(f"Logfile command failed: {result.stderr.strip()}")

            # Extract path from output (first line, strip whitespace)
            logfile_path = result.stdout.strip().split('\n')[0]

            if logfile_path and Path(logfile_path).exists():
                logger.debug(f"Log file found at: {logfile_path}")
                return Path(logfile_path)
            else:
                logger.warning(f"Log file not found at: {logfile_path}")
                return None

        except subprocess.TimeoutExpired:
            raise JottaCLIError("Logfile command timed out")

    def run_observe(self) -> subprocess.Popen:
        """
        Start 'jotta-cli observe --json' subprocess for real-time transfer monitoring.

        This starts a long-running subprocess that streams transfer events.
        The caller is responsible for managing the subprocess lifecycle.

        Returns:
            Popen object with stdout stream

        Raises:
            CLINotFoundError: If jotta-cli is not found
            JottaCLIError: If observe command fails to start
        """
        cmd = [self.cli_path, "observe", "--json"]

        try:
            logger.debug(f"Starting observe subprocess: {' '.join(cmd)}")
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,  # Line buffered
            )

            # Check if process started successfully
            if process.poll() is not None:
                stderr = process.stderr.read()
                raise JottaCLIError(f"Observe command failed to start: {stderr}")

            return process

        except FileNotFoundError:
            raise CLINotFoundError(f"jotta-cli not found at: {self.cli_path}")

    def check_available(self) -> bool:
        """
        Check if jotta-cli is available and responding.

        Returns:
            True if jotta-cli is available, False otherwise
        """
        try:
            self.run_status()
            return True
        except (CLINotFoundError, DaemonOfflineError):
            return False
        except JottaCLIError:
            # CLI exists but there's some other error
            return True
