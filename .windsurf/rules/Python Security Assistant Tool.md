---
trigger: always_on
---

# Python Security Assistant Tool

## Key Principles

- Write concise, technical responses with accurate Python examples
- Use functional, declarative programming; avoid classes where possible
- Prefer iteration and modularization over code duplication
- Use descriptive variable names with auxiliary verbs (e.g., `is_encrypted`, `has_valid_signature`)
- Use lowercase with underscores for directories and files (e.g., `utils/validators.py`)
- Favor named exports for commands and utility functions
- Follow the Receive an Object, Return an Object (RORO) pattern for all tool interfaces

## Python/GTK4 Security

- Use `def` for pure, CPU-bound routines; `async def` for network- or I/O-bound operations
- Add type hints for all function signatures; validate inputs with Pydantic v2 models where structured config is required
- Organize file structure into modules:
    - `services/` (clipboard, screenshot, notification, tts, share)
    - `widgets/` (extracted_page, language_popover, preferences)
    - `utils/` (validators, cleanup, signal_manager)
    - `types/` (download_state, language_item)

## Error Handling and Validation

- Perform error and edge-case checks at the top of each function (guard clauses)
- Use early returns for invalid inputs (e.g., malformed URIs, invalid language codes)
- Log errors with structured context (module, function, parameters)
- Raise custom exceptions (e.g., `TimeoutError`, `InvalidURLError`) and map them to user-friendly notifications
- Avoid nested conditionals; keep the "happy path" last in the function body

## Dependencies

- `cryptography` for symmetric/asymmetric operations (if needed)
- `Pillow` for image processing and validation
- `pytesseract` for OCR operations
- `pyzbar` for QR code processing
- `requests` for HTTP operations (tessdata downloads)
- `gi.repository.Gtk` and `gi.repository.Adw` for UI
- `gi.repository.GLib` for main loop and threading
- `gi.repository.Gio` for file operations and settings

## Security-Specific Guidelines

- Sanitize all external inputs; never invoke shell commands with unsanitized strings
- Use secure defaults (e.g., TLSv1.2+, strong cipher suites for network operations)
- Implement rate-limiting and back-off for network operations to avoid abuse
- Ensure secrets (API keys, credentials) are loaded from secure stores or environment variables
- Provide both CLI and GUI interfaces using the RORO pattern for tool control
- Use decorators for centralized logging, metrics, and exception handling

## URI and Input Validation

- Always validate URIs before opening or displaying to user
- Use `uri_validator()` function in `utils/validators.py` for comprehensive validation
- Validate language codes using `LANG_CODE_PATTERN` in `config.py`
- Sanitize file paths and prevent directory traversal attacks
- Validate image formats before processing with Pillow

## Thread Safety and Concurrency

- Never emit GObject signals or modify GTK widgets from secondary threads
- Always use `GLib.idle_add()` to schedule UI operations from the main thread
- Implement proper cancellation patterns with `Gio.Cancellable`
- Use atomic operations for shared state between threads
- Implement `__slots__` for memory efficiency in service classes

## Performance Optimization

- Utilize asyncio and connection pooling for high-throughput operations
- Batch or chunk large file lists to manage resource utilization
- Cache language model downloads and validation results when appropriate
- Lazy-load heavy modules (e.g., Tesseract language models) only when needed
- Use `functools.lru_cache` for expensive computations

## Key Conventions

1. Rely on dependency injection for shared resources (e.g., clipboard service, settings)
2. Prioritize measurable security metrics (processing time, error rates)
3. Avoid blocking operations in core processing loops; extract heavy I/O to dedicated async helpers
4. Use structured logging (JSON) for easy ingestion by SIEMs
5. Automate testing of edge cases with pytest and `pytest-asyncio`, mocking network layers

## Flatpak Security Considerations

- Operate within Flatpak sandbox limitations
- Use XDG Desktop Portal for system interactions (screenshots, notifications)
- Assume limited filesystem access (primarily `xdg-download`)
- Validate all file operations within sandbox constraints
- Never assume system dependencies beyond those specified in Flatpak manifest

## Data Protection and Privacy

- Process all data locally within the sandbox
- Never transmit user data to external services without explicit consent
- Implement proper cleanup of temporary files and resources
- Use atomic file operations to prevent data corruption
- Validate all user-provided content before processing

## Network Security

- Validate all TLS certificates for network operations
- Implement proper timeout handling for network requests
- Use secure defaults for HTTP operations (TLS, user agents)
- Sanitize URLs before making HTTP requests
- Implement proper error handling for network failures

## Key Security Patterns

### Input Validation Pattern
```python
from anura.utils.validators import uri_validator
from anura.config import LANG_CODE_PATTERN

def process_user_input(url: str, lang_code: str) -> bool:
    # Guard clauses for validation
    if not uri_validator(url):
        raise InvalidURLError(f"Invalid URI: {url}")
    
    if not re.match(LANG_CODE_PATTERN, lang_code):
        raise ValueError(f"Invalid language code: {lang_code}")
    
    # Happy path
    return True
```

### Thread Safety Pattern
```python
def background_operation(self):
    result = heavy_computation()
    # Always use GLib.idle_add() for UI updates
    GLib.idle_add(self.emit, "operation-complete", result)
```

### Atomic File Operations Pattern
```python
import tempfile
import shutil

def atomic_write(data: bytes, filepath: str) -> None:
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(data)
        tmp.flush()
        shutil.move(tmp.name, filepath)
```

## Testing Security

- Test all validation functions with malicious inputs
- Verify thread safety under concurrent operations
- Test error handling with network failures and timeouts
- Validate file operations within Flatpak sandbox constraints
- Use property-based testing for validation functions

---
Generated for Anura OCR — GTK4/Libadwaita + Python + Meson + Flatpak
