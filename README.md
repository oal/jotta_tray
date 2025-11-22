# Jotta Cloud System Tray Widget

A lightweight system tray widget for Linux that provides at-a-glance monitoring of Jotta Cloud sync status, storage usage, and quick access to common actions.

## Features

- 🔄 Real-time sync status monitoring
- 💾 Storage quota display
- 🚀 Quick actions menu (pause/resume, open web, view logs)
- 🔔 Desktop notifications for important events
- 🖥️ Works with GNOME, KDE, XFCE, and other desktop environments

## System Requirements

- **Operating System:** Linux (tested on Ubuntu 22.04+, Fedora 38+, Arch Linux)
- **Python:** 3.10 or higher
- **Desktop Environment:** GTK3-based (GNOME, XFCE) or Qt-based (KDE Plasma)
- **Dependencies:**
  - PyGObject (Python GTK bindings)
  - GTK3
  - AppIndicator3
- **Required Software:** `jotta-cli` (Jotta Cloud command-line tool) must be installed and configured

## Installation

Choose the installation method that works best for your system:

### 🚀 Quick Install (Recommended)

#### via pipx (All Linux distributions)

```bash
# Install pipx if you don't have it
sudo apt install pipx  # Ubuntu/Debian
# or
sudo dnf install pipx  # Fedora
# or
sudo pacman -S python-pipx  # Arch

# Install jotta-tray
pipx install jotta-tray
```

**Note:** You'll need to install system dependencies separately (see [Prerequisites](#prerequisites) below).

#### via AUR (Arch Linux & Manjaro)

```bash
# Using yay
yay -S jotta-tray

# Or using paru
paru -S jotta-tray
```

This automatically installs all system dependencies.

#### via Flatpak (Universal)

```bash
flatpak install flathub io.github.oal.jotta_tray
```

This is the easiest method as all dependencies are bundled.

### 📦 Other Installation Methods

<details>
<summary><b>From PyPI with pip</b></summary>

```bash
# Install system dependencies first (see Prerequisites below)

# Install using pip
pip install --user jotta-tray

# Or system-wide (not recommended)
sudo pip install jotta-tray
```
</details>

<details>
<summary><b>From source (for development)</b></summary>

This project uses [uv](https://docs.astral.sh/uv/) for dependency management. Install it first:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then clone and install:

```bash
# Clone the repository
git clone https://github.com/oal/jotta_tray.git
cd jotta_tray

# Install in development mode with dev dependencies
uv sync --dev

# Or install in production mode
uv sync
```
</details>

### Prerequisites

**All installation methods require:**

1. **jotta-cli** - The official Jotta Cloud command-line tool
   - Download from [jottacloud.com](https://www.jottacloud.com/downloads)
   - Must be configured and logged in before using jotta-tray

2. **System dependencies** (automatically installed by AUR and Flatpak):

   ```bash
   # Ubuntu/Debian
   sudo apt install python3-gi gir1.2-gtk-3.0 gir1.2-appindicator3-0.1

   # Fedora
   sudo dnf install python3-gobject gtk3 libappindicator-gtk3

   # Arch Linux (if not using AUR)
   sudo pacman -S python-gobject gtk3 libappindicator-gtk3
   ```

## Usage

### Start the widget

```bash
jotta-tray
```

The widget will appear in your system tray with an icon indicating the current sync status.

### Icon States

- **Idle (cloud):** All files synced, no active transfers
- **Syncing (arrows):** Active upload or download in progress
- **Paused (pause):** Sync manually paused
- **Error (warning):** Sync error detected
- **Offline (gray):** Jotta daemon not running

### Context Menu Actions

Right-click the tray icon to access:

- **Storage info:** Current usage and quota
- **Pause/Resume Backup:** Temporarily stop or restart syncing
- **Open Jottacloud Web:** Launch web interface in browser
- **View Logs:** Open log file in text editor
- **Settings:** Configure autostart and other preferences
- **About:** Version and credits
- **Quit:** Close the tray widget

### Autostart on Login

You can configure jotta-tray to start automatically when you log in using either the GUI or command line:

#### Using the GUI (Recommended)

1. Right-click the tray icon and select **Settings**
2. Check the **"Start automatically at login"** checkbox
3. Click **Save**

#### Using Command Line

```bash
# Enable autostart
jotta-tray --install-autostart

# Disable autostart
jotta-tray --uninstall-autostart

# Check autostart status
jotta-tray --check-autostart
```

The autostart feature uses XDG autostart standards (`~/.config/autostart/jotta-tray.desktop`), which is compatible with all major Linux desktop environments including GNOME, KDE, XFCE, Sway, Hyprland, and others.

## Configuration

Configuration file location: `~/.config/jotta-tray/config.ini`

A default configuration file will be created on first run. You can customize:

- Polling intervals
- Notification preferences
- Icon theme
- Menu options

(Full configuration documentation coming soon)

## Development

### Running from source

```bash
# Using uv
uv run python -m jotta_tray.main

# Or activate the virtual environment first
source .venv/bin/activate
python -m jotta_tray.main
```

### Running tests

```bash
# Using uv
uv run pytest tests/

# Or with activated virtual environment
pytest tests/
```

## Troubleshooting

### Widget doesn't appear in system tray

- **GNOME:** Ensure AppIndicator extension is installed
- **KDE:** Check system tray settings allow new icons
- **XFCE:** Verify "Notification Area" panel plugin is active

### "Jotta daemon not running" error

```bash
# Check if jottad is running
jotta-cli status

# Start the daemon if needed
sudo systemctl start jottad  # systemd
```

### Icon not changing/updating

- Check that `jotta-cli status --json` returns valid output
- Review logs: `~/.local/share/jotta-tray/app.log`

## Uninstallation

```bash
# Remove package
uv pip uninstall jotta-tray

# Remove configuration and data
rm -rf ~/.config/jotta-tray ~/.local/share/jotta-tray

# Remove autostart entry (if enabled)
rm ~/.config/autostart/jotta-tray.desktop
```

## License

MIT License (see LICENSE file)

## Credits

Created for Jotta Cloud users who want seamless desktop integration on Linux.

Built with PyGObject and GTK3.
