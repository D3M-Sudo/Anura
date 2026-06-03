---
trigger: on_dead_code
---

# Anura OCR Dead Code Finder

When the user asks to "find dead code", "find unused code", "audit dead code", "find unused imports", "find unused exports", "remove dead code", "clean up unused code", or runs the `/dead-code` command, run the **dead-code-find** analysis. Use the scope the user specified (current file, folder, or workspace); default to current file. Report findings first; only apply removals if the user explicitly asked to remove or fix.

## Triggers

- "find dead code"
- "find unused code" 
- "audit dead code"
- "find unused imports"
- "find unused exports"
- "remove dead code"
- "clean up unused code"
- `/dead-code` command

## Analysis Scope

**Default:** Current file
**Options:** Single file, folder, or entire workspace

## Dead Code Patterns for Anura OCR

### Python Imports
- Unused `import` statements
- Unused `from ... import ...` statements
- Star imports that aren't used
- TYPE_CHECKING imports with actual runtime usage

### GTK4/Libadwaita Specific
- Unused widget imports
- Unused signal handlers
- Dead Blueprint (.blp) references
- Unused GSettings keys
- Unused GObject properties

### Functions and Methods
- Unused functions/methods
- Unused class methods
- Unused static methods
- Overridden methods that don't use super()
- Unused signal callbacks

### Classes and Data Structures
- Unused classes
- Unused dataclass fields
- Unused Enum values
- Unused TypedDict keys

### Anura-Specific Patterns
- Unused language codes in language_manager.py
- Unused share providers in share_service.py
- Unused Tesseract language models
- Unused notification service methods
- Unused clipboard service operations
- Unused TTS service methods

### Configuration and Build
- Unused Meson build targets
- Unused Flatpak dependencies
- Unused entries in .gresource.xml
- Unused desktop file categories

## Analysis Process

1. **Static Analysis** - Use ruff to find unused imports and variables
2. **GTK4 Analysis** - Check for unused widget references and signal handlers
3. **Blueprint Analysis** - Cross-reference .blp files with Python code
4. **Settings Analysis** - Check GSettings usage against schema
5. **Test Coverage** - Identify code not covered by tests
6. **Import Analysis** - Find circular imports and unused TYPE_CHECKING blocks

## Reporting Format

```
## Dead Code Analysis Results

### Unused Imports (X found)
- `anura.widgets.unused_widget` in `anura/window.py:15`
- `gi.repository.Gtk unused_import` in `anura/services/clipboard.py:8`

### Unused Functions (X found)  
- `unused_method()` in `anura/services/tts.py:42-45`
- `dead_callback()` in `anura/widgets/extracted_page.py:123-125`

### Unused Classes (X found)
- `UnusedClass` in `anura/types/dead_type.py:10-15`

### GTK4 Specific (X found)
- Unused signal handler `on_dead_signal` in `anura/window.py:200`
- Unused widget reference `dead_button` in `data/ui/dead.ui:25`

### Anura Services (X found)
- Unused share provider `dead_service` in `anura/services/share_service.py:80`
```

## Removal Guidelines

**Only remove when explicitly requested:**
- User says "remove dead code"
- User says "fix dead code" 
- User says "clean up unused code"
- User confirms removal after report

**Safe to remove:**
- Unused imports (ruff can auto-fix)
- Unused functions with no references
- Unused classes with no inheritance
- Unused variables
- Dead signal handlers

**Require confirmation:**
- Functions that might be used via reflection
- Classes that might be subclassed externally
- GSettings keys that might be used by external tools
- Exported functions in __init__.py

## Anura-Specific Considerations

- **Never remove** entries from `po/*.po` files
- **Never remove** core GSettings keys from schema
- **Check Flatpak manifest** before removing dependencies
- **Verify Blueprint files** before removing widget references
- **Test language codes** before removing from language_manager
- **Check service registrations** before removing service methods

## Tools Used

- `ruff check --select F401,F841` - Unused imports/variables
- `grep -r` - Cross-reference analysis
- Manual GTK4/Blueprint inspection
- GSettings schema validation

---
Generated for Anura OCR — GTK4/Libadwaita + Python + Meson + Flatpak
