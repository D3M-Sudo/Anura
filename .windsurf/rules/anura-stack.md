# Anura Tech Stack

- **Linguaggio**: Python 3.12+
- **Build System**: Meson ≥ 1.5.0
- **UI Framework**: GTK4 + Libadwaita
- **Declarative UI**: Blueprint Compiler ≥ 0.16.0
- **OCR Engine**: Tesseract OCR 5.5.0 (via `pytesseract`)
- **QR/Barcode Engine**: zxing-cpp 2.3.0 (replaces legacy pyzbar)
- **Text-to-Speech**: gTTS + GStreamer `playbin3`
- **Screenshots**: XDG Desktop Portal (via `libportal` / `Xdp`) + Fallback **scrot** (X11 only)
- **Sandbox**: Flatpak (GNOME 50 runtime)
- **Async Processing**: `AtomicTaskManager` (single-slot, UUID versioning)
- **Dependency Management**: `uv`
- **Linting & Formatting**: `ruff`
