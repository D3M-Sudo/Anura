# config.py
#
# Copyright 2021-2025 Andrey Maksimov
# Copyright 2026 D3M-Sudo (Anura fork and modifications)

import os

# Core Application Identity
# Rebranded for the Anura fork to avoid GSettings/Resource conflicts
APP_ID = "com.github.d3msudo.anura"
RESOURCE_PREFIX = "/com/github/d3msudo/anura"

# XDG Base Directory specification compliance
# Maintains system stability by storing data in the correct user-space location
XDG_DATA_HOME = os.getenv('XDG_DATA_HOME', os.path.expanduser('~/.local/share'))

# Anura specific data directory for OCR models
TESSDATA_DIR = os.path.join(XDG_DATA_HOME, 'anura', 'tessdata')

# Ensure the local directory exists for system stability
if not os.path.exists(TESSDATA_DIR):
    os.makedirs(TESSDATA_DIR, exist_ok=True)

# Tesseract OCR Repository URLs
# Standard: balance between speed and accuracy
TESSDATA_URL = "https://github.com/tesseract-ocr/tessdata/raw/main/"
# Best: High-accuracy LSTM models (Anura priority)
TESSDATA_BEST_URL = "https://github.com/tesseract-ocr/tessdata_best/raw/main/"

# Network Configuration for LanguageManager
USER_AGENT = "Anura-OCR-Client/1.0 (Linux; Linux Mint Cinnamon)"
REQUEST_TIMEOUT = 30  # seconds

# Technical OCR parameters:
# --tessdata-dir: explicit path to local models
# --psm 3: Fully automatic page segmentation
# --oem 1: Neural nets LSTM engine only
TESSDATA_CONFIG = f'--tessdata-dir {TESSDATA_DIR} --psm 3 --oem 1'