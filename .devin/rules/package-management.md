# Package Management with uv

## Guidelines

- **Always** use `uv` for managing Python dependencies.
- Use `uv sync --dev` to synchronize the development environment.
- Add new dependencies with `uv add <package>`.
- Remove dependencies with `uv remove <package>`.
- Never use `pip`, `poetry`, or `pip-tools` directly.

## Core Runtime Dependencies
- `pytesseract`
- `Pillow`
- `zxing-cpp`
- `gtts`
- `loguru`
- `requests`

## Development Dependencies
- `meson`
- `ninja`
- `ruff`
- `pytest`
- `pytest-cov`
- `blueprint-compiler`
