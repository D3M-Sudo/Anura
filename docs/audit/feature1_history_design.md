# Capture History Design - Feature 1

## Roles & Architecture
Anura uses a Controller-Composition model where `AnuraWindow` is a clean UI shell, and background work is handled by `AtomicTaskManager`. Privacy is central ("zero telemetry"), which means all data must remain local, secure, and completely clearable by the user.

### 1. Model: `CaptureSession`
A new immutable dataclass representation of a single capture stored in history:
```python
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True, slots=True)
class CaptureSession:
    id: str  # UUID
    timestamp: float  # Epoch timestamp
    text: str  # Extracted/processed text
    lang: str  # Language code used (e.g. 'eng')
    thumbnail: str | None = None  # Base64 encoded thumbnail image (optional, small size)
```
Located in `anura/models/history.py`.

### 2. Service: `HistoryService`
A thread-safe lazy singleton service in `anura/services/history_service.py`:
- Checks `history-enabled` key from `Gio.Settings` before saving.
- Reads/writes JSON files in `$XDG_STATE_HOME/anura/history/history.json`.
- Uses asynchronous non-blocking Gio I/O (`load_contents_async` / `replace_contents_async` or similar, or threading/executor under AtomicTaskManager) to avoid blocking the main UI thread.
- Implements `history-limit` configured via GSettings (default: 50). When appending, trims older entries if history exceeds the limit.
- Zero-telemetry: No cloud sync, completely local.
- Safety: If the JSON file is corrupted or malformed, it degrades safely by backing up/renaming the corrupted file (or logging and recreating an empty history) rather than crashing.
- Actions: Exposes `add_session(text, lang, thumbnail_bytes)`, `get_all_sessions()`, and `clear_history()`.

### 3. Settings additions
In `data/io.github.d3msudo.anura.gschema.xml`:
- `history-enabled` (boolean, default `true`)
- `history-limit` (integer, default `50`)

### 4. Post-OCR Integration
In `anura/controllers/ocr_controller.py`:
- In `_on_shot_done`, when text is successfully extracted, after notifying/dispatching, call `HistoryService.get_instance().add_session_async(text, lang)` (if `history-enabled` is true).

### 5. UI Integration
- A new menu item in the primary menu: "History" (`app.show_history` action).
- A new `HistoryPage` (`anura/widgets/history_page.py`, `data/ui/history_page.blp`) which is an `Adw.NavigationPage`.
- It displays a list of sessions using `Gtk.ListView` (or a `Gtk.ListBox` inside `Adw.PreferencesPage` or `Adw.ToolbarView` for simplicity/robustness, similar to current pages). Let's use `Gtk.ListBox` inside a scrollable view for simplicity and reliability.
- Each row represents a history item: text summary (first 80 characters), timestamp, language badge, and a thumbnail if present.
- Clicking a history item calls `extracted_page.set_extracted_text(session.text, f"History ({session.lang})")` and pushes the `extracted` page onto the navigation stack.
- Preferences dialog integration: add a "History" row or section in `PreferencesGeneralPage` with:
  - Switch for "Enable Capture History" (`history-enabled`).
  - SpinButton or dropdown for "History Limit" (`history-limit`).
  - Button to "Clear Capture History" which shows a confirmation dialog and then clears the history.

## Plan Validation Commands
1. Lint: `uv run ruff check .`
2. Headless tests: `uv run pytest tests/ -v -m "not gtk"`
3. Full GTK tests: `./setup-gschema.sh`, `./tests/setup_resources.sh`, and `GSETTINGS_SCHEMA_DIR="builddir" uv run pytest tests/ -v`
4. Clean Meson build and compile: `uv run meson setup builddir --wipe` and `uv run meson compile -C builddir`
5. Smoke test application startup: `GSETTINGS_SCHEMA_DIR=builddir/data python3 -m anura.main --help`
