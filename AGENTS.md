# AGENTS.md — Anura OCR AI Assistant Guide

> Canonical AI-assistant guide for this repository. Also read by Claude Code, Cline, Cursor, Aider, Continue, and Zed via the AGENTS.md convention.

## Project Overview

Anura OCR is a GTK4/Libadwaita desktop application for GNOME that extracts text from screenshots, images, and clipboard using Tesseract OCR, with QR code support, text-to-speech, and social sharing. It is a fork of Frog OCR with complete telemetry removal.

**Key Facts:**

- Python 3.12+ required
- GTK4 + Libadwaita + Blueprint Compiler for declarative UI
- Text editor: GtkSourceView 5 (`GtkSource.View`/`GtkSource.Buffer`) with native search and external-editor handoff
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
│   ├── main.py                 AnuraApplication (Adw.Application) - Lightweight Orchestrator
│   ├── window.py               AnuraWindow — Core UI shell (Composition-based)
│   ├── config.py               Constants APP_ID, tessdata URL, lang_code validation
│   ├── core/                   Modular Core Services
│   │   ├── atomic_task_manager.py  Single-slot thread pool with UUID versioning
│   │   ├── boot.py             Hardware bootstrap, Capability Audit
│   │   ├── logger.py           Rotary Logging logic
│   │   ├── i18n.py             Hybrid C/Python/GLib Localization
│   │   ├── resources.py        Atomic GResource management
│   │   ├── action_registry.py  Centralized Action Factory
│   │   ├── dialogs.py          UI Dialog Orchestration (About, Preferences)
│   │   └── silent_runner.py    Isolated Headless Engine (CLI/Silent mode)
│   ├── controllers/            Business Logic Controllers
│   │   ├── ocr_controller.py   OCR coordination and signal handling
│   │   ├── tts_controller.py   TTS lifecycle and UI state management
│   │   └── dnd_controller.py   Asynchronous Drag-and-Drop coordination
│   ├── services/
│   │   ├── clipboard_service.py    Clipboard read/write (Gdk.Clipboard)
│   │   ├── language_manager.py     Tessdata coordination (singleton)
│   │   ├── language/               Specialized language managers
│   │   │   ├── cache_manager.py    Tessdata caching logic
│   │   │   ├── download_manager.py Tessdata download coordination
│   │   │   └── language_validator.py Language code validation
│   │   ├── notification_service.py Notifications: XDG Portal → libnotify fallback
│   │   ├── result_dispatcher.py    Post-OCR coordination (Clipboard, URLs, Notifications)
│   │   ├── screenshot/             Abstract Factory Screenshot providers
│   │   │   ├── base.py              Base provider interface
│   │   │   ├── factory.py           Provider factory
│   │   │   ├── legacy_provider.py   X11 scrot fallback provider
│   │   │   └── portal_provider.py   XDG Desktop Portal provider
│   │   ├── screenshot_service.py   Screenshot capture orchestration
│   │   ├── history_service.py      Opt-in local JSON history (History V1, see docs/reference/history-v1.md)
│   │   ├── settings.py             GSettings singleton wrapper
│   │   ├── share_service.py        Social sharing (9 providers)
│   │   ├── tts/                    Text-to-speech modular components
│   │   │   ├── audio_player.py     GStreamer audio playback
│   │   │   ├── language_mapper.py  Language code mapping for TTS
│   │   │   ├── pipeline_manager.py TTS pipeline orchestration
│   │   │   ├── service.py          TTSService facade
│   │   │   └── speech_generator.py gTTS speech generation
│   ├── models/
│   │   ├── context.py              ApplicationContext capability audit
│   │   ├── download_state.py       DownloadState enum
│   │   ├── history.py              Immutable HistoryEntry dataclass (History V1)
│   │   ├── language_item.py        LanguageItem dataclass
│   │   └── ocr.py                  Immutable OcrResult and OcrWord dataclasses
│   ├── transformers/          Semantic text transformers (Chain of Responsibility)
│   │   ├── base_transformers.py Base implementations (SingleLine, Paragraph, etc.)
│   │   ├── email_transformer.py Specialized email extraction & scoring
│   │   ├── magic_processor.py Orchestrator: Classification & semantic coordination
│   │   ├── models.py            Dataclasses and ITransformer Protocol
│   │   └── url_transformer.py   Specialized URL extraction & validation
│   ├── utils/
│   │   ├── barcode_detector.py    QR/Barcode detection via zxing-cpp
│   │   ├── cleanup.py             Resource cleanup utilities
│   │   ├── export_files.py        Hardened export files for external-editor handoff (F3)
│   │   ├── file_ready_retry.py    File readiness utility with retry logic
│   │   ├── image_filters.py       Modular image enhancement filter chain
│   │   ├── notification_helpers.py Notification formatting and validation helpers
│   │   ├── portal_advice.py       Desktop-specific advice for missing portals
│   │   ├── signal_manager.py      GLib signal management mixin
│   │   ├── singleton.py           Thread-safe lazy singleton pattern
│   │   ├── structural_reconstructor.py Paragraph/Layout spatial analysis
│   │   ├── tessdata_integrity.py  Git-blob SHA-1 verification of tessdata models (F1)
│   │   ├── text_preprocessor.py   Image enhancement & text cleanup factory
│   │   └── validators.py          URI validation, security & text sanitization
│   ├── widgets/
│   │   ├── extracted_page.py       OCR result page: GtkSourceView 5 editor (native search, external editor handoff) + share/TTS actions
│   │   ├── history_page.py         History V1 page (read-only list, clear action)
│   │   ├── language_popover.py     Language selector with search
│   │   ├── language_popover_row.py Language row in popover
│   │   ├── language_row.py         Language row in preferences page
│   │   ├── preferences_dialog.py   Preferences dialog (Adw.PreferencesDialog)
│   │   ├── preferences_general_page.py   General preferences page
│   │   ├── preferences_languages_page.py Language management/download page
│   │   ├── share_row.py            Share provider row
│   │   ├── shortcuts_overlay.py    Keyboard shortcuts cheat sheet widget
│   │   └── welcome_page.py         Welcome page
│   └── data/
│       └── tessdata_checksums.json Pinned git-blob SHA-1 manifest for runtime model integrity (see docs/reference/tessdata-integrity.md)
├── data/
│   ├── ui/                     Blueprint files (.blp) → compiled to .ui (incl. history_page.blp)
│   ├── icons/                  Scalable SVG icons + symbolic variants
│   ├── screenshots/            Screenshots for Flathub/metainfo
│   ├── io.github.d3msudo.anura.desktop.in
│   ├── io.github.d3msudo.anura.gresource.xml
│   ├── io.github.d3msudo.anura.gschema.xml   (incl. history-enabled/limit, editor-*, external-editor keys)
│   ├── io.github.d3msudo.anura.metainfo.xml.in
│   └── style.css
├── docs/
│   ├── README.md               Documentation index (normative / planning / audit)
│   ├── reference/              Current (normative) references:
│   │                            history-v1.md, dependencies.md, tessdata-integrity.md
│   ├── planning/               Active (not yet implemented) plans (recreated when needed)
│   └── audit/                  QA/security audit material:
│                                README.md (root = active audits) + legacy/ (append-only: reports/)
├── flatpak/
│   ├── io.github.d3msudo.anura.json         Release manifest — GENERATED by
│   │                                         release.sh from .local.json, never hand-edited
│   └── io.github.d3msudo.anura.local.json   Local manifest — the one to edit (anura module: dir source)
├── build-aux/
│   ├── release.sh              Release script (bump version, pin tessdata ref,
│   │                            generate release manifest from .local.json)
│   ├── generate_release_notes.py CHANGELOG.md parser → _release_notes.py
│   ├── generate_tessdata_checksums.py Tessdata integrity manifest (git-blob SHA-1) generator
│   ├── setup-gschema.sh        GSettings schema compilation for testing
│   ├── sync_dependencies.py    uv.lock → local Flatpak manifest python3-* sync (excl. certifi)
│   ├── check_manifest_consistency.py        Drift check: release vs local manifest (release-time self-check, see docs/reference/dependencies.md)
│   ├── check_runtime_dependency_coverage.py F-005: uv.lock runtime closure → manifest coverage (--manifest local in CI, --manifest both at release)
│   ├── check_tessdata_consistency.py        Tessdata ref: config.py vs both manifests (release-time self-check)
│   └── meson/postinstall.py    Post-install script
├── bin/
│   └── anura.in                Entry point script (installed as `anura`)
├── po/                         Gettext translations (25+ languages)
├── .github/
│   ├── workflows/
│   │   ├── main.yml                    CI build and smoke tests
│   │   ├── dependency-sync.yml         Dependabot PRs: pyproject → uv.lock → manifests
│   │   └── flatpak-dependencies.yml    Weekly FEDC + auto-PR certifi
│   ├── scripts/
│   │   └── fedc_certifi.py             Isolate/replace certifi source for FEDC updates
│   └── dependabot.yml                  Automatic pip and Actions updates (target: testing)
├── meson.build                 Main build (also generates _release_notes.py)
├── CHANGELOG.md                Versioned changelog (source for release notes)
├── docs/                       Documentation index + reference/ (normative) + planning/ (active) + audit/ (historical)
```

## Development Commands

### Environment Setup

```bash
# System dependencies (Ubuntu/Debian)
sudo apt install gettext python3-gi gir1.2-gtk-4.0 gir1.2-adw-1 \
    gir1.2-gtksource-5 blueprint-compiler libportal-gtk4-dev \
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
flatpak-builder --force-clean builddir flatpak/io.github.d3msudo.anura.local.json

# Run the build
flatpak-builder --run builddir flatpak/io.github.d3msudo.anura.local.json anura
```


## Release Process

> **AGENT REMINDER — the GitHub release body is NOT automated.**
> The CI auto-creates the GitHub release for every `v*` tag (the
> `flatpak-builder` job in `.github/workflows/main.yml` calls
> `softprops/action-gh-release` and attaches the Flatpak bundle) — but with
> an **EMPTY body**. Populating the release notes is a **mandatory manual
> step** every time a tag is created and pushed.

1. Run `./build-aux/release.sh <version>` (bumps version, pins tessdata,
   generates the release manifest) and push the tag.
2. Wait for the tag's CI run to complete (`gh run watch <run-id>`): the
   release is created only when the `flatpak-builder` job finishes.
3. Populate the release body — `CHANGELOG.md` is the single source of truth:
   ```bash
   { echo "## Anura v<version> — <YYYY-MM-DD>"; echo;
     awk 'BEGIN{p=0} /^## \[<version>\]/{p=1; next} /^## \[<prev-version>\]/{exit} p{print}' \
       CHANGELOG.md > /tmp/notes-<version>.md
     gh release edit v<version> --title "v<version>" \
       --notes-file /tmp/notes-<version>.md --latest
   ```
   - Header style: `## Anura vX.Y.Z — YYYY-MM-DD`; keep the date consistent
     with the CHANGELOG entry (both files are the reference for users).
   - Never leave the body empty and never invent notes that are not in the
     CHANGELOG; keep the `### Added / Fixed / Changed / Security / Removed`
     subsection structure as-is.
4. Final check: `gh release view v<version>` — asset
   `io.github.d3msudo.anura.flatpak` attached, notes complete, `Latest`
   flag on the new release.

## Dependency Management

Anura uses `uv` for Python development and native dependencies via Flatpak.

### Runtime Dependencies (Flatpak/System)

| Module | Version | Purpose |
|--------|---------|---------|
| tesseract | 5.3.4 | OCR engine |
| zxing-cpp | 3.0.0 | High-performance Barcode/QR decoding |
| leptonica | 1.87.0 | Image processing library |
| libportal | 0.9.1 | XDG Desktop Portal API |
| blueprint-compiler | 0.16.0 | UI compilation .blp → .ui |

### Build Dependencies (Flatpak)

These dependencies are required only at build time and are managed by FEDC
via `x-checker-data` metadata. They are NOT runtime dependencies and are NOT
present in `uv.lock`:

| Module | Purpose |
|--------|---------|
| pybind11 | Python bindings for zxing-cpp (build-time only) |
| scikit-build-core | Build system for zxing-cpp (build-time only) |

### Special Dependency Ownership

**certifi**: This package is a transitive dependency of `requests` and appears in
`uv.lock`. However, its Flatpak version is **NOT** managed by `sync_dependencies.py`.
Instead, it is owned exclusively by FEDC (flatpak-external-data-checker) via
`.github/workflows/flatpak-dependencies.yml`.

This means:
- `uv.lock` certifi version may differ from Flatpak manifest certifi version
- `sync_dependencies.py` intentionally excludes certifi from its mapping
- FEDC updates certifi in `io.github.d3msudo.anura.local.json` only — the
  release manifest inherits it automatically the next time `release.sh` runs
- This divergence is intentional and not a drift issue

## Agent Rules — ABSOLUTE

These rules are binding for every AI coding agent working on this repo
(Claude Code, Cline, Cursor, Aider, Continue, Zed). They were consolidated
here from `CLAUDE.md`, which is now a thin pointer to this file.

### Protected Files — NEVER MODIFY

- `po/*.po`
- `anura/_release_notes.py`
- `data/ui/*.ui` (generated from `.blp` files)
- `builddir/` (build artifacts)
- `CHANGELOG.md` (maintained via Keep a Changelog — add entries under `[Unreleased]`, never rewrite history)

### Lint & Dependencies

- **Linter**: **ruff** only — never flake8, pylint or black.
- **`uv` exclusive**: `uv add`, `uv sync`. Never `pip` or `poetry`.

### Internationalization (i18n)

- `_("text {var}").format(var=value)` — NEVER `_(f"...")`.
- `ngettext()` for plurals.
- After new UI strings → `cd po && ./update_potfiles.sh`.

### Error Handling — Early Return Pattern

- Guards and validations at the beginning. Happy path at the end.
- No generic `except Exception` that silences bugs.

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
from anura.core.atomic_task_manager import get_atomic_manager

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

### Capability Audit & Logging

**Rule:** Perform a boot-time system audit (`ApplicationContext`) via `anura.core.boot.boot_audit()` to detect available binaries and libraries.

**Logging Protocol:**
1.  **Standard Output**: For terminal visibility during development.
2.  **Offline Rotary Logs**: Secure local logs in `$XDG_STATE_HOME/anura/logs/`.
3.  **Constraints**: 5MB max size, 3-file retention, plain text (no compression).
4.  **Privacy**: Strictly zero-telemetry.

### Semantic Transformation Pipeline (MagicProcessor)

**Orchestration Pattern:** `MagicProcessor` acts as the central coordinator for semantic text transformation.

1.  **Input:** Receives `OcrResult` (Layout-aware immutable dataclass).
2.  **Scoring:** Iterates through registered transformers (`UrlTransformer`, `EmailTransformer`, `ParagraphTransformer`, etc.). Each transformer provides a `score()` based on the content's structural and semantic characteristics.
3.  **Classification:** Selects the transformer with the highest confidence score.
4.  **Transformation:** Invocates the `.transform()` method of the selected winner to produce specialized, cleaned, or restructured text.
5.  **Output:** Returns the final transformed text and calculated confidence.

### Text Sanitization

Always use `validators.sanitize_text` to strip Unicode Control/Format characters and prevent RTL spoofing or terminal injection. `TextPreprocessor` delegates all initial cleaning to this centralized security entry-point.

## Testing

### Test Architecture

- **Unit Tests** (headless tests): Coverage for core logic without GTK dependencies.
- **Security Tests** (`tests/test_security_hardening.py`): Verification of DoS prevention and URI validation.
- **Integration Tests** (`tests/test_file_dialog_regressions.py`): Verification of GTK/Portal behavior.
- **Enterprise/Audit Suite** (`tests/test_*_enterprise.py`, `tests/test_audit_*.py`): Advanced exhaustive coverage for all core services and reliability.

### Running Tests

Headless tests run with `uv run pytest tests/ -v -m "not gtk"`. GTK tests
need the system `python3-gi` via `PYTHONPATH` (PyGObject ships no wheels, so
it is NOT in the venv) — see `docs/reference/dependencies.md` "GTK (PyGObject) and the
development venv" section for the full pattern.

```bash
# Headless/Security tests
uv run pytest tests/ -v -m "not gtk"

# GTK integration tests (compiled schemas + GResource + system gi)
./build-aux/setup-gschema.sh
./tests/setup_resources.sh
SP=$(ls -d .venv/lib/python3.*/site-packages)
PYTHONPATH=".:$SP" GI_TYPELIB_PATH="/usr/lib/x86_64-linux-gnu/girepository-1.0:/usr/lib/girepository-1.0" \
  GSETTINGS_SCHEMA_DIR="builddir/data" /usr/bin/python3 -m pytest tests/ -v
```

History V1 tests: `tests/test_history_storage.py`,
`tests/test_history_controller_integration.py`, `tests/test_history_ui.py`
(headless), `tests/test_history_settings.py` (GTK-marked) and
`tests/test_preferences_page_resilience.py` (history/TTS wiring regression).
Shortcuts overlay consistency: `tests/test_shortcuts_consistency.py`.
Tessdata integrity: `tests/test_tessdata_checksums.py` (manifest lookup and
fail-closed semantics, headless) and `tests/test_tessdata_consistency.py`
(anti-drift checker, headless); download atomicity and digest verification:
`tests/test_language_download_integrity.py`.

## Security Guidelines

1. **DoS Prevention**: Validate `MAX_IMAGE_SIZE_BYTES` before processing.
2. **Text Sanitization**: Strip Unicode Control (Cc) and Format (Cf) categories.
3. **URI Validation**: Use `uri_validator()` before any browser launch.
4. **No Telemetry**: Absolute privacy by design.

---
*For AI Agents: Read BEFORE operation. Follow Controller-Composition, Memory Safety, and Capability Audit patterns strictly.*
