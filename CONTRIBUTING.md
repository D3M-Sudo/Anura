# Contributing to Anura OCR

> This file is read by AI coding agents (Cascade, Claude Code, Cursor, Aider).
> It complements AGENTS.md with workflow-specific guidelines.

## Quick Start

```bash
# 1. Clone and enter the repo
git clone https://github.com/d3msudo/anura && cd anura

# 2. Create virtualenv and install dev tools
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# 3. Install system dependencies (Ubuntu/Debian)
sudo apt install python3-gi gir1.2-gtk-4.0 gir1.2-adw-1 \
    blueprint-compiler libportal-gtk4-dev \
    tesseract-ocr python3-pil \
    gstreamer1.0-plugins-good gstreamer1.0-pulseaudio

# 4. Build with Meson
.venv/bin/meson setup builddir
.venv/bin/meson compile -C builddir

# 5. Run from source (no install needed)
GSETTINGS_SCHEMA_DIR=builddir/data python3 -m anura.main
```

## Running Tests

```bash
# All pure-Python tests (no GTK required)
pytest tests/ -v -m "not gtk"

# Skip network-dependent tests
pytest tests/ -v -m "not network"

# Run only a specific file
pytest tests/test_config.py -v

# Run URI validator tests specifically
pytest tests/test_uri_validator.py -v
```

## Linting

```bash
# Check only
ruff check anura/

# Fix auto-fixable issues
ruff check --fix anura/

# Format
ruff format anura/
```

## Branch & Commit Conventions

- Branch names: `fix/short-description`, `feat/short-description`
- Commit messages: `fix: description` / `feat: description` / `chore: description`
- Every bug fix should have a corresponding entry in `CHANGELOG.md` under `[Unreleased]`

## Adding a New Feature

1. Add the Python source in the correct module directory (see `AGENTS.md` → Repository Structure)
2. If the feature has a UI, add its `.blp` file in `data/ui/` and update `data/meson.build`
3. If the feature adds a new Python file to `anura/`, it will be picked up automatically by `install_subdir`
4. All user-facing strings must use `_()` — never raw strings in UI code
5. Run `./generate_pot.sh` after adding new translatable strings
6. Update `AGENTS.md` → Module Reference if you add a new module

## Files You Must NOT Edit Directly

| File | Reason |
|------|--------|
| `anura/_release_notes.py` | Generated at build time by Meson from CHANGELOG.md |
| `data/ui/*.ui` | Compiled from `.blp` by blueprint-compiler — edit `.blp` instead |
| `po/*.po` | Maintained by translators — use `./generate_pot.sh` to update |
| `flatpak/com.github.d3msudo.anura.json` | Dependency versions are pinned with SHA — update via FEDC only |
| `CHANGELOG.md` | Manual entries only — follows Keep a Changelog format |

## Security Checklist (before every PR)

- [ ] Language codes validated with `LANG_CODE_PATTERN` before Tesseract
- [ ] URLs validated with `uri_validator()` before `Gtk.UriLauncher`
- [ ] No `subprocess` calls (use GLib/GIO instead)
- [ ] No GTK/GObject signal emissions from secondary threads (use `GLib.idle_add`)
- [ ] File writes use `tempfile` + `shutil.move` (atomic)
- [ ] No new analytics, telemetry, or external data collection of any kind
