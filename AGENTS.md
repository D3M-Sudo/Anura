# AGENTS.md — Anura OCR AI Assistant Guide

> Canonical AI-assistant guide for this repository. Also read by Claude Code, Cursor, Aider, Continue, and Zed via the AGENTS.md convention.

## Project Overview

Anura OCR is a GTK4/Libadwaita desktop application for GNOME that extracts text from screenshots, images, and clipboard using Tesseract OCR, with QR code support, text-to-speech, and social sharing. It is a fork of Frog OCR with complete telemetry removal.

**Key Facts:**

- Python 3.12+ required
- GTK4 + Libadwaita + Blueprint Compiler for declarative UI
- OCR via `pytesseract` (Tesseract 5.x wrapper)
- Barcode/QR code via `zxing-cpp` (replaces legacy `pyzbar`)
- TTS via `gTTS` + GStreamer `playbin3`
- Screenshots via XDG Desktop Portal (`libportal` / `Xdp`)
- **Fallback**: Bundled `scrot` for X11 sessions when portal backends are missing
- Distributed as Flatpak (`io.github.d3msudo.anura`) — GNOME 50 runtime
- Internationalization with gettext: 25+ languages (see `po/LINGUAS`)
- Build system: Meson ≥ 1.5.0
- License: MIT

## Repository Structure

```text
anura/
├── anura/                      Python application source
│   ├── main.py                 AnuraApplication (Adw.Application) + CLI + AboutDialog
│   ├── window.py               AnuraWindow — Core window management
│   ├── window_mixins/          Extracted Window logic (Naked mixins)
│   │   ├── ocr_mixin.py        OCR signal handling and processing
│   │   ├── tts_mixin.py        TTS lifecycle and audio management
│   │   └── dnd_mixin.py        Asynchronous Drag-and-Drop support
│   ├── config.py               Constants APP_ID, tessdata URL, lang_code validation
│   ├── atomic_task_manager.py  Single-slot thread pool with UUID versioning
│   ├── language_manager.py     Tessdata model download/management (singleton)
│   ├── services/
│   │   ├── screenshot_service.py   Screenshot capture via Xdp.Portal
│   │   ├── host_screenshot_fallback.py X11 fallback using bundled scrot
│   │   ├── clipboard_service.py    Clipboard read/write (Gdk.Clipboard)
│   │   ├── notification_service.py Notifications: XDG Portal → libnotify fallback
│   │   ├── tts.py                  Text-to-speech via gTTS + GStreamer
│   │   ├── share_service.py        Social sharing (9 providers)
│   │   └── settings.py             GSettings singleton wrapper
│   ├── types/
│   │   ├── download_state.py       DownloadState enum
│   │   └── language_item.py        LanguageItem dataclass
│   ├── utils/
│   │   ├── barcode_detector.py    QR/Barcode detection via zxing-cpp
│   │   ├── image_filters.py       Modular image enhancement filter chain
│   │   ├── structural_reconstructor.py Paragraph/Layout spatial analysis
│   │   ├── validators.py          URI validation & text sanitization
│   │   ├── portal_advice.py       Desktop-specific advice for missing portals
│   │   ├── text_preprocessor.py   Image enhancement & text cleanup factory
│   │   ├── singleton.py           Thread-safe lazy singleton pattern
│   │   ├── cleanup.py             Resource cleanup utilities
│   │   └── signal_manager.py      GLib signal management mixin
│   ├── widgets/
│   │   ├── extracted_page.py       OCR result page with share/TTS actions
│   │   ├── language_popover.py     Language selector with search
│   │   ├── language_popover_row.py Language row in popover
│   │   ├── language_row.py         Language row in preferences page
│   │   ├── preferences_dialog.py   Preferences dialog (Adw.PreferencesDialog)
│   │   ├── preferences_general_page.py   General preferences page
│   │   ├── preferences_languages_page.py Language management/download page
│   │   ├── share_row.py            Share provider row
│   │   ├── shortcuts_overlay.py    Keyboard shortcuts cheat sheet widget
│   │   └── welcome_page.py         Welcome page
├── data/
│   ├── ui/                     Blueprint files (.blp) → compiled to .ui
│   ├── icons/                  Scalable SVG icons + symbolic variants
│   ├── screenshots/            Screenshots for Flathub/metainfo
│   ├── io.github.d3msudo.anura.desktop.in
│   ├── io.github.d3msudo.anura.gresource.xml
│   ├── io.github.d3msudo.anura.gschema.xml
│   ├── io.github.d3msudo.anura.metainfo.xml.in
│   └── style.css
├── flatpak/
│   └── io.github.d3msudo.anura.json   Flatpak manifest with all dependencies
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
    gstreamer1.0-plugins-good gstreamer1.0-pulseaudio \
    libxml2-utils # Required for GResource compilation

# Python runtime and dev dependencies
uv sync --dev

# Build with Meson (local development)
uv run meson setup builddir
uv run meson compile -C builddir

# Run from source tree (without installing)
GSETTINGS_SCHEMA_DIR=builddir/data python3 -m anura.main
```

### Flatpak Build

```bash
# Full build
flatpak-builder --force-clean builddir flatpak/io.github.d3msudo.anura.json

# Run the build
flatpak-builder --run builddir flatpak/io.github.d3msudo.anura.json anura
```

## Dependency Management

Anura uses `uv` for Python development and native dependencies via Flatpak.

### Runtime Dependencies (Flatpak/System)

| Module | Version | Purpose |
|--------|---------|---------|
| tesseract | 5.5.0 | OCR engine |
| zxing-cpp | 2.3.0 | High-performance Barcode/QR decoding |
| libportal | 0.9.1 | XDG Desktop Portal API |
| blueprint-compiler | 0.16.0 | UI compilation .blp → .ui |

## Code Patterns & Conventions

### Thread Safety & Atomic Execution

**Rule:** Never modify GTK widgets from secondary threads. Use `AtomicTaskManager` for all background tasks.

```python
from anura.atomic_task_manager import get_atomic_manager

# Atomic execution with versioning (prevents race conditions)
get_atomic_manager().execute(
    self.decode_image,
    args=(lang, filename, copy),
    callback=self._on_success,
    errorback=self._on_error
)
```

`AtomicTaskManager` manages a single-worker `ThreadPoolExecutor` and uses UUIDs to discard results from stale/cancelled tasks.

### Signal Management Mixin

Classes should inherit from `SignalManagerMixin` and use `connect_tracked()` to ensure signals are automatically disconnected during `do_destroy()`.

### Text Sanitization

Always use `validators.sanitize_text` to strip Unicode Control/Format characters and prevent RTL spoofing or terminal injection.

### Logical Proposal Strategy

When proposing major architectural changes, provide a reference implementation in a new module (e.g., `anura/utils/new_feature.py`) before refactoring core classes. Use a dedicated branch (`feature/...`) for submission.

## Testing

### Test Architecture

- **Unit Tests** (`tests/test_gi_atomic_task_manager_unit.py`): Headless coverage for core logic.
- **Security Tests** (`tests/test_security_hardening.py`): Verification of DoS prevention and URI validation.
- **Integration Tests** (`tests/test_file_dialog_regressions.py`): Verification of GTK/Portal behavior.

### Running Tests

```bash
# Headless/Security tests
uv run pytest tests/ -v -m "not gtk"

# Full suite (requires GTK environment)
./setup-gschema.sh
./tests/setup_resources.sh
export GSETTINGS_SCHEMA_DIR="builddir"
uv run pytest tests/ -v
```

## Security Guidelines

1. **DoS Prevention**: Validate `MAX_IMAGE_SIZE_BYTES` before processing.
2. **Text Sanitization**: Strip Unicode Control (Cc) and Format (Cf) categories.
3. **URI Validation**: Use `uri_validator()` before any browser launch.
4. **No Telemetry**: Absolute privacy by design.

---
*For AI Agents: Read BEFORE operation. Follow Atomic Cancellation and Signal Management patterns strictly.*
