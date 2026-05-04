---
trigger: always_on
---

# Anura OCR — Tech Stack

- Language: Python 3.12+
- Build: Meson ≥ 1.5.0
- Distribution: Flatpak (com.github.d3msudo.anura)
- UI: GTK4 + Libadwaita + Blueprint Compiler 0.16.0
- OCR: pytesseract + Tesseract 5.5.0
- QR: pyzbar + zbar
- TTS: gTTS + GStreamer playbin3
- Screenshots: Xdp.Portal (libportal)
- Settings: GSettings singleton → anura/services/settings.py
- Lang validation: LANG_CODE_PATTERN in anura/config.py
- URI validation: uri_validator() in anura/window.py