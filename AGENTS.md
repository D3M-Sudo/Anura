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
│   ├── main.py                 AnuraApplication (Adw.Application) + CLI + Capability Audit
│   ├── window.py               AnuraWindow — Core UI shell (Composition-based)
│   ├── controllers/            Business Logic Controllers
│   │   ├── ocr_controller.py   OCR coordination and signal handling
│   │   ├── tts_controller.py   TTS lifecycle and UI state management
│   │   └── dnd_controller.py   Asynchronous Drag-and-Drop coordination
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
│   │   ├── ocr.py                  Immutable OcrResult and OcrWord dataclasses
│   │   ├── context.py              ApplicationContext capability audit
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

### Controller Pattern (Composition)

**Rule:** `AnuraWindow` must remain a clean UI shell. All business logic and signal coordination must be moved to standalone controllers (e.g., `OcrController`).

#### Controller Lifecycle & GObject Signal Safety

**Tassative Directive:** Every controller must implement a `.cleanup()` method. This method MUST be connected to the `destroy` signal of the host widget/window (or explicitly called during its teardown). The cleanup logic is responsible for:
1.  Calling `self.disconnect_all_signals()` (if using `SignalManagerMixin`).
2.  Nullifying references to the host window (`self._window = None`) to break potential circular dependencies.
Failure to do so results in latent GObject memory leaks where the Python instance is kept alive by active signal connections in the native GLib layer.

### Memory Safety & Weak References

**Rule:** When connecting to long-lived native signals (e.g., GStreamer Bus), always use `weakref` closures to prevent reference cycles and ensure objects can be correctly finalized.

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

### Immutable Data Models

**Rule:** OCR recognized data should be encapsulated in immutable `frozen` dataclasses (`OcrResult`, `OcrWord`) to ensure data integrity across the transformation pipeline.

### Capability Audit (Feature Toggling)

**Rule:** Perform a boot-time system audit (`ApplicationContext`) to detect available binaries and libraries. Bind UI sensitivity to these capability flags to prevent runtime failures.

### Text Sanitization

Always use `validators.sanitize_text` to strip Unicode Control/Format characters and prevent RTL spoofing or terminal injection.

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
*For AI Agents: Read BEFORE operation. Follow Controller-Composition, Memory Safety, and Capability Audit patterns strictly.*
