---
trigger: always_on
---

# Anura OCR — Coding Rules

## Protected files — NEVER modify
- po/*.po
- anura/_release_notes.py  
- data/ui/*.ui
- CHANGELOG.md
- release.sh

## Code rules
- Linter: ruff only — never suggest flake8, pylint or black
- No subprocess — use GLib/GIO instead
- No GObject signals from secondary threads — use GLib.idle_add()
- No new Flatpak dependencies without asking first
- All user-facing strings: _("text {x}").format(x=x) — never _( f"..." )
- File writes: tempfile + shutil.move (atomic)
- Type hints required on all public functions
- After any new UI string → remind user to run ./generate_pot.sh

## Tests
- Framework: pytest, lives in tests/ (root)
- Run: uv run pytest tests/ -m "not gtk" (pure Python tests)
- Run with GTK: uv run env PYTHONPATH="/usr/lib/python3/dist-packages:$PYTHONPATH" GI_TYPELIB_PATH="/usr/lib/x86_64-linux-gnu/girepository-1.0:/usr/lib/girepository-1.0" pytest tests/ -v
- conftest.py must exist before other test files
- Install dependencies: uv sync --dev