# This file is part of Anura.
# Copyright (C) 2022-2025 Andrey Maksimov (Frog)
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import os
from pathlib import Path
import time

from loguru import logger

from anura.config import TESSDATA_DIR, TESSDATA_POOL_DIR


def cleanup_orphaned_resources(active_lang_code: str = "eng") -> None:
    """
    Clean up orphaned temporary files from previous sessions.

    This function safely removes stale temporary files from:
    - TTS cache directory (~/.cache/anura/*.mp3)
    - Tessdata directory (~/.local/share/anura/tessdata/*.tmp)
    - Tessdata pool directory (~/.cache/anura/tessdata_pool/*.traineddata)

    Only files older than 1 hour are removed for general temp files.
    The pool is cleaned based on currently needed models.
    """
    current_time = time.time()
    one_hour_ago = current_time - 3600  # 1 hour in seconds

    # Clean up TTS cache files
    _cleanup_tts_cache(one_hour_ago)

    # Clean up tessdata temporary files
    _cleanup_tessdata_temp_files(one_hour_ago)

    # Clean up stale models from the pool
    _cleanup_tessdata_pool(active_lang_code)


def _cleanup_tts_cache(cutoff_time: float) -> None:
    """Clean up old TTS MP3 files from cache directory."""
    try:
        cache_dir_str = os.environ.get("XDG_CACHE_HOME")
        if cache_dir_str:
            cache_dir = Path(cache_dir_str)
        else:
            cache_dir = Path.home() / ".cache"

        tts_cache_dir = cache_dir / "anura"

        if not tts_cache_dir.exists():
            return

        # Check access - pathlib doesn't have a direct equivalent to os.access for specific modes easily
        # but we can try-except the operations.

        cleaned_count = 0
        for file_path in tts_cache_dir.glob("*.mp3"):
            try:
                # Check file age to avoid deleting recent files
                file_mtime = file_path.stat().st_mtime
                if file_mtime < cutoff_time:
                    file_path.unlink()
                    cleaned_count += 1
                    logger.debug(f"Anura Cleanup: Removed old TTS file: {file_path.name}")
            except OSError as e:
                logger.warning(f"Anura Cleanup: Failed to remove TTS file {file_path.name}: {e}")

        if cleaned_count > 0:
            logger.info(f"Anura Cleanup: Removed {cleaned_count} old TTS cache files")

    except OSError as e:
        logger.error(f"Anura Cleanup: Error accessing TTS cache directory: {e}")


def _cleanup_tessdata_pool(active_lang_code: str) -> None:
    """
    Remove stale models from the pool that are not needed for the active language.

    Args:
        active_lang_code: The currently active language code (e.g. 'eng' or 'eng+ita')
    """
    pool_dir = Path(TESSDATA_POOL_DIR)
    if not pool_dir.exists():
        return

    try:
        needed_codes = set(active_lang_code.split("+"))
        removed_count = 0

        for file_path in pool_dir.glob("*.traineddata"):
            stem = file_path.name[:-12]  # Remove .traineddata
            if stem not in needed_codes:
                try:
                    file_path.unlink()
                    removed_count += 1
                    logger.debug(f"Anura Cleanup: Removed stale pool model: {file_path.name}")
                except OSError as e:
                    logger.warning(f"Anura Cleanup: Failed to remove stale model {file_path.name}: {e}")

        if removed_count > 0:
            logger.info(f"Anura Cleanup: Removed {removed_count} stale pool models")

    except OSError as e:
        logger.error(f"Anura Cleanup: Error scanning tessdata pool directory: {e}")


def _cleanup_tessdata_temp_files(cutoff_time: float) -> None:
    """Clean up orphaned temporary files from tessdata directory."""
    try:
        tessdata_dir = Path(TESSDATA_DIR)
        if not tessdata_dir.exists():
            return

        cleaned_count = 0
        for file_path in tessdata_dir.glob("*.tmp"):
            try:
                # Check file age to avoid deleting active downloads
                file_mtime = file_path.stat().st_mtime
                if file_mtime < cutoff_time:
                    file_path.unlink()
                    cleaned_count += 1
                    logger.debug(f"Anura Cleanup: Removed orphaned temp file: {file_path.name}")
            except OSError as e:
                logger.warning(f"Anura Cleanup: Failed to remove temp file {file_path.name}: {e}")
        if cleaned_count > 0:
            logger.info(f"Anura Cleanup: Removed {cleaned_count} orphaned temporary files")

    except OSError as e:
        logger.error(f"Anura Cleanup: Error scanning tessdata directory: {e}")


def get_cache_info() -> dict[str, int]:
    """
    Get information about cache directory sizes for debugging.

    Returns:
        Dictionary with cache statistics
    """
    cache_info = {"tts_files": 0, "tts_size_bytes": 0, "temp_files": 0}

    try:
        # TTS cache info
        cache_dir_str = os.environ.get("XDG_CACHE_HOME")
        if cache_dir_str:
            cache_dir = Path(cache_dir_str)
        else:
            cache_dir = Path.home() / ".cache"

        tts_cache_dir = cache_dir / "anura"

        if tts_cache_dir.exists():
            for file_path in tts_cache_dir.glob("*.mp3"):
                cache_info["tts_files"] += 1
                try:
                    cache_info["tts_size_bytes"] += file_path.stat().st_size
                except (OSError, FileNotFoundError):
                    # File might have been deleted between listdir and getsize
                    pass

        # Temp files info
        tessdata_dir = Path(TESSDATA_DIR)
        if tessdata_dir.exists():
            for _ in tessdata_dir.glob("*.tmp"):
                cache_info["temp_files"] += 1

    except OSError as e:
        logger.debug(f"Anura Cleanup: Error getting cache info: {e}")

    return cache_info
