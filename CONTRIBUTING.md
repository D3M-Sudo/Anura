# CONTRIBUTING.md - Contributing to Velis

## Development Setup

1. **Prerequisites**:
   - Python 3.12+
   - GTK4 / Libadwaita
   - Meson, Ninja
   - Tesseract OCR

2. **Clone and Build**:
   ```bash
   git clone https://github.com/d3msudo/velis
   cd velis
   meson setup builddir
   meson compile -C builddir
   ```

3. **Run from source**:
   ```bash
   PYTHONPATH=. python3 velis/main.py
   ```

## Coding Guidelines
- Follow PEP 8.
- Use `ruff` for formatting and linting.
- All core business logic should be in `velis/services/` and tested in `tests/`.
- UI templates are defined in `data/ui/` (Blueprint or XML).

## Pull Requests
- Create a feature branch.
- Ensure all tests pass.
- Write clear commit messages.
