# Design Spec: Navigable History of last N Captures

This document details the architectural design for implementing a navigable history of the last $N$ OCR captures within the Anura desktop application.

---

## 1. Objectives & Goals
* **Navigable Capture History:** Preserve the last $N$ successful text extractions instead of overwriting the UI state on every single capture.
* **Rich Metadata:** Save text content, timestamp, language, applied Smart Parse/transformer name, and a scaled PNG thumbnail of the captured region.
* **Privacy-by-Design:** Support toggling history storage via GSettings (`history-enabled`). When disabled, absolutely zero disk and memory writes occur.
* **Thread-Safe & Non-blocking I/O:** Run all file reads/writes on a separate thread using a single synchronization lock, preventing thread/lock races and GUI freezes.
* **High-Performance UI:** Implement an `Adw.NavigationPage` featuring GTK4's virtualized `Gtk.ListView` and `Gio.ListStore` for seamless scrolling through up to 200 high-resolution history list rows.

---

## 2. GSettings Configuration

We will add two new keys under the main schema `<schema id="io.github.d3msudo.anura">` inside `data/io.github.d3msudo.anura.gschema.xml`:

```xml
<key name="history-enabled" type="b">
  <default>true</default>
  <summary>Enable capture history</summary>
  <description>If true, successful OCR extractions will be saved locally.</description>
</key>
<key name="history-limit" type="i">
  <default>50</default>
  <range min="1" max="200"/>
  <summary>Capture history limit</summary>
  <description>The maximum number of recent captures to keep in history.</description>
</key>
```

---

## 3. Data Model: `CaptureSession`

To integrate perfectly with `Gio.ListStore` and `Gtk.ListView`, we will define a GObject subclass `CaptureSession` in `anura/models/capture_session.py`.

```python
import gi
gi.require_version("GObject", "2.0")
from gi.repository import GObject

class CaptureSession(GObject.GObject):
    """GObject wrapper for a single historic OCR capture session."""

    id = GObject.Property(type=str, default="")
    text = GObject.Property(type=str, default="")
    timestamp = GObject.Property(type=float, default=0.0)
    language = GObject.Property(type=str, default="")
    transformer_name = GObject.Property(type=str, default="")
    thumbnail_base64 = GObject.Property(type=str, default="")  # Base64-encoded PNG thumbnail

    def __init__(
        self,
        id: str = "",
        text: str = "",
        timestamp: float = 0.0,
        language: str = "",
        transformer_name: str = "",
        thumbnail_base64: str = "",
        **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self.set_property("id", id)
        self.set_property("text", text)
        self.set_property("timestamp", timestamp)
        self.set_property("language", language)
        self.set_property("transformer_name", transformer_name)
        self.set_property("thumbnail_base64", thumbnail_base64)

    def to_dict(self) -> dict:
        return {
            "id": self.props.id,
            "text": self.props.text,
            "timestamp": self.props.timestamp,
            "language": self.props.language,
            "transformer_name": self.props.transformer_name,
            "thumbnail_base64": self.props.thumbnail_base64,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CaptureSession":
        return cls(
            id=data.get("id", ""),
            text=data.get("text", ""),
            timestamp=data.get("timestamp", 0.0),
            language=data.get("language", ""),
            transformer_name=data.get("transformer_name", ""),
            thumbnail_base64=data.get("thumbnail_base64", ""),
        )
```

---

## 4. Business Logic & Storage: `HistoryService`

We will implement a thread-safe singleton `HistoryService` at `anura/services/history_service.py` to handle loading, saving, and managing historic entries.

### Key Thread Safety & Write Isolation Patterns
1. **Single Lock (`self._lock = threading.Lock()`)**: Both in-memory mutations and disk read/write operations must be serialized through this lock.
2. **Synchronized/Sequenced Write & Deletion Threads**: To avoid concurrent write races on the same file, any method starting a file save OR history clearance must join the previously spawned save/write thread first:
   ```python
   with self._lock:
       if self._write_thread and self._write_thread.is_alive():
           self._write_thread.join(timeout=1.5)  # Timeout prevents indefinite blocking on stalled I/O
       self._write_thread = threading.Thread(target=self._write_to_disk, args=(data_snapshot,))
       self._write_thread.start()
   ```
3. **`clear_history()` Safety**: `clear_history()` must follow the exact same thread-safety pattern. It will join the active `self._write_thread` (if alive) with a timeout of 1.5 seconds, and then assign its own file deletion thread to the same `self._write_thread` shared variable so that any subsequent capture calls (`add_session()`, etc.) correctly sequence and wait for the clearing operation to finish.
4. **Shutdown Coexistence**: A dedicated `.shutdown()` method will wait for the active writer thread to finish up to a 5.0-second timeout, ensuring zero corrupted or missing writes when the application exits. It is called inside `do_shutdown()` in `anura/main.py`.
5. **Error Recovery**: If the JSON history file is corrupted, the service logs the error, renames the corrupted file to `history.corrupt.<timestamp>.json`, and safe-degrades by loading a fresh empty state.

### `history-enabled` Behavior & Storage Policy
- **When `history-enabled` is `false`**:
  - `add_session()` will return immediately doing absolutely nothing (zero memory writes, zero disk writes).
  - Existing entries already on disk are **NOT** automatically deleted when toggling `history-enabled` off. They remain completely intact so that re-enabling the option seamlessly restores previous history.
  - `HistoryPage` remains accessible and still displays the existing entries even while `history-enabled` is false.
  - A warning banner is displayed at the top of the `HistoryPage` saying: `"History is disabled — new captures won't be saved."` (or translated equivalent).
  - The only way existing entries get deleted is via the explicit "Clear History" action, never as an implicit side-effect of a toggle.

---

## 5. UI Architecture: `HistoryPage`

We will add a new navigation page `HistoryPage` in `anura/widgets/history_page.py` and layout in `data/ui/history_page.blp`.

### Layout & Widgets
* Header bar containing:
  * A "Back" navigation button (on the left) to pop the navigation view.
  * A title ("Cronologia" / "History") centered.
  * A "Clear History" button (`trash-symbolic` icon) on the right.
* Warning Banner:
  * An `Adw.Banner` displayed beneath the header bar, revealed only when `history-enabled` is false, with the label: `_("History is disabled — new captures won't be saved.")`.
* Body:
  * A `Gtk.Stack` switching between:
    1. **Empty State**: An `Adw.StatusPage` showing "Nessuna cattura recente" (No recent captures) with a clock icon.
    2. **List State**: A `Gtk.ScrolledWindow` wrapping a `Gtk.ListView`.
* `Gtk.ListView` configuration:
  * **Factory**: `Gtk.SignalListItemFactory` connecting to `setup` and `bind`.
  * **Model**: `Gio.ListStore` populated directly with `CaptureSession` GObjects.
  * **Row Widget (`HistoryRow` / `HistoryPageRow`)**: A custom horizontal box layout with:
    * Left: A `Gtk.Picture` with `content-fit: contain` displaying the base64-decoded PNG thumbnail. This preserves the thumbnail's original rectangular aspect ratio without forcing a square/circular crop (which would distort screenshots of text). Thumbnail dimensions: scaled to 160px on its longest side.
    * Middle: A vertical box with:
      * Label: Snippet of extracted text (truncated, bold).
      * Label: Subtitle with formatted date & time.
    * Right: A small badge with the language code (e.g. `ENG`, `ITA`).
  * **Activation**: Clicking/activating a row populates `ExtractedPage.set_extracted_text(text, transformer_name)` and navigates the window to the `extracted` page.

---

## 6. Entry Points & Connections
1. **Welcome Page Headerbar / Primary Menu**:
   * Add a clock-icon button (`document-open-recent-symbolic`) on the header bar to pop up the history page.
   * Add a menu item "Recent Captures" inside the `primary_menu`.
2. **Extracted Page Primary Menu**:
   * Add a menu item "Recent Captures" inside the `primary_menu` of `extracted_page.blp` so users can jump to history from a current result.
3. **Preferences dialog integration**:
   * Add a "Clear History" button in the General preferences tab.

---

## 7. Quality Assurance & CI Strategy

### Plain Virtual Environment & `ANURA_CI_TEST_MODE`
`ANURA_CI_TEST_MODE` is a custom environment variable defined in Anura's own `tests/conftest.py` file.
- **Why it is set**: It is used in headless CI environments (where the real `gi` binding/GTK runtime is absent) to trigger module-level injection of a coherent `gi` mock hierarchy. This prevents class-definition crashes (such as `TypeError: metaclass conflict` during GObject subclassing resolution) during test collection.
- **When is it set**: The `python-quality` CI job on GitHub Actions explicitly sets `ANURA_CI_TEST_MODE: "1"` in its environment to enable this mock injection.
- **Plain Venv Behavior**: When running `uv run pytest tests/ -m "not gtk"` in a plain venv with no environment variables set, `ANURA_CI_TEST_MODE` is default/unset (`0`), meaning module-level mock injection is disabled. Test collection proceeds normally but fails on files referencing `OcrController` because `test_ocr_controller_ref.py` is loaded and triggers the test-level dynamic `headless_gi_mocks` fixture, which lacks module-scope alignment and results in a `TypeError: metaclass conflict`.

### Isolation of `tests/test_history_service.py`
To satisfy plain-venv execution and prevent any interference with other test jobs, our new test file `tests/test_history_service.py` will:
1. Not import `gi` at module level, avoiding any collection crashes.
2. Be fully covered by unit testing for its core logic (serialisation, limits, toggles, threads).
3. Be added to `--ignore` in `.github/workflows/main.yml` and `addopts` in `pyproject.toml` so it is synchronized with other system-mocked tests and only executed under appropriate environments.
