# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**jotta-tray** is a Linux system tray widget for monitoring Jotta Cloud sync status. It's a Python GTK3 application that uses AppIndicator3 to display sync status, storage usage, and provides quick actions through a context menu.

## Development Setup

### Prerequisites
- Python 3.10+
- [uv](https://docs.astral.sh/uv/) package manager
- GTK3 and AppIndicator3 system dependencies

### Installation

```bash
# Install dependencies
uv sync --dev

# Or install in development mode
uv pip install -e .
```

### Running the Application

```bash
# Run from source (recommended for development)
uv run python -m jotta_tray.main

# Or activate venv first
source .venv/bin/activate
python -m jotta_tray.main

# With debug logging
uv run python -m jotta_tray.main --debug
# or
.venv/bin/python -m jotta_tray.main --debug
```

### Testing

```bash
# Run all tests
uv run pytest tests/

# With activated venv
pytest tests/
```

## Architecture

### Module Structure

The application is organized into distinct modules with clear responsibilities:

- **main.py**: Application entry point and lifecycle management
  - `JottaTrayApp` class orchestrates all components
  - Handles signal handling (SIGINT, SIGTERM) for clean shutdown
  - Coordinates between CLI, monitor, and tray widget

- **cli_interface.py**: Wrapper around `jotta-cli` command-line tool
  - Executes CLI commands with JSON output parsing
  - Provides methods: `run_status()`, `run_pause()`, `run_resume()`, `get_logfile_path()`, `run_observe()`
  - Custom exceptions: `JottaCLIError`, `DaemonOfflineError`, `CLINotFoundError`

- **status_monitor.py**: Background polling service (runs in separate thread)
  - Polls `jotta-cli status` at adaptive intervals (2s active, 10s idle, 30s offline)
  - Emits status change events via callbacks
  - `SyncStatus` dataclass contains state snapshot
  - Thread-safe status updates using callback pattern

- **tray_widget.py**: GTK3/AppIndicator3 UI implementation
  - Uses AppIndicator3 for system tray icon
  - Icon states: idle, syncing, paused, error, offline
  - Context menu with storage info, pause/resume, open web, logs, settings, about, quit
  - **Important**: Uses absolute icon paths for Waybar compatibility

- **utils.py**: Formatting utilities
  - `format_bytes()`, `format_quota()`, `format_transfer_speed()`, `format_file_count()`
  - `parse_sync_state()`, `detect_quota_warning()`

### Threading Model

The application uses two threads:
1. **Main GTK thread**: Runs GTK event loop, handles all UI updates
2. **StatusMonitor thread**: Background daemon thread for polling jotta-cli

Communication between threads uses:
- Callback pattern from monitor to main app
- `GLib.idle_add()` to safely update UI from monitor thread (see main.py:106)

### Icon Path Resolution

Icons are located in `src/jotta_tray/icons/`. The `TrayWidget._find_icon_path()` method searches:
1. Module directory (`Path(__file__).parent / "icons"`)
2. Installed location in sys.path
3. Current directory (fallback)

**Critical**: AppIndicator requires absolute icon paths for Waybar compatibility (tray_widget.py:93-96).

### jotta-cli Integration

The application depends on the external `jotta-cli` tool being installed and configured:
- Must be in PATH
- Daemon (`jottad`) must be running for full functionality
- Application continues in "offline" state if daemon is unavailable

## Key Implementation Details

### State Management
- State is centralized in `SyncStatus` dataclass
- Status changes trigger callbacks to update UI
- Adaptive polling based on current state (active sync = faster polling)

### Error Handling
- Graceful degradation when jotta daemon is offline
- Timeout protection on CLI commands (default 5s)
- Error dialogs for user-facing failures

### Configuration
- Config file location: `~/.config/jotta-tray/config.ini`
- Auto-created on first access via Settings menu
- Contains polling intervals, notification preferences

## Package Structure

```
src/jotta_tray/
├── __init__.py
├── main.py              # Entry point and app lifecycle
├── cli_interface.py     # jotta-cli wrapper
├── status_monitor.py    # Background polling service
├── tray_widget.py       # GTK UI and system tray
├── utils.py             # Formatting utilities
└── icons/               # SVG icons for tray states
    ├── jotta-idle.svg
    ├── jotta-syncing.svg
    ├── jotta-paused.svg
    ├── jotta-error.svg
    └── jotta-offline.svg
```

## Dependencies

### Runtime
- **PyGObject (>=3.40.0)**: Python bindings for GTK3 and AppIndicator3

### Development
- **pytest (>=7.0)**: Testing framework
- **pytest-cov (>=4.0)**: Coverage reporting

### System (not in pyproject.toml)
- GTK3
- AppIndicator3
- jotta-cli (external tool)

## Entry Point

The `jotta-tray` command is registered in pyproject.toml as a console script pointing to `jotta_tray.main:main`.
