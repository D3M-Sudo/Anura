# This file is part of Anura.
# Copyright (C) 2022-2025 Andrey Maksimov (Frog)
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import os
from pathlib import Path

# Core Application Identity
APP_ID = "io.github.d3msudo.anura"

# Logging configuration — override via ANURA_LOG_LEVEL env var
_LOG_LEVEL = os.environ.get("ANURA_LOG_LEVEL", "INFO").upper()
_VALID_LOG_LEVELS = {"TRACE", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
LOG_LEVEL: str = _LOG_LEVEL if _LOG_LEVEL in _VALID_LOG_LEVELS else "INFO"
RESOURCE_PREFIX = "/io/github/d3msudo/anura"

# Language code validation pattern (ISO 639-2, 2-18 alphanumeric chars with plus and underscore)
# Plus character allows multi-language OCR codes like "eng+ita"
# Underscore allowed for Tesseract codes like "chi_sim" (Chinese Simplified)
LANG_CODE_PATTERN = r"^[a-zA-Z0-9+_]{2,18}$"

# XDG Base Directory specification compliance
XDG_DATA_HOME = os.getenv("XDG_DATA_HOME", str(Path.home() / ".local/share"))
XDG_CACHE_HOME = os.getenv("XDG_CACHE_HOME", str(Path.home() / ".cache"))

# Anura specific data directory for OCR models (user-downloaded)
TESSDATA_DIR = str(Path(XDG_DATA_HOME) / "anura" / "tessdata")

# Cache directory for multi-language model pooling (Flatpak optimization)
TESSDATA_POOL_DIR = str(Path(XDG_CACHE_HOME) / "anura" / "tessdata_pool")

# Maximum image file size (50MB) to prevent memory exhaustion (DoS)
# Used for input validation across services and UI.
MAX_IMAGE_SIZE_MB = 50
MAX_IMAGE_SIZE_BYTES = MAX_IMAGE_SIZE_MB * 1024 * 1024

# Maximum length for extracted text (1,000,000 characters) to prevent DoS
# from excessively large OCR output and expensive downstream processing.
MAX_TEXT_LENGTH = 1_000_000


def _get_tessdata_system_dir() -> str:
    """
    Resolve the system tessdata directory with multiple fallback paths.

    Check order:
    1. Environment variable (TESSDATA_PREFIX_SYSTEM)
    2. Flatpak path (/app/share/tessdata)
    3. Common system paths on Linux distributions

    Returns:
        The first valid directory path found, or the Flatpak default as fallback.
    """
    # Priority 1: Environment variable override
    env_path = os.getenv("TESSDATA_PREFIX_SYSTEM")
    if env_path and Path(env_path).is_dir():
        return env_path

    # Priority 2: Dynamic scan of candidate directories
    # Scan in order of preference - first existing directory wins
    candidate_dirs = [
        "/app/share/tessdata",  # Flatpak
        "/usr/share/tesseract-ocr/tessdata",  # Debian/Ubuntu, Arch, Fedora
        "/usr/share/tesseract/tessdata",  # Alternative layout
        "/usr/share/tessdata",  # Alternative system path
    ]

    for path in candidate_dirs:
        if Path(path).is_dir():
            return path

    # Fallback to Flatpak default even if not present (for Flatpak builds)
    return "/app/share/tessdata"


# System directory with models bundled by the Flatpak manifest
# Uses dynamic resolution with fallbacks for non-Flatpak installations
TESSDATA_SYSTEM_DIR = _get_tessdata_system_dir()

# Note: TESSDATA_DIR creation is handled by language_manager.init_tessdata()
# to avoid side effects at import time.

# Tesseract OCR Repository URLs
# Pinned to specific commit hashes for security and immutability.
# tessdata (standard models) - Pinned to main as of 2024-05-18
TESSDATA_URL = "https://github.com/tesseract-ocr/tessdata/raw/4767ea922bcc460e70b87b1d303ebdfed0e3060b/"
# tessdata_best (high-quality models) - Pinned to main as of 2024-05-18
TESSDATA_BEST_URL = "https://github.com/tesseract-ocr/tessdata_best/raw/923915d4ced2a7235221788285785a29c4a42d4a/"
# TESSDATA_STANDARD_URL (balanced models) - Pinned to main as of 2024-05-18
TESSDATA_STANDARD_URL = "https://github.com/tesseract-ocr/tessdata/raw/4767ea922bcc460e70b87b1d303ebdfed0e3060b/"

# Network configuration for LanguageManager
USER_AGENT = "Anura-OCR-Client/1.0 (Linux; Flatpak)"
REQUEST_TIMEOUT = 30  # seconds

# Tesseract OCR parameters
# --psm 3: Fully automatic page segmentation
# --oem 1: Neural nets LSTM engine only
# Note: get_tesseract_config() is defined in anura.services.language_manager
# and imported from there by all callers (screenshot_service.py line 33).
