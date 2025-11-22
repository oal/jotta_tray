# jotta-tray Distribution & Packaging

This directory contains packaging configurations for distributing jotta-tray across multiple platforms and package managers.

## 📦 Distribution Channels

jotta-tray is distributed through three primary channels:

1. **PyPI** - Python Package Index (`pip`, `pipx`)
2. **AUR** - Arch User Repository (Arch Linux & derivatives)
3. **Flatpak** - Universal Linux package (Flathub)

## Directory Structure

```
packaging/
├── aur/
│   ├── PKGBUILD          # Arch package build script
│   └── README.md         # AUR-specific documentation
├── flatpak/
│   ├── io.github.oal.jotta_tray.yml              # Flatpak manifest
│   ├── io.github.oal.jotta_tray.metainfo.xml     # AppStream metadata
│   └── README.md         # Flatpak-specific documentation
└── README.md             # This file
```

## Automated Release Workflow

When a new version is tagged (e.g., `v0.1.0`), the following happens automatically:

### 1️⃣ GitHub Release (`.github/workflows/release.yml`)
- Creates GitHub release with changelog
- Generates release notes from commits
- Triggers dependent workflows

### 2️⃣ PyPI Publishing (`.github/workflows/publish-pypi.yml`)
- Builds Python wheel and source distribution
- Publishes to PyPI using trusted publishing (OIDC)
- Makes package available via `pip` and `pipx`

### 3️⃣ AUR Update (`.github/workflows/update-aur.yml`)
- Downloads PyPI source tarball
- Calculates SHA256 checksum
- Updates PKGBUILD with new version
- Generates .SRCINFO
- Pushes to AUR repository

### 4️⃣ Flatpak Build (`.github/workflows/build-flatpak.yml`)
- Builds Flatpak package
- Validates AppStream metadata
- Uploads artifact for manual Flathub submission

## Distribution Comparison

| Feature | PyPI | AUR | Flatpak |
|---------|------|-----|---------|
| **Target Audience** | Python developers | Arch users | All Linux users |
| **Install Command** | `pipx install jotta-tray` | `yay -S jotta-tray` | `flatpak install io.github.oal.jotta_tray` |
| **Auto Dependencies** | Python only | All (system + Python) | All (bundled) |
| **Requires jotta-cli** | Yes (manual) | Yes (manual) | Yes (manual) |
| **Auto Updates** | No | Yes (via AUR helpers) | Yes (via Flatpak) |
| **Sandboxing** | No | No | Yes |
| **Disk Space** | ~1 MB | ~1 MB | ~100 MB (with runtime) |
| **Build Time** | Seconds | Minutes | Minutes |

## Release Checklist

Before creating a new release:

- [ ] Update version in `src/jotta_tray/__init__.py`
- [ ] Update version in `pyproject.toml`
- [ ] Update CHANGELOG or release notes
- [ ] Update AppStream metadata `releases` section if needed
- [ ] Verify all tests pass: `uv run pytest`
- [ ] Test build locally: `uv build`
- [ ] Test installation: `uv pip install dist/*.whl`
- [ ] Commit all changes
- [ ] Create and push tag: `git tag v0.1.0 && git push origin v0.1.0`
- [ ] Monitor automated workflows
- [ ] Verify PyPI publish succeeded
- [ ] Verify AUR package updated
- [ ] (Optional) Manually submit Flatpak to Flathub

## Manual Release Process

If automated workflows fail or you need to release manually:

### PyPI

```bash
# Build package
uv build

# Publish (requires PyPI API token)
uv publish

# Or use twine
pip install twine
twine upload dist/*
```

### AUR

See `aur/README.md` for detailed instructions.

```bash
# Clone AUR repo
git clone ssh://aur@aur.archlinux.org/jotta-tray.git

# Update PKGBUILD
cd jotta-tray
vim PKGBUILD

# Generate .SRCINFO
makepkg --printsrcinfo > .SRCINFO

# Push to AUR
git add PKGBUILD .SRCINFO
git commit -m "Update to version X.Y.Z"
git push
```

### Flatpak

See `flatpak/README.md` for detailed instructions.

```bash
# Build locally
flatpak-builder --force-clean build-dir packaging/flatpak/io.github.oal.jotta_tray.yml

# Test install
flatpak-builder --user --install build-dir packaging/flatpak/io.github.oal.jotta_tray.yml

# For Flathub submission, create PR to https://github.com/flathub/flathub
```

## Package Maintenance

### Dependency Updates

When updating dependencies in `pyproject.toml`:

1. Update PyPI package (automatic via workflow)
2. Update `packaging/aur/PKGBUILD` `depends` and `makedepends` arrays
3. Update `packaging/flatpak/io.github.oal.jotta_tray.yml` modules
4. Test all three distribution methods

### System Dependency Changes

If GTK, AppIndicator, or other system dependencies change:

1. Update README.md installation prerequisites
2. Update `packaging/aur/PKGBUILD` dependencies
3. Update `packaging/flatpak/io.github.oal.jotta_tray.yml` modules
4. Update CONTRIBUTING.md development setup

### Icon/Resource Changes

If adding or modifying icons or other resources:

1. Ensure they're included in `pyproject.toml` wheel config
2. Verify paths work in all installation scenarios
3. Test absolute path resolution (important for system tray)
4. Update Flatpak manifest resource paths

## GitHub Secrets Required

The automated workflows require these GitHub repository secrets:

- `AUR_SSH_KEY` - SSH private key for AUR repository access
  - Generate: `ssh-keygen -t ed25519 -C "aur@github-actions"`
  - Add public key to AUR account settings
  - Add private key to GitHub repository secrets

PyPI publishing uses trusted publishing (OIDC), which requires configuration in PyPI project settings but no manual token management.

## Troubleshooting

### PyPI publish fails

- Check that version number is unique (not already published)
- Verify trusted publishing is configured in PyPI
- Check workflow has correct permissions (`id-token: write`)

### AUR update fails

- Verify `AUR_SSH_KEY` secret is correctly configured
- Check that AUR repository exists and you have access
- Verify PyPI source tarball is available (may need delay)

### Flatpak build fails

- Check all source URLs are accessible
- Verify SHA256 checksums match
- Test build locally with `flatpak-builder`
- Validate manifest syntax with `yamllint`

## Support & Questions

- **General packaging questions**: Open an issue
- **PyPI specific**: See [Python Packaging Guide](https://packaging.python.org/)
- **AUR specific**: See [AUR submission guidelines](https://wiki.archlinux.org/title/AUR_submission_guidelines)
- **Flatpak specific**: See [Flatpak documentation](https://docs.flatpak.org/)

## Contributing

See `CONTRIBUTING.md` for guidelines on contributing to packaging and distribution.
