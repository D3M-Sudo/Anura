# config.py
#
# Copyright 2021-2025 Andrey Maksimov
# Copyright 2026 D3M-Sudo (Anura fork and modifications)

import os

# Core Application Identity
APP_ID = "com.github.d3msudo.anura"
RESOURCE_PREFIX = "/com/github/d3msudo/anura"

# XDG Base Directory specification compliance
XDG_DATA_HOME = os.getenv("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))
XDG_CACHE_HOME = os.getenv("XDG_CACHE_HOME", os.path.expanduser("~/.cache"))

# Anura specific data directory for OCR models
TESSDATA_DIR = os.path.join(XDG_DATA_HOME, "anura", "tessdata")

# Ensure the local directory exists
os.makedirs(TESSDATA_DIR, exist_ok=True)

# Tesseract OCR Repository URLs
TESSDATA_URL = "https://github.com/tesseract-ocr/tessdata/raw/main/"
TESSDATA_BEST_URL = "https://github.com/tesseract-ocr/tessdata_best/raw/main/"

# Network configuration for LanguageManager
USER_AGENT = "Anura-OCR-Client/1.0 (Linux; Flatpak)"
REQUEST_TIMEOUT = 30  # seconds

# Tesseract OCR parameters
# --psm 3: Fully automatic page segmentation
# --oem 1: Neural nets LSTM engine only
# FIX: renamed from TESSDATA_CONFIG to tessdata_config (snake_case) to match
# the import in screenshot_service.py: `from anura.config import tessdata_config`
tessdata_config = f"--tessdata-dir {TESSDATA_DIR} --psm 3 --oem 1"
