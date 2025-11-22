# Flatpak Package for jotta-tray

This directory contains the Flatpak manifest for distributing jotta-tray as a universal Linux package.

## Files

- `io.github.oal.jotta_tray.yml` - Flatpak manifest
- `io.github.oal.jotta_tray.metainfo.xml` - AppStream metadata

## Building Locally

### Prerequisites

```bash
# Install flatpak-builder
sudo apt install flatpak-builder  # Ubuntu/Debian
# or
sudo dnf install flatpak-builder  # Fedora
# or
sudo pacman -S flatpak-builder    # Arch

# Add Flathub repository
flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo

# Install Freedesktop runtime and SDK
flatpak install flathub org.freedesktop.Platform//23.08
flatpak install flathub org.freedesktop.Sdk//23.08
```

### Build

```bash
# From the packaging/flatpak directory
flatpak-builder --force-clean build-dir io.github.oal.jotta_tray.yml

# Install locally for testing
flatpak-builder --user --install --force-clean build-dir io.github.oal.jotta_tray.yml

# Run the application
flatpak run io.github.oal.jotta_tray
```

## Automated Builds

The GitHub Action (`.github/workflows/build-flatpak.yml`) will automatically:

1. Build the Flatpak on every pull request (for testing)
2. Upload the built package as an artifact
3. Validate the manifest and AppStream metadata

## Submitting to Flathub

### Initial Submission

1. Fork https://github.com/flathub/flathub
2. Create a new branch
3. Copy `io.github.oal.jotta_tray.yml` and `io.github.oal.jotta_tray.metainfo.xml`
4. Create a pull request to Flathub

### Automated Updates

After initial acceptance, you can set up the Flathub bot to automatically update:

1. Add a `.github/workflows/flathub-update.yml` to this repository
2. Configure it to trigger the Flathub bot on new releases

## Important Notes

### jotta-cli Dependency

The Flatpak sandbox cannot bundle `jotta-cli` automatically because it's:
- A proprietary binary distributed by Jottacloud
- Not available in standard package repositories
- Requires system-level daemon access

**Users must install jotta-cli separately** before using this Flatpak. The README should clearly document this requirement.

### System Tray Integration

The manifest includes permissions for:
- KDE StatusNotifier protocol
- Ayatana/Canonical AppIndicator
- DBus session bus
- Desktop notifications

These ensure compatibility across GNOME, KDE, XFCE, and other desktops.

### File System Access

The manifest provides:
- Read access to `~/.jottad` and `~/.config/jotta-cli` (for jotta-cli integration)
- Full access to `~/.config/jotta-tray` (for application config)
- Network access (for sync status checking)

## Testing Checklist

Before submitting to Flathub:

- [ ] Builds successfully with `flatpak-builder`
- [ ] Application launches without errors
- [ ] System tray icon appears correctly
- [ ] Can read jotta-cli status (when installed on host)
- [ ] Menu actions work correctly
- [ ] AppStream metadata validates: `flatpak run org.freedesktop.appstream-glib validate io.github.oal.jotta_tray.metainfo.xml`
- [ ] Desktop file validates: `desktop-file-validate *.desktop`

## Troubleshooting

### Build failures

Check that all source URLs are accessible and checksums match.

### Runtime not found

Ensure you've installed the Freedesktop runtime:
```bash
flatpak install flathub org.freedesktop.Platform//23.08
```

### Cannot access jotta-cli

The Flatpak needs filesystem access to jotta-cli's config directories. If users have jotta-cli installed in a non-standard location, they may need to add permissions:

```bash
flatpak override --user --filesystem=~/.custom-jotta-location io.github.oal.jotta_tray
```
