# AGENTS.md — Anura OCR AI Assistant Guide

> Canonical AI-assistant guide for this repository. Also read by Claude Code, Cursor, Aider, Continue, and Zed via the AGENTS.md convention.

## Project Overview

Anura OCR is a GTK4/Libadwaita desktop application for GNOME that extracts text from screenshots, images, and clipboard using Tesseract OCR, with QR code support, text-to-speech, and social sharing. It is a fork of Frog OCR with complete telemetry removal.

**Key Facts:**

- Python 3.11+ required
- GTK4 + Libadwaita + Blueprint Compiler for declarative UI
- OCR via `pytesseract` (Tesseract 5.x wrapper)
- QR code via `pyzbar` + `zbar`
- TTS via `gTTS` + GStreamer `playbin3`
- Screenshots via XDG Desktop Portal (`libportal` / `Xdp`)
- Distributed as Flatpak (`com.github.d3msudo.anura`) — GNOME 49 runtime
- Internationalization with gettext: 25+ languages (see `po/LINGUAS`)
- Build system: Meson ≥ 1.5.0
- License: MIT

## Repository Structure

```
anura/
├── anura/                      Python application source
│   ├── main.py                 AnuraApplication (Adw.Application) + CLI + AboutDialog
│   ├── window.py               AnuraWindow — DnD, FileDialog, paste, URI validation
│   ├── config.py               Constants APP_ID, tessdata URL, lang_code validation
│   ├── gobject_worker.py       Generic thread pool with GLib.idle_add
│   ├── language_manager.py     Tessdata model download/management (singleton)
│   ├── services/
│   │   ├── screenshot_service.py   Screenshot capture via Xdp.Portal
│   │   ├── clipboard_service.py    Clipboard read/write (Gdk.Clipboard)
│   │   ├── notification_service.py Notifications: XDG Portal → libnotify fallback
│   │   ├── tts.py                  Text-to-speech via gTTS + GStreamer
│   │   ├── share_service.py        Social sharing (5 providers)
│   │   └── settings.py             GSettings singleton wrapper
│   ├── types/
│   │   ├── download_state.py       DownloadState enum
│   │   └── language_item.py        LanguageItem dataclass
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── validators.py          URI validation utilities
│   │   ├── cleanup.py             Resource cleanup utilities
│   │   └── signal_manager.py      GLib signal management
│   ├── widgets/
│   │   ├── extracted_page.py       OCR result page with share/TTS actions
│   │   ├── language_popover.py     Language selector with search
│   │   ├── language_popover_row.py Language row in popover
│   │   ├── language_row.py         Language row in preferences page
│   │   ├── list_menu_row.py        Generic menu row
│   │   ├── preferences_dialog.py   Preferences dialog (Adw.PreferencesDialog)
│   │   ├── preferences_general_page.py   General preferences page
│   │   ├── preferences_languages_page.py Language management/download page
│   │   ├── share_row.py            Share provider row
│   │   └── welcome_page.py         Welcome page
├── data/
│   ├── ui/                     Blueprint files (.blp) → compiled to .ui
│   ├── icons/                  Scalable SVG icons + symbolic variants
│   ├── screenshots/            Screenshots for Flathub/metainfo
│   ├── com.github.d3msudo.anura.desktop.in
│   ├── com.github.d3msudo.anura.gresource.xml
│   ├── com.github.d3msudo.anura.gschema.xml
│   ├── com.github.d3msudo.anura.metainfo.xml.in
│   └── style.css
├── flatpak/
│   └── com.github.d3msudo.anura.json   Flatpak manifest with all dependencies
├── build-aux/
│   ├── generate_release_notes.py   CHANGELOG.md parser → _release_notes.py
│   └── meson/postinstall.py
├── bin/
│   └── anura.in                Entry point script (installed as `anura`)
├── po/                         Gettext translations (25+ languages)
├── .github/
│   ├── workflows/
│   │   ├── main.yml                    CI build and smoke tests
│   │   └── flatpak-dependencies.yml    Weekly FEDC + auto-PR certifi
│   └── dependabot.yml                  Automatic pip and Actions updates
├── meson.build                 Main build (also generates _release_notes.py)
├── CHANGELOG.md                Versioned changelog (source for release notes)
└── release.sh                  Release script (pin tessdata SHA, bump version)
```

## Development Commands

### Environment Setup

```bash
# System dependencies (Ubuntu/Debian)
sudo apt install python3-gi gir1.2-gtk-4.0 gir1.2-adw-1 \
    blueprint-compiler libportal-gtk4-dev \
    tesseract-ocr python3-pil python3-pip \
    gstreamer1.0-plugins-good gstreamer1.0-pulseaudio

# Python dependencies
pip install pytesseract gtts pyzbar loguru pillow requests

# Build with Meson (local development)
meson setup builddir
meson compile -C builddir

# Run from source tree (without installing)
GSETTINGS_SCHEMA_DIR=builddir/data python3 -m anura.main
```

### Flatpak Build

```bash
# Full build
flatpak-builder --force-clean builddir flatpak/com.github.d3msudo.anura.json

# Run the build
flatpak-builder --run builddir flatpak/com.github.d3msudo.anura.json anura

# Install locally for testing
flatpak-builder --install --user builddir flatpak/com.github.d3msudo.anura.json
```

### Local Build with Meson (venv)

To test the build system without Flatpak:

```bash
# System requirements needed:
sudo apt install blueprint-compiler libportal-gtk4-dev

# Setup and build using venv meson
.venv/bin/meson setup builddir
.venv/bin/meson compile -C builddir

# Full local install (optional)
.venv/bin/meson install -C builddir --destdir /tmp/install-test
```

### Flatpak Dependency Updates

```bash
# Check for available updates (dry-run)
flatpak-external-data-checker --dry-run flatpak/com.github.d3msudo.anura.json

# Apply updates (requires manual verification for critical dependencies)
flatpak-external-data-checker --update flatpak/com.github.d3msudo.anura.json
```

### Internationalization

```bash
# Regenerate POT template after string changes
./generate_pot.sh

# Update existing .po files
for lang in po/*.po; do msgmerge -U "$lang" po/anura.pot; done
```

## Dependency Management

Anura uses a hybrid dependency system: Python packages via pip/venv for dev tools, and native dependencies via Flatpak for runtime.

### Python Dependencies (Development Tools)

**File:** `pyproject.toml`

Development dependencies (linter, build system):

```toml
[project.optional-dependencies]
dev = [
    "ruff>=0.15.0",      # Linter and formatter
    "meson>=1.5.0",      # Build system (optional, for local testing)
]
```

**Virtual Environment:** `.venv/` (already present in repo, not committed)

```bash
# Install all dev dependencies
pip install -e ".[dev]"

# Or specifically meson for local build testing
pip install "meson>=1.5.0"
# Automatically installs ninja if needed
```

**Typical venv packages for testing:**
- `meson` — Build system
- `ninja` — Build tool (meson dependency)
- `ruff` — Linter
- `pytesseract`, `Pillow`, `pyzbar` — For local OCR testing (requires system tesseract)

### Runtime Dependencies (Flatpak/System)

**File:** `flatpak/com.github.d3msudo.anura.json`

Native dependencies compiled in the Flatpak:

| Module | Version | Purpose |
|--------|---------|---------|
| leptonica | 1.85.0 | Image processing for Tesseract |
| tesseract | 5.5.0 | OCR engine |
| tessdata-fast | pinned | Language models (eng, ita) |
| libportal | 0.9.1 | XDG Desktop Portal API |
| zbar | 0.23.93 | QR code decoding |
| blueprint-compiler | 0.16.0 | UI compilation .blp → .ui |

Python runtime dependencies (installed in Flatpak):
- pytesseract, Pillow, pyzbar, gTTS, loguru, requests, etc.

### Build System Configuration

**File:** `meson.build`

```meson
project('anura',
    version: '0.1.4',
    meson_version: '>= 1.5.0',
    ...
)
```

Release notes generation from CHANGELOG.md:
```meson
custom_target('release_notes',
  input: ['CHANGELOG.md', 'build-aux/generate_release_notes.py'],
  output: '_release_notes.py',
  ...
)
```

**Build commands with venv:**
```bash
.venv/bin/meson setup builddir
.venv/bin/meson compile -C builddir
```

## Code Patterns & Conventions

### Thread Safety — Fundamental Rule

**Never emit GObject signals or modify GTK widgets from secondary threads.**
Always use `GLib.idle_add()` to schedule UI operations from the main thread:

```python
# CORRECT — emit from secondary thread
GLib.idle_add(self.emit, "decoded", text, copy)
GLib.idle_add(self.emit, "error", _("Error message"))

# WRONG — crash from race condition
self.emit("decoded", text, copy)  # ← never do this from a thread
```

### Atomic Cancellation Pattern

Core services use `__slots__` for memory efficiency and implement atomic cancellation:

```python
class ClipboardService(GObject.GObject):
    __slots__ = ("_cancellable", "_clipboard", "_clipboard_timeout_id")
    
    def cancel_pending_operations(self) -> None:
        """Cancel any pending operations atomically."""
        if self._cancellable is not None and not self._cancellable.is_cancelled():
            self._cancellable.cancel()
        if self._clipboard_timeout_id and self._clipboard_timeout_id > 0:
            GLib.source_remove(self._clipboard_timeout_id)
            self._clipboard_timeout_id = None
        self._cancellable = None
```

### GLib MainContext — Silent Mode and Custom Loops

When creating a custom `GLib.MainLoop` (e.g., silent CLI mode), GLib sources must be **explicitly** attached to the loop's context:

```python
ctx = GLib.MainContext.new()
loop = GLib.MainLoop.new(ctx, False)

# CORRECT — source attached to ctx
timeout_source = GLib.timeout_source_new_seconds(60)
timeout_source.set_callback(on_timeout)
timeout_source.attach(ctx)

idle_source = GLib.idle_source_new()
idle_source.set_callback(on_done)
idle_source.attach(ctx)

# WRONG — attaches to default context, never invoked by loop.run()
GLib.idle_add(on_done)           # ← don't do this in a custom loop
GLib.timeout_add_seconds(60, cb) # ← same issue
```

### Internationalization (i18n)

All user-facing strings must be translatable with gettext:

```python
from gettext import gettext as _
from gettext import ngettext

# Simple strings
label.set_text(_("Extracted text"))

# WRONG — xgettext doesn't extract f-strings
label.set_text(_(f"Language: {lang}"))

# CORRECT — format after translation
label.set_text(_("Language: {lang}").format(lang=lang))

# Plurals
msg = ngettext("{n} file processed", "{n} files processed", count).format(n=count)
```

**Do NOT translate:**
- Logger messages (`logger.debug/info/warning/error`)
- Developer exceptions
- GSettings keys, CSS class names, D-Bus paths, technical identifiers

### lang_code Validation

Always validate any language code before passing to Tesseract using the regex in `config.py`:

```python
from anura.config import LANG_CODE_PATTERN

if not re.match(LANG_CODE_PATTERN, lang_code):
    raise ValueError(f"Invalid language code: {lang_code}")
```

### URI and URL Handling

Always validate URIs before opening or displaying to user. The `uri_validator()` function in `anura/utils/validators.py` protects against homograph attacks, control characters, and disallowed schemes.

```python
from anura.utils.validators import uri_validator

# Use validator before Gtk.UriLauncher
if uri_validator(url):
    launcher = Gtk.UriLauncher.new(url)
    launcher.launch(...)
```

### XDG Desktop Portal — Screenshots

Always use `Xdp.Portal` for screenshots. Do not use direct Wayland or X11 APIs.

### Notifications

Always use `NotificationService` — never `Notify.Notification` directly. The service automatically falls back from XDG Portal to libnotify.

### GStreamer TTS

Use `playbin3` (not deprecated `playbin`). GStreamer resource cleanup must occur under a lock to prevent race conditions.

### Tessdata Download — Atomic Writes

Downloads use atomic writes with `tempfile` + `shutil.move` to prevent corruption.

### Release Notes — Build Time

Release notes for `Adw.AboutDialog` are generated from `CHANGELOG.md` during Meson build. Do NOT generate them at runtime.

## Security Considerations

1. **lang_code validation**: always use `LANG_CODE_PATTERN` before passing to Tesseract (injection prevention)
2. **URI validation**: use `uri_validator()` before opening URLs (homograph attack protection)
3. **Atomic writes**: use `tempfile` + `shutil.move` for downloads
4. **Thread safety**: use `GLib.idle_add()` for all emissions from secondary threads
5. **No runtime subprocess**: never use `subprocess` for operations possible via GLib/GIO
6. **Flatpak sandbox**: don't assume filesystem access beyond `xdg-download`
7. **No telemetry**: Anura is privacy-first — never add analytics without explicit user consent

## Module Reference

| Module | Responsibility |
|---|---|
| `anura/main.py` | Application lifecycle, CLI parsing, AboutDialog |
| `anura/window.py` | Main window, DnD, FileDialog, URI validation |
| `anura/config.py` | App constants and configuration |
| `anura/language_manager.py` | Tessdata download/management (singleton) |
| `anura/services/screenshot_service.py` | XDG Portal screenshot + OCR/QR |
| `anura/services/notification_service.py` | Notifications with fallback |
| `anura/services/tts.py` | Text-to-speech via gTTS + GStreamer |
| `anura/services/share_service.py` | Social sharing providers |
| `anura/utils/validators.py` | URI validation and security utilities |
| `anura/utils/cleanup.py` | Resource cleanup utilities |
| `anura/utils/signal_manager.py` | GLib signal management |

### Configuration Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | Python project config, dev deps (ruff, meson) |
| `meson.build` | Main build system, generates `_release_notes.py` |
| `flatpak/com.github.d3msudo.anura.json` | Flatpak manifest with all native dependencies |
| `build-aux/generate_release_notes.py` | CHANGELOG.md parser → `_release_notes.py` |
| `CHANGELOG.md` | Versioned changelog (source for release notes) |

## Testing

### Test Architecture

Anura uses a comprehensive test suite with two main categories:

1. **Unit Tests** (`tests/test_unit_logic.py`) - Pure Python business logic without GTK dependencies
2. **Service Tests** (`tests/test_*_service.py`) - Service-specific tests with mocked GTK dependencies

### Test Files

| File | Purpose | Dependencies |
|------|---------|--------------|
| `tests/test_unit_logic.py` | Business logic validation (URL encoding, language mapping, validation) | Pure Python |
| `tests/test_screenshot_service.py` | Screenshot capture, OCR, QR decoding | Mocked Xdp.Portal |
| `tests/test_clipboard_service.py` | Clipboard read/write operations | Mocked Gdk.Clipboard |
| `tests/test_share_service.py` | Social sharing providers, URL validation | Mocked Gtk.UriLauncher |
| `tests/test_tts_service.py` | Text-to-speech, language mapping, GStreamer | Mocked GStreamer |
| `tests/test_notification_service.py` | Notifications with XDG Portal/libnotify fallback | Mocked Xdp.Portal |
| `tests/conftest.py` | Shared fixtures, environment isolation | Pure Python |

### Running Tests

```bash
# All pure-Python tests (no GTK required)
pytest tests/ -v -m "not gtk"

# Unit logic tests only
pytest tests/test_unit_logic.py -v

# Setup GSettings schema for GTK tests (required once)
mkdir -p builddir
cp data/com.github.d3msudo.anura.gschema.xml builddir/
glib-compile-schemas builddir/

# Service-specific tests (requires system gi + GSettings)
export GSETTINGS_SCHEMA_DIR="builddir"
pytest tests/test_screenshot_service.py -v
pytest tests/test_clipboard_service.py -v
pytest tests/test_share_service.py -v
pytest tests/test_tts_service.py -v
pytest tests/test_notification_service.py -v

# Or use automated setup script
./setup-gschema.sh

# GTK tests (require Flatpak environment)
flatpak run --devel --command=bash com.github.d3msudo.anura
python3 -m pytest tests/ -m "gtk" -v
```

### Test Patterns

**Mocking GTK Dependencies:**
```python
def setup_method(self):
    self.service = ScreenshotService()
    self.service.portal = Mock()  # Avoid Xdp dependency
```

**Business Logic Testing:**
```python
def test_language_mapping(self):
    service = TTSService()
    result = service.get_effective_language("eng")
    assert result == "en"
```

**Error Handling:**
```python
def test_service_error(self):
    with patch.object(self.service.portal, 'send_notification', side_effect=Exception("Error")):
        # Test graceful error handling
        self.service.show_notification("Title", "Body")
```

### CI/CD Considerations

- **Unit tests** run in standard CI (no system dependencies)
- **GTK tests** require Flatpak runtime environment
- **Environment isolation** via `conftest.py` fixtures
- **Coverage** focuses on business logic and error paths

### Common Testing Issues

#### Error: `RuntimeError: GSettings schema 'com.github.d3msudo.anura' not found`
**Cause**: GSettings schema not compiled or not in schema path
**Fix**: 
```bash
mkdir -p builddir
cp data/com.github.d3msudo.anura.gschema.xml builddir/
glib-compile-schemas builddir/
export GSETTINGS_SCHEMA_DIR="builddir"
```

#### Error: `ModuleNotFoundError: No module named 'gi'`
**Cause**: Virtual environment doesn't have access to system packages
**Fix**: Use PYTHONPATH and GI_TYPELIB_PATH:
```bash
uv run env PYTHONPATH="/usr/lib/python3/dist-packages:$PYTHONPATH" GI_TYPELIB_PATH="/usr/lib/x86_64-linux-gnu/girepository-1.0:/usr/lib/girepository-1.0" pytest tests/ -v
```

#### Complete GTK Test Setup
```bash
# One-time setup
./setup-gschema.sh

# Run tests
export GSETTINGS_SCHEMA_DIR="builddir"
uv run env PYTHONPATH="/usr/lib/python3/dist-packages:$PYTHONPATH" GI_TYPELIB_PATH="/usr/lib/x86_64-linux-gnu/girepository-1.0:/usr/lib/girepository-1.0" GSETTINGS_SCHEMA_DIR="builddir" pytest tests/ -v
```

## For Cascade / AI Agents

- Read this file BEFORE any operation on the codebase
- Do NOT add dependencies not present in the Flatpak manifest without discussing first
- The only official linter is `ruff` — do not suggest flake8, pylint or black
- Never modify: `po/*.po`, `anura/_release_notes.py`, `data/ui/*.ui`, `CHANGELOG.md`
- After any new UI string, remind the user to run `./generate_pot.sh`
- Thread safety: never emit GObject signals from secondary threads — use `GLib.idle_add()`
- When in doubt about an architectural choice, ask before proceeding

### Test Architecture Note

`anura/__init__.py` imports `gi` at module level, so ALL tests that import from `anura` require PyGObject (`python3-gi` system package) and must be marked with `@pytest.mark.gtk`. Only tests with zero `anura` imports (like `test_uri_validator.py`) run without a GTK environment.

## Decision Log

| Date | Decision | Reason |
|------|----------|--------|
| 2026-05-03 | Removed set_paintable() from welcome_page.py | Gdk.Texture on transparent widget causes checkerboard pattern |
| 2026-05-03 | osd filter added to get_downloaded_codes() | osd.traineddata is a Tesseract orientation file, not a real language |
| 2026-05-03 | new_item None guard added in populate_model() | Prevents crash if get_language_item("eng") returns None |
| 2026-05-03 | SIM105 added to ruff ignore list in pyproject.toml | Pre-existing style preference across the codebase |
| 2026-05-03 | Bug 1/2/3 main fixes were already applied in a previous session | Verified via pre-fix grep checks from bug report v2 |
| 2026-05-03 | GSK_RENDERER=cairo added to Flatpak finish-args | GL renderer fails on non-GNOME desktops (LXQt, XFCE, KDE) causing grayed-out UI |
| 2026-05-03 | Defensive audit confirmed: button state controlled by Gio.SimpleAction via action-name, not set_sensitive | No Python sensitivity code needed — GTK handles it automatically |
| 2026-05-03 | Full ruff cleanup — zero warnings across entire codebase | 28 pre-existing warnings fixed in 14 files |
| 2026-05-03 | Added test_language_manager.py — 8 tests for pure-Python LanguageManager methods | All marked @pytest.mark.gtk, deselected correctly without GTK environment |
| 2026-05-03 | GTK tests require Flatpak sandbox — Xdp namespace not available on host | Use pytest -m "not gtk" on host; run full suite inside flatpak sandbox |
| 2026-05-03 | Regenerated anura.pot and synced all 25 .po files via msgmerge | 91 stale strings removed, share_service.py added to POTFILES, 262 active strings |
| 2026-05-04 | Fixed __slots__ conflict in ClipboardService | Missing _cancellable in declaration causing AttributeError |
| 2026-05-04 | Extracted URI validation to utils module | Centralized security utilities and relaxed IP/localhost restrictions |
| 2026-05-04 | Implemented atomic cancellation pattern | Enhanced thread safety across Clipboard, TTS, and Screenshot services |
| 2026-05-04 | Fixed ruff linting errors across codebase | Resolved import sorting and code style issues in 14 files |
| 2026-05-04 | Fixed Flatpak manifest warnings | Removed _comment properties causing flatpak-builder warnings |
| 2026-05-04 | Regenerated anura.pot (+30 net strings) and synced 25 .po files | Image validation, clipboard timeout, URL security blocking strings added |
