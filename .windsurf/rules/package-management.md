---
trigger: always_on
---

# Package Management with `uv`

These rules define strict guidelines for managing Python dependencies in this project using `uv` dependency manager.

**✅ Use `uv` exclusively**

- All Python dependencies **must be installed, synchronized, and locked** using `uv`.
- Never use `pip`, `pip-tools`, or `poetry` directly for dependency management.

**🔁 Managing Dependencies**

Always use these commands:

```bash
# Add or upgrade dependencies
uv add <package>

# Remove dependencies
uv remove <package>

# Reinstall all dependencies from lock file
uv sync
```

**🔁 Scripts**

```bash
# Run script with proper dependencies
uv run script.py
```

You can edit inline-metadata manually:

```python
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "torch",
#     "torchvision",
#     "opencv-python",
#     "numpy",
#     "matplotlib",
#     "Pillow",
#     "timm",
# ]
# ///

print("some python code")
```

Or using uv cli:

```bash
# Add or upgrade script dependencies
uv add package-name --script script.py

# Remove script dependencies
uv remove package-name --script script.py

# Reinstall all script dependencies from lock file
uv sync --script script.py
```

## Anura OCR Specific Guidelines

**📦 Core Dependencies**

```bash
# Core OCR dependencies
uv add pytesseract Pillow pyzbar

# UI dependencies  
uv add PyGObject gi-adw1

# Network and utilities
uv add requests loguru gtts

# Development dependencies
uv add --dev ruff pytest pytest-asyncio mypy
```

**🏗️ Build System Integration**

```bash
# Meson build with uv environment
uv run meson setup builddir
uv run meson compile -C builddir

# Run application with proper dependencies
GSETTINGS_SCHEMA_DIR=builddir/data uv run python -m anura.main
```

**🧪 Testing with uv**

```bash
# Run tests with proper environment
uv run pytest tests/ -m "not gtk"

# Run GTK tests (requires system dependencies)
uv run pytest tests/ -m gtk
```

**📦 Flatpak Development**

```bash
# Install development dependencies locally
uv sync --dev

# Test before Flatpak build
uv run python -m anura.main --help

# Check for security issues in dependencies
uv add --dev safety
uv run safety check
```

**🔒 Lock File Management**

- Always commit `uv.lock` to version control
- Use `uv sync` to ensure reproducible builds
- Update dependencies with `uv add package@latest` then test thoroughly
- Use `uv tree` to inspect dependency graph

**⚡ Performance Tips**

```bash
# Use uv cache for faster installs
uv cache info

# Clean cache if needed
uv cache clean

# Install only production dependencies
uv sync --no-dev
```

**🔍 Dependency Analysis**

```bash
# Check for outdated dependencies
uv tree --outdated

# Find security vulnerabilities
uv add --dev bandit
uv run bandit -r anura/

# Check license compatibility
uv add --dev pip-licenses
uv run pip-licenses --from=mixed
```

**🚫 Prohibited Commands**

Never use these in Anura OCR development:
- `pip install` - Use `uv add` instead
- `pip freeze` - Use `uv tree` instead  
- `poetry add` - Not compatible with our workflow
- `pip-tools compile` - Use `uv lock` instead

**📝 Environment Management**

```bash
# Create virtual environment
uv venv

# Activate environment
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate     # Windows

# Remove environment
rm -rf .venv
uv venv
```

**🔧 Script Dependencies for Anura**

```python
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pytesseract",
#     "Pillow", 
#     "requests",
#     "loguru"
# ]
# ///

import pytesseract
from PIL import Image
import requests
from loguru import logger

def process_image(image_path: str) -> str:
    """Process image with OCR using uv-managed dependencies."""
    logger.info(f"Processing image: {image_path}")
    
    image = Image.open(image_path)
    text = pytesseract.image_to_string(image)
    
    logger.success(f"Extracted text: {text[:50]}...")
    return text

if __name__ == "__main__":
    result = process_image("example.png")
    print(result)
```

---
Generated for Anura OCR — GTK4/Libadwaita + Python + Meson + Flatpak
