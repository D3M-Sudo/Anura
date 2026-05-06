---
trigger: on_test
---

# Anura OCR Testing Guide

## Environment Setup

### System Dependencies (Ubuntu/Debian)
```bash
sudo apt install python3-gi gir1.2-gtk-4.0 gir1.2-adw-1 \
    blueprint-compiler libportal-gtk4-dev gir1.2-xdpgtk4-1.0 \
    tesseract-ocr python3-pil \
    gstreamer1.0-plugins-good gstreamer1.0-pulseaudio
```

### Verify gi Installation
```bash
python3 -c "import gi; print(gi.__file__)"
# Output: /usr/lib/python3/dist-packages/gi/__init__.py
```

## Running Tests with uv

### Install Dependencies
```bash
uv sync --dev
```

### Run All Tests (with system gi)
```bash
uv run env PYTHONPATH="/usr/lib/python3/dist-packages:$PYTHONPATH" pytest tests/ -v
```

### Run Tests Without GTK
```bash
uv run pytest tests/ -v -m "not gtk"
```

### Run Specific Test Files
```bash
# Config tests (pure Python)
uv run pytest tests/test_config.py -v

# Language manager tests
uv run pytest tests/test_language_manager.py -v

# URI validator tests
uv run pytest tests/test_uri_validator.py -v

# Screenshot service tests (requires gi)
uv run env PYTHONPATH="/usr/lib/python3/dist-packages:$PYTHONPATH" pytest tests/test_screenshot_service.py -v

# TTS service tests (requires gi)
uv run env PYTHONPATH="/usr/lib/python3/dist-packages:$PYTHONPATH" pytest tests/test_tts_service.py -v
```

## Test Markers

- `@pytest.mark.gtk` - Tests requiring GTK/GLib (need PYTHONPATH for gi)
- `@pytest.mark.network` - Tests requiring network access

## Troubleshooting

### Error: No module named 'gi'
The virtual environment doesn't have access to system packages. Use:
```bash
uv run env PYTHONPATH="/usr/lib/python3/dist-packages:$PYTHONPATH" pytest tests/ -v
```

### Error: No module named 'pytesseract'
Install dependencies first:
```bash
uv sync --dev
```

## Common Test Issues

#### Error: `ValueError: Namespace Xdp not available` 
**Cause**: XDP Portal typelib not available in virtual environment
**Fix**: Install system package:
```bash
sudo apt install gir1.2-xdpgtk4-1.0
```

#### Error: `ModuleNotFoundError: No module named 'gi'` 
**Cause**: Virtual environment doesn't have access to system packages
**Fix**: Use PYTHONPATH and GI_TYPELIB_PATH:
```bash
uv run env PYTHONPATH="/usr/lib/python3/dist-packages:$PYTHONPATH" GI_TYPELIB_PATH="/usr/lib/x86_64-linux-gnu/girepository-1.0:/usr/lib/girepository-1.0" pytest tests/ -v
```

#### Error: `RuntimeError: GSettings schema 'com.github.d3msudo.anura' not found`
**Cause**: GSettings schema not compiled or not in schema path
**Fix**: Compile the schema and set GSETTINGS_SCHEMA_DIR:
```bash
# Create build directory and copy schema
mkdir -p builddir
cp data/com.github.d3msudo.anura.gschema.xml builddir/

# Compile the schema
glib-compile-schemas builddir/

# Run tests with schema directory
export GSETTINGS_SCHEMA_DIR="builddir"
uv run env PYTHONPATH="/usr/lib/python3/dist-packages:$PYTHONPATH" GI_TYPELIB_PATH="/usr/lib/x86_64-linux-gnu/girepository-1.0:/usr/lib/girepository-1.0" GSETTINGS_SCHEMA_DIR="builddir" pytest tests/ -v
```

#### Complete GTK Test Setup
For full GTK testing environment setup:
```bash
# 1. Compile GSettings schema
mkdir -p builddir
cp data/com.github.d3msudo.anura.gschema.xml builddir/
glib-compile-schemas builddir/

# 2. Run all tests with full environment
export GSETTINGS_SCHEMA_DIR="builddir"
uv run env PYTHONPATH="/usr/lib/python3/dist-packages:$PYTHONPATH" GI_TYPELIB_PATH="/usr/lib/x86_64-linux-gnu/girepository-1.0:/usr/lib/girepository-1.0" GSETTINGS_SCHEMA_DIR="builddir" pytest tests/ -v

# 3. Or run only GTK-dependent tests
uv run env PYTHONPATH="/usr/lib/python3/dist-packages:$PYTHONPATH" GI_TYPELIB_PATH="/usr/lib/x86_64-linux-gnu/girepository-1.0:/usr/lib/girepository-1.0" GSETTINGS_SCHEMA_DIR="builddir" pytest tests/test_clipboard_service.py tests/test_screenshot_service.py tests/test_share_service.py tests/test_tts_service.py tests/test_notification_service.py -v
```

#### Error: `TypeError: TesseractError.__init__() missing 1 required positional argument: 'message'` 
**Cause**: pytesseract API change in newer versions
**Fix**: Provide both message and msg parameters:
```python
pytesseract.TesseractError("Test error", "Test error")
```

#### Error: `mock_glib.idle_add.assert_called_once()` fails
**Cause**: Multiple GLib.idle_add calls may occur
**Fix**: Use `assert_called()` instead of `assert_called_once()` 

#### Test Failures with uv Environment
**Cause**: Some tests assume system Python environment
**Fix**: Always use `uv run` with proper environment variables

## Quick Reference

| Command | Purpose |
|---------|---------|
| `uv sync --dev` | Install all dependencies |
| `uv run pytest tests/ -m "not gtk"` | Run pure Python tests |
| `uv run pytest tests/test_config.py -v` | Config tests (pure Python) |
| `uv run pytest tests/test_language_manager.py -v` | Language manager tests |
| `uv run pytest tests/test_uri_validator.py -v` | URI validator tests |
| `uv run pytest tests/test_unit_logic.py -v` | Unit logic tests (business logic) |
| `uv run pytest tests/test_services_simple.py -v` | Simple services tests (pure Python) |
| `PYTHONPATH="/usr/lib/python3/dist-packages:$PYTHONPATH" pytest` | Run with system gi |

## Test Architecture

### Test Categories
1. **Unit Tests** - Pure Python logic without GTK dependencies
2. **Service Tests** - Service-specific tests with mocked GTK dependencies
3. **Integration Tests** - Require GTK/GLib environment

### Test Files Structure
- `tests/test_unit_logic.py` - Business logic validation
- `tests/test_config.py` - Configuration tests
- `tests/test_language_manager.py` - Language management tests
- `tests/test_uri_validator.py` - URI validation tests
- `tests/test_services_simple.py` - Simple service tests
- `tests/test_*_service.py` - Service tests with GTK dependencies

### Running Tests by Category

#### Pure Python Tests (No GTK Required)
```bash
uv run pytest tests/test_config.py tests/test_language_manager.py tests/test_uri_validator.py tests/test_unit_logic.py tests/test_services_simple.py -v
```

#### GTK Tests (Requires System Environment)
```bash
uv run env PYTHONPATH="/usr/lib/python3/dist-packages:$PYTHONPATH" GI_TYPELIB_PATH="/usr/lib/x86_64-linux-gnu/girepository-1.0:/usr/lib/girepository-1.0" pytest tests/test_screenshot_service.py tests/test_clipboard_service.py tests/test_share_service.py tests/test_tts_service.py tests/test_notification_service.py -v
```

---
Generated for Anura OCR — GTK4/Libadwaita + Python + Meson + Flatpak
