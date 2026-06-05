# AGENTS.md - Velis Development Guide

## Project Identity
- **App ID**: `io.github.d3msudo.velis`
- **Name**: Velis
- **Stack**: Python 3.12+, GTK4, Libadwaita, Meson, Blueprint

## Key Patterns

### Signal Management
Always use `SignalManagerMixin` for widgets and controllers. Connect to signals using `self.connect_tracked(emitter, "signal", callback)` to ensure automatic cleanup during destruction.

### Thread Safety
Use `AtomicTaskManager` for background tasks. Never update the UI from a background thread; use `GLib.idle_add`.

### Privacy
- All OCR is performed locally.
- History is stored locally in `$XDG_DATA_HOME/velis/history.db`.
- Translation uses user-configured LibreTranslate endpoints.

## Directory Layout
- `velis/`: Python source code
- `data/ui/`: Blueprint templates
- `data/icons/`: Scalable and symbolic icons
- `po/`: Translations
