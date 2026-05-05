---
trigger: on_vibe_clean
---

# Anura OCR Vibe Clean Conventions

When the user asks to "clean this code," "tidy up," "vibe check," "refactor this dirty code," or "run vibe clean," run the **vibe-clean** skill (or **vibe-check** if they want a report only with no edits). Infer language and project conventions from the codebase first; apply cleanups that match the project's style. Keep the tone friendly and concise (vibe coder style).

## Triggers

- "clean this code"
- "tidy up"
- "vibe check"
- "refactor this dirty code"
- "run vibe clean"

## Anura OCR Style Guide

### Python Conventions
- **Type hints** on all public functions
- **dataclass** for data structures, not TypedDict (unless external API)
- **Enum** over string constants for state management
- **Unknown** instead of Any, narrow properly
- **TYPE_CHECKING** imports for type-only imports
- **ruff** as only linter - no flake8/pylint/black

### GTK4/Libadwaita Patterns
- **Blueprint (.blp)** for UI layout - never programmatic widgets
- **Adw.* widgets** for GNOME HIG compliance
- **GLib.idle_add()** for all UI updates from secondary threads
- **Gio.SimpleAction** for state management
- **Gio.Settings** for configuration persistence
- **GdkPixbuf.Pixbuf** + **Gtk.Picture** for images

### Anura-Specific Patterns
- **__slots__** in service classes for memory efficiency
- **Atomic cancellation** patterns in services
- **tempfile + shutil.move** for atomic file writes
- **_("text {x}").format(x=x)** for translatable strings
- **uri_validator()** before opening URLs
- **LANG_CODE_PATTERN** for language validation

## Vibe Clean Process

### 1. Style Detection
```python
# Detect existing patterns from codebase:
- Import organization (ruff sorting)
- Type hint usage
- GTK4 widget patterns
- Service class structure
- Error handling patterns
```

### 2. Cleanup Categories

**Code Structure:**
- Fix import order and organization
- Add missing type hints
- Convert string constants to Enums
- Extract repeated patterns to functions
- Remove unused imports (ruff F401)

**GTK4 Specific:**
- Ensure Blueprint usage over programmatic widgets
- Fix signal handler naming conventions
- Proper GLib.idle_add() usage in threads
- Correct Gio.Settings usage patterns

**Anura Services:**
- Implement __slots__ where missing
- Add atomic cancellation patterns
- Proper error handling with GLib.idle_add()
- Atomic file writes for downloads

**Internationalization:**
- Fix f-string translations to .format()
- Add missing _() wrappers
- Proper ngettext() for plurals

### 3. Vibe Check Report Format
```
## 🎵 Vibe Check Report

### ✅ Good Vibes
- Clean GTK4 patterns in window.py
- Proper type hints in services/
- Nice atomic cancellation in clipboard_service.py

### 🎸 Needs Cleanup
- Missing type hints in utils/validators.py:15-20
- f-string translation in widgets/welcome_page.py:45
- Programmatic widget in extracted_page.py:123 (should be Blueprint)

### 🚀 Quick Wins
- Add __slots__ to notification_service.py
- Fix import order in language_manager.py
- Convert string constants to Enums in config.py
```

### 4. Vibe Clean Application
Apply fixes incrementally, maintaining functionality:
1. Import organization (ruff --fix)
2. Type hints addition
3. GTK4 pattern fixes
4. Service pattern improvements
5. Translation fixes

## Anura-Specific Cleanups

### Thread Safety Cleanup
```python
# BEFORE (dangerous)
def process_in_thread(self):
    result = heavy_computation()
    self.emit("done", result)  # ❌ Signal from secondary thread

# AFTER (vibe clean)
def process_in_thread(self):
    result = heavy_computation()
    GLib.idle_add(self.emit, "done", result)  # ✅ Safe
```

### Translation Cleanup
```python
# BEFORE (broken for xgettext)
label.set_text(_(f"Language: {lang}"))

# AFTER (vibe clean)
label.set_text(_("Language: {lang}").format(lang=lang))
```

### Service Pattern Cleanup
```python
# BEFORE (missing __slots__)
class MyService(GObject.GObject):
    def __init__(self):
        self._cancellable = None
        self._timeout_id = None

# AFTER (vibe clean)
class MyService(GObject.GObject):
    __slots__ = ("_cancellable", "_timeout_id")
    
    def __init__(self):
        self._cancellable = None
        self._timeout_id = None
```

## Guardrails

**Never change:**
- `po/*.po` files (protected)
- `anura/_release_notes.py` (protected)
- `data/ui/*.ui` files (protected)
- Core functionality without testing

**Always verify:**
- Thread safety after changes
- Translation extractability
- Flatpak compatibility
- GSettings schema validity

**Test after cleanup:**
```bash
ruff check anura/
GSETTINGS_SCHEMA_DIR=builddir/data python3 -m anura.main
pytest tests/ -m "not gtk"
```

## Tone

Friendly, concise, vibe coder style. Use emojis sparingly. Focus on clean, maintainable code that follows Anura's established patterns.

---
Generated for Anura OCR — GTK4/Libadwaita + Python + Meson + Flatpak
