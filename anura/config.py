# This file is part of Anura.
# Copyright (C) 2022-2025 Andrey Maksimov (Frog)
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import os
from pathlib import Path
import re

from loguru import logger

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


def get_tesseract_config(lang_code: str) -> str:
    """
    Returns Tesseract config string with correct --tessdata-dir.

    Tesseract only supports a single --tessdata-dir path. For multi-language
    configurations (e.g. 'eng+ita') where models may be split between system
    (/app/share/tessdata) and user (~/.local/share/anura/tessdata) directories,
    this function creates a dynamic pool in the sandbox cache.

    Args:
        lang_code: The ISO 639-2 language code (e.g., 'eng', 'eng+ita')

    Returns:
        Config string with --tessdata-dir pointing to the correct directory.
    """
    import shutil

    # Security: Validate lang_code
    if not lang_code or not re.match(LANG_CODE_PATTERN, lang_code):
        logger.error(f"Anura: Invalid language code '{lang_code}' - using 'eng'")
        lang_code = "eng"

    # If it's a single language, use standard priority logic without pooling
    if "+" not in lang_code:
        user_model = Path(TESSDATA_DIR) / f"{lang_code}.traineddata"
        if user_model.exists():
            return f'--tessdata-dir "{TESSDATA_DIR}" --psm 3 --oem 1'

        system_model = Path(TESSDATA_SYSTEM_DIR) / f"{lang_code}.traineddata"
        if system_model.exists():
            return f'--tessdata-dir "{TESSDATA_SYSTEM_DIR}" --psm 3 --oem 1'

        return f'--tessdata-dir "{TESSDATA_DIR}" --psm 3 --oem 1'

    # Multi-language: Dynamic Pooling Approach
    codes = lang_code.split("+")
    Path(TESSDATA_POOL_DIR).mkdir(parents=True, exist_ok=True)

    for code in codes:
        # Resolve source
        source_path = None
        user_path = Path(TESSDATA_DIR) / f"{code}.traineddata"
        system_path = Path(TESSDATA_SYSTEM_DIR) / f"{code}.traineddata"

        if user_path.exists():
            source_path = user_path
        elif system_path.exists():
            source_path = system_path

        if source_path:
            dest_path = Path(TESSDATA_POOL_DIR) / f"{code}.traineddata"
            # Create hard link with fallback to copy (for cross-filesystem)
            try:
                if dest_path.exists():
                    dest_path.unlink()
                os.link(source_path, dest_path)
            except (OSError, AttributeError):
                try:
                    shutil.copy2(source_path, dest_path)
                except OSError as e:
                    logger.error(f"Anura Pooling: Failed to copy {code}: {e}")

    return f'--tessdata-dir "{TESSDATA_POOL_DIR}" --psm 3 --oem 1'
