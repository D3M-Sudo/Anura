# Technical Remediation Changelog - Anura OCR

## Phase 1: Infrastructural Improvements

### 1.1 Flatpak Dependency Management
- Added `psutil` (v7.2.2) to `flatpak/io.github.d3msudo.anura.json` and `flatpak/io.github.d3msudo.anura.local.json`.
- Verified `psutil` usage in `anura/utils/image_filters.py` for OOM prevention (Resource Guard).
- Note: Standard sandbox permissions allow access to necessary `/proc` information for memory monitoring.

### 1.2 Test Environment Integration
- Created `bin/run_gtk_tests.sh` helper script to execute GTK tests using `xvfb-run`.
- Added support for system `gi` (PyGObject) typelibs in the test environment.

## Phase 2: Code Modernization & Safety

### 2.1 Blind Exception Handling (BLE001)
- Refactored 15 instances of generic `except Exception:` blocks in `anura/controllers/` and `anura/core/`.
- Replaced with specific exception tuples: `(AttributeError, TypeError, RuntimeError, OSError, GLib.Error)`.
- Improved error logging and observability.

### 2.2 Pathlib Migration (PTH)
- Refactored `anura/utils/cleanup.py` to use `pathlib.Path` instead of `os.path`.
- Modernized filesystem operations for better readability and safety.

### 2.3 Type Annotation (ANN)
- Added comprehensive Type Annotations to `anura/controllers/ocr_controller.py` and `anura/window.py`.
- Improved static analysis coverage and code documentation.
- Integrated `TYPE_CHECKING` blocks for circular dependency management in hints.

## Phase 3: Linting & Style
- Fixed multiple Ruff linting warnings (SIM102, etc.).
- Standardized import sorting and formatting.
