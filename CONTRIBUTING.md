# Contributing to jotta-tray

Thank you for considering contributing to jotta-tray! This document provides guidelines and instructions for contributing.

## Code of Conduct

Be respectful and constructive. We're all here to make jotta-tray better for everyone.

## Development Setup

### Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) package manager
- System dependencies: GTK3, AppIndicator3
- jotta-cli installed and configured

### Setting Up Development Environment

```bash
# Clone the repository
git clone https://github.com/oal/jotta_tray.git
cd jotta_tray

# Install dependencies
uv sync --dev

# Run in development mode
uv run python -m jotta_tray.main --debug
```

### Running Tests

```bash
uv run pytest tests/
```

## Making Changes

### Branch Strategy

- `main` - Stable releases
- `distribution` - Distribution/packaging work
- Feature branches - Use descriptive names like `feature/new-menu-item` or `fix/icon-not-updating`

### Commit Messages

Follow conventional commits format:

- `feat: Add storage usage chart`
- `fix: Icon not updating on sync state change`
- `docs: Update installation instructions`
- `refactor: Simplify status polling logic`
- `test: Add tests for CLI interface`

### Code Style

- Follow PEP 8
- Use type hints where applicable
- Add docstrings to public functions and classes
- Keep functions focused and small

## Submitting Changes

1. Fork the repository
2. Create a feature branch from `main`
3. Make your changes with clear commit messages
4. Add tests if applicable
5. Ensure tests pass: `uv run pytest`
6. Submit a pull request

### Pull Request Guidelines

- Provide a clear description of the changes
- Reference any related issues
- Include screenshots for UI changes
- Ensure CI checks pass

## Packaging and Distribution

jotta-tray is distributed through multiple channels. Changes to packaging should be made in the `distribution` branch.

### Package Structure

```
packaging/
├── aur/           # Arch User Repository (PKGBUILD)
├── flatpak/       # Flatpak manifest and metadata
└── README.md      # Packaging documentation
```

### Release Process

1. **Update Version**
   - Update version in `src/jotta_tray/__init__.py`
   - Update version in `pyproject.toml`
   - Update changelog in AppStream metadata if needed

2. **Test Locally**
   ```bash
   # Build and test package
   uv build

   # Test installation
   uv pip install dist/jotta_tray-*.whl
   jotta-tray --version
   ```

3. **Create Release**
   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   ```

4. **Automated Workflows**
   The following will happen automatically:
   - GitHub Release is created
   - PyPI package is published
   - AUR PKGBUILD is updated
   - Flatpak build is created

### Updating Packaging Files

#### PyPI (pyproject.toml)

- Ensure all dependencies are correctly listed
- Update classifiers if adding new Python version support
- Verify wheel includes all necessary files

#### AUR (packaging/aur/PKGBUILD)

- Keep dependency lists synchronized with pyproject.toml
- Update `pkgrel` for packaging-only changes
- Test builds in clean chroot: `makepkg -C`

#### Flatpak (packaging/flatpak/)

- Update manifest when adding new dependencies
- Test builds locally with `flatpak-builder`
- Validate AppStream metadata: `appstream-util validate-relax`
- Update runtime version cautiously (breaks existing installs)

### Package Testing Checklist

Before releasing:

- [ ] PyPI package installs correctly: `pipx install jotta-tray`
- [ ] AUR package builds: `makepkg -si` (in clean chroot)
- [ ] Flatpak builds: `flatpak-builder build-dir manifest.yml`
- [ ] Desktop file is valid: `desktop-file-validate`
- [ ] Icons are accessible in all installation methods
- [ ] Entry point works: `jotta-tray --version`
- [ ] Autostart integration works

## Documentation

### Code Documentation

- Add docstrings to new functions and classes
- Update `CLAUDE.md` if changing architecture
- Keep README.md installation instructions current

### User Documentation

Update README.md when:
- Adding new features
- Changing installation requirements
- Modifying system dependencies
- Changing configuration options

## Issue Reporting

### Bug Reports

Include:
- jotta-tray version: `jotta-tray --version`
- Python version: `python --version`
- Distribution and version: `cat /etc/os-release`
- Desktop environment
- jotta-cli version and status
- Steps to reproduce
- Expected vs actual behavior
- Relevant log output

### Feature Requests

Include:
- Clear description of the feature
- Use case / problem it solves
- How you envision it working
- Any alternative solutions considered

## Questions?

- Open an issue for questions about contributing
- Check existing issues and pull requests first

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Recognition

Contributors will be recognized in release notes and may be added to a CONTRIBUTORS file.

Thank you for helping make jotta-tray better! 🎉
