# AUR Package for jotta-tray

This directory contains the PKGBUILD for submitting jotta-tray to the Arch User Repository (AUR).

## Initial Setup (One-time)

### 1. Create AUR Account

1. Go to https://aur.archlinux.org/register
2. Create an account
3. Add your SSH public key to your AUR account

### 2. Create AUR Package Repository

```bash
# Clone the AUR package template
git clone ssh://aur@aur.archlinux.org/jotta-tray.git aur-jotta-tray
cd aur-jotta-tray

# Copy PKGBUILD from this directory
cp /path/to/jotta_tray/packaging/aur/PKGBUILD .

# Generate .SRCINFO
makepkg --printsrcinfo > .SRCINFO

# Commit and push
git add PKGBUILD .SRCINFO
git commit -m "Initial import: jotta-tray 0.1.0"
git push
```

### 3. Set up GitHub Secret for Automation

1. Go to your GitHub repository settings
2. Navigate to Secrets and Variables → Actions
3. Add a new secret named `AUR_SSH_KEY`
4. Paste your SSH private key (the one whose public key is registered on AUR)

## Automated Updates

After initial setup, the GitHub Action (`.github/workflows/update-aur.yml`) will automatically:

1. Trigger when you publish a new release
2. Download the PyPI source tarball
3. Calculate the SHA256 checksum
4. Update PKGBUILD with new version and checksum
5. Generate .SRCINFO
6. Push to AUR repository

## Manual Updates

If you need to update manually:

```bash
# Update pkgver in PKGBUILD
vim PKGBUILD

# Download source and calculate checksum
wget https://files.pythonhosted.org/packages/source/j/jotta-tray/jotta-tray-X.Y.Z.tar.gz
sha256sum jotta-tray-X.Y.Z.tar.gz

# Update sha256sums in PKGBUILD
vim PKGBUILD

# Test build
makepkg -si

# Generate .SRCINFO
makepkg --printsrcinfo > .SRCINFO

# Commit and push to AUR
git add PKGBUILD .SRCINFO
git commit -m "Update to X.Y.Z"
git push
```

## Dependencies

The PKGBUILD declares all necessary dependencies:

- **Runtime:** python, python-gobject, gtk3, libappindicator-gtk3, jotta-cli
- **Build:** python-build, python-installer, python-wheel, python-hatchling
- **Optional:** gnome-shell-extension-appindicator (for GNOME users)

## Maintainer Notes

- Update the maintainer information in PKGBUILD before submitting
- The `jotta-cli` dependency must be installed separately by users
- PKGBUILD follows Arch packaging guidelines for Python packages
