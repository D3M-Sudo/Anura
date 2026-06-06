# Anura Audit Legacy Insights

## Recurring Bug Patterns
- **P-TYPE-ANNOTATION**: PIL `ImageFile` vs `Image.Image` mismatches due to subclassing and reassignment in preprocessing pipelines.
- **P-NULL-SAFETY / P-MISSING-NONE-GUARD**: Missing `None` guards in error handling paths or when passing optional values to functions expecting non-None types.
- **P-RESOURCE-LEAK**: Potential for orphan worker processes in `ProcessPoolExecutor` or unclosed intermediate PIL images in filter chains.
- **P-IMPORT-INCOMPLETE**: Usage of package submodules (e.g. `importlib.util`) without explicit submodule imports.
- **P-REDUNDANT-SIGNAL-CONNECT**: Duplicate signal connections (e.g. `error-occurred`) in multiple architectural layers (Application vs Window).

## Previously Fixed Bugs (Historical Log)
- **BUG-1 (TTS Icon)**: Fix for pause/resume icon not updating. (Severity: MEDIUM, `extracted_page.py`)
- **BUG-2 (DnD Failure)**: Resolved immediate cancellation of isolated tasks in worker processes. (Severity: HIGH, `atomic_task_manager.py`)
- **BUG-3a (Notification Race)**: Fixed timing race between `present()` and error signal emission. (Severity: MEDIUM, `ocr_controller.py`)
- **BUG-3b (Flatpak Permissions)**: Added `org.freedesktop.Notifications` to manifest. (Severity: HIGH, `io.github.d3msudo.anura.json`)
- **BUG-4B (Screenshot Timeout)**: Fixed interference between portal timeout and `scrot` fallback. (Severity: MEDIUM, `window.py`)
- **BUG-5 (Log Level)**: Changed cancelled task logging from ERROR to silent propagation. (Severity: LOW, `image_filters.py`)
- **BUG-6 (Clipboard Warnings)**: Defensive check for source existence before removal. (Severity: LOW, `clipboard_service.py`)
- **NEW-007 (Pooling Race)**: Task-isolated Tesseract pools to prevent race conditions. (Severity: HIGH, `language_manager.py`)
- **NEW-011 (IDN Validation)**: Refined homograph defense to allow safe Latin-1 characters. (Severity: MEDIUM, `validators.py`)
- **NEW-016 (Scrot Race)**: Increased polling duration for slow filesystems. (Severity: MEDIUM, `legacy_provider.py`)

## Systemic Observations
- **Enterprise Clean Architecture**: Decoupling of View and Controller layers via GLib signals is robust but requires discipline to avoid duplicate listeners.
- **Task Isolation**: Multi-process OCR must use UUID-based sandboxed directories for any shared assets (like Tessdata) to remain race-free.
- **GObject Lifecycle**: Always use `SignalManagerMixin` and `connect_tracked` to prevent memory leaks from stale signal handlers.
- **Flatpak sandbox constraints**: Fallback tools (`scrot`) require explicit environment variable forwarding (DISPLAY, XAUTHORITY) to function inside the sandbox.

## Tool Findings History
- **Mypy**: Historically generates many false positives for `gi.repository` namespaces; requires custom filtering or stubs.
- **Vulture**: Accurate for finding dead code in specialized logic, but needs careful configuration to ignore GObject virtual methods (`do_*`) and template callbacks.
- **Safety**: Regularly identifies vulnerabilities in development dependencies (like `pip`); requires periodic supply chain audits.
- **Radon**: Most core modules maintain Rank A complexity, but `main.py` and `window.py` tend towards lower maintainability scores due to coordination logic.
