# 🚨 PRIORITY - READ FIRST FOR CONTEXT

## IMPORTANT: Always Read Project Documentation Before Any Action

**This file must be read first by any Cascade/Claude/AI agent instance before any code operations.**

### Required Reading Order (for context):

1. **`README.md`** - Project overview, features, installation, basic testing
2. **`CONTRIBUTING.md`** - Development setup, testing procedures, code quality
3. **`AGENTS.md`** - AI agent guide, architecture, security patterns, testing
4. **`.windsurf/rules/testing.md`** - Testing environment setup, troubleshooting
5. **`.windsurf/rules/`** - All other rule files for specific patterns

### Critical Context Information:

**Project**: Anura OCR - GTK4/Libadwaita desktop application
**Tech Stack**: Python 3.11+, GTK4, Meson, Flatpak, Tesseract OCR
**Testing**: Two-tier system (pure Python + GTK-dependent)
**Security**: Privacy-first, local processing only

### Key Setup Requirements:

```bash
# GSchema setup (required for GTK tests)
./setup-gschema.sh

# Environment for GTK tests
export GSETTINGS_SCHEMA_DIR="builddir"
uv run env PYTHONPATH="/usr/lib/python3/dist-packages:$PYTHONPATH" GI_TYPELIB_PATH="/usr/lib/x86_64-linux-gnu/girepository-1.0:/usr/lib/girepository-1.0" GSETTINGS_SCHEMA_DIR="builddir" pytest tests/ -v
```

### Architecture Patterns:

- **Thread Safety**: Never emit GObject signals from secondary threads - use `GLib.idle_add()`
- **Security**: Validate all inputs with `LANG_CODE_PATTERN` and `uri_validator()`
- **Testing**: Pure Python tests with `pytest tests/ -m "not gtk"`
- **GTK Tests**: Require system environment setup as above

### Files You Must NOT Edit:
- `po/*.po` - Translation files
- `anura/_release_notes.py` - Generated at build time
- `data/ui/*.ui` - Compiled from .blp files
- `CHANGELOG.md` - Manual changelog entries only

### Before Any Code Changes:
1. Read the relevant documentation files above
2. Check existing patterns in the codebase
3. Follow security and thread safety guidelines
4. Run appropriate tests after changes

### For Testing Issues:
- Check `.windsurf/rules/testing.md` for troubleshooting
- Use `./setup-gschema.sh` for GSchema setup
- Run pure Python tests first: `pytest tests/ -m "not gtk"`
- Then run GTK tests with full environment

---

**⚠️ FAILURE TO READ THIS DOCUMENTATION FIRST WILL RESULT IN CONTEXT ERRORS, BROKEN CODE, AND SECURITY VIOLATIONS.**

**ALWAYS START BY READING THE PROJECT DOCUMENTATION FOR PROPER CONTEXT.**
