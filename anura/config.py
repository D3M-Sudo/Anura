# config.py
#
# Copyright 2021-2025 Andrey Maksimov
# Copyright 2026 D3M-Sudo (Anura fork and modifications)

import os
import re

from loguru import logger

# Core Application Identity
APP_ID = "com.github.d3msudo.anura"
RESOURCE_PREFIX = "/com/github/d3msudo/anura"

# Language code validation pattern (ISO 639-2, 2-8 alphanumeric chars with underscore)
LANG_CODE_PATTERN = r'^[a-zA-Z0-9_]{2,8}$'

# XDG Base Directory specification compliance
XDG_DATA_HOME = os.getenv("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))
XDG_CACHE_HOME = os.getenv("XDG_CACHE_HOME", os.path.expanduser("~/.cache"))

# Anura specific data directory for OCR models (user-downloaded)
TESSDATA_DIR = os.path.join(XDG_DATA_HOME, "anura", "tessdata")


def _get_tessdata_system_dir() -> str:
    """
    Resolve the system tessdata directory with multiple fallback paths.

    Check order:
    1. Environment variable (TESSDATA_PREFIX_SYSTEM)
    2. Flatpak path (/app/share/tessdata)
    3. System paths common on Linux distributions

    Returns:
        The first valid directory path found, or the Flatpak default as fallback.
    """
    # Priority 1: Environment variable override
    env_path = os.getenv("TESSDATA_PREFIX_SYSTEM")
    if env_path and os.path.isdir(env_path):
        return env_path

    # Priority 2: Flatpak path
    flatpak_path = "/app/share/tessdata"
    if os.path.isdir(flatpak_path):
        return flatpak_path

    # Priority 3: Common system paths
    system_paths = [
        "/usr/share/tesseract-ocr/4.00/tessdata",
        "/usr/share/tesseract-ocr/tessdata",
        "/usr/share/tessdata",
    ]

    for path in system_paths:
        if os.path.isdir(path):
            return path

    # Fallback to Flatpak default even if not present (for Flatpak builds)
    return flatpak_path


# System directory with models bundled by the Flatpak manifest
# Uses dynamic resolution with fallbacks for non-Flatpak installations
TESSDATA_SYSTEM_DIR = _get_tessdata_system_dir()

# Note: TESSDATA_DIR creation is handled by language_manager.init_tessdata()
# to avoid side effects at import time.

# Tesseract OCR Repository URLs
TESSDATA_URL = "https://github.com/tesseract-ocr/tessdata/raw/main/"
TESSDATA_BEST_URL = "https://github.com/tesseract-ocr/tessdata_best/raw/main/"

# Network configuration for LanguageManager
USER_AGENT = "Anura-OCR-Client/1.0 (Linux; Flatpak)"
REQUEST_TIMEOUT = 30  # seconds

# Tesseract OCR parameters
# --psm 3: Fully automatic page segmentation
# --oem 1: Neural nets LSTM engine only


def get_tesseract_config(lang_code: str) -> str:
    """
    Returns Tesseract config string with correct --tessdata-dir.

    Tesseract only supports a single --tessdata-dir path, not colon-separated
    multiple paths. This function checks both user and system directories
    and returns the appropriate path based on where the language model exists.

    Priority: User directory > System directory (bundled with Flatpak)

    Args:
        lang_code: The ISO 639-2 language code (e.g., 'eng', 'ita')

    Returns:
        Config string with --tessdata-dir pointing to the correct directory.
        Paths are quoted to handle spaces in directory names.
    """
    # Security: Validate lang_code is a valid ISO 639-2 code
    if not lang_code or not re.match(LANG_CODE_PATTERN, lang_code):
        logger.error(f"Anura: Invalid language code '{lang_code}' - using default 'eng'")
        lang_code = "eng"

    # Check user directory first (user models take priority)
    user_model = os.path.join(TESSDATA_DIR, f"{lang_code}.traineddata")
    if os.path.exists(user_model):
        return f'--tessdata-dir "{TESSDATA_DIR}" --psm 3 --oem 1'

    # Fall back to system directory (bundled models in Flatpak)
    system_model = os.path.join(TESSDATA_SYSTEM_DIR, f"{lang_code}.traineddata")
    if os.path.exists(system_model):
        return f'--tessdata-dir "{TESSDATA_SYSTEM_DIR}" --psm 3 --oem 1'

    # If model not found in either location, default to user dir
    # Tesseract will fail gracefully with a missing language error
    logger.warning(f"Anura: Model '{lang_code}' not found in user or system tessdata directories")
    return f'--tessdata-dir "{TESSDATA_DIR}" --psm 3 --oem 1'
