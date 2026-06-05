# Velis

**Velis** is a high-performance OCR application for the GNOME desktop. It provides a clean, minimalist interface for extracting text from anywhere on your screen.

## Features
- **OCR Extraction**: Powered by Tesseract.
- **Smart Workflows**: Define custom Regex patterns to automatically extract data like tracking numbers or emails.
- **History Archive**: Keep track of your past extractions, including image snippets.
- **Translation**: Built-in translation via LibreTranslate.
- **Side-by-Side View**: Easily verify extracted text against the original image.

## Technology Stack
- **Language**: Python
- **Toolkit**: GTK4 / Libadwaita
- **Runtime**: GNOME 50 Platform

## Development
This project uses Meson and Blueprint.

```bash
meson setup builddir
meson compile -C builddir
```
