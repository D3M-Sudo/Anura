# Python Security Assistant Tool

## Goal
Assist in identifying and fixing security vulnerabilities in Anura's Python codebase.

## Key Security Domains

### 1. OCR & Input Validation
- Validate `lang_code` with `LANG_CODE_PATTERN` before Tesseract hand-off.
- Use `validators.sanitize_text` to strip Unicode Control/Format characters from OCR output.
- Enforce `MAX_IMAGE_SIZE_BYTES` in `ScreenshotService` to prevent memory-based DoS.

### 2. URI & URL Safety
- Always use `uri_validator()` before launching any URL via `Gtk.UriLauncher`.
- Prevent homograph attacks and RTL spoofing in shared links.

### 3. Concurrency & Race Conditions
- Use `AtomicTaskManager` for all background tasks to ensure atomic execution.
- Leverage UUID task versioning to discard stale results.
- Automated signal cleanup via `SignalManagerMixin`.

### 4. Sandbox Integrity
- Respect Flatpak sandbox boundaries.
- No direct filesystem access outside of `xdg-download` or portal-provided URIs.
- Use `libportal` for all screenshot and notification operations.

### 5. Dependency Security
- Use `zxing-cpp` for robust barcode processing.
- Maintain pinned versions in Flatpak manifest.
