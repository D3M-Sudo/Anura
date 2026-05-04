# cleanup.py
#
# Copyright 2026 D3M-Sudo (Anura fork and modifications)
#
# Resource cleanup utilities for Anura OCR

import os
import time

from loguru import logger

from anura.config import TESSDATA_DIR


def cleanup_orphaned_resources() -> None:
    """
    Clean up orphaned temporary files from previous sessions.

    This function safely removes stale temporary files from:
    - TTS cache directory (~/.cache/anura/*.mp3)
    - Tessdata directory (~/.local/share/anura/tessdata/*.tmp)

    Only files older than 1 hour are removed to avoid conflicts with
    currently running operations.
    """
    current_time = time.monotonic()
    one_hour_ago = current_time - 3600  # 1 hour in seconds

    # Clean up TTS cache files
    _cleanup_tts_cache(one_hour_ago)

    # Clean up tessdata temporary files
    _cleanup_tessdata_temp_files(one_hour_ago)


def _cleanup_tts_cache(cutoff_time: float) -> None:
    """Clean up old TTS MP3 files from cache directory."""
    try:
        cache_dir = os.environ.get("XDG_CACHE_HOME", os.path.expanduser("~/.cache"))
        tts_cache_dir = os.path.join(cache_dir, "anura")

        if not os.path.exists(tts_cache_dir):
            return

        if not os.access(tts_cache_dir, os.R_OK | os.W_OK):
            logger.warning(f"Anura Cleanup: Cannot access TTS cache directory: {tts_cache_dir}")
            return

        cleaned_count = 0
        for filename in os.listdir(tts_cache_dir):
            if filename.endswith('.mp3'):
                file_path = os.path.join(tts_cache_dir, filename)
                try:
                    # Check file age to avoid deleting recent files
                    file_mtime = os.path.getmtime(file_path)
                    if file_mtime < cutoff_time:
                        os.remove(file_path)
                        cleaned_count += 1
                        logger.debug(f"Anura Cleanup: Removed old TTS file: {filename}")
                except (OSError, PermissionError) as e:
                    logger.warning(f"Anura Cleanup: Failed to remove TTS file {filename}: {e}")

        if cleaned_count > 0:
            logger.info(f"Anura Cleanup: Removed {cleaned_count} old TTS cache files")

    except OSError as e:
        logger.error(f"Anura Cleanup: Error accessing TTS cache directory: {e}")


def _cleanup_tessdata_temp_files(cutoff_time: float) -> None:
    """Clean up orphaned temporary files from tessdata directory."""
    try:
        if not os.path.exists(TESSDATA_DIR):
            return

        if not os.access(TESSDATA_DIR, os.R_OK | os.W_OK):
            logger.warning("Anura Cleanup: Cannot access tessdata directory for cleanup")
            return

        cleaned_count = 0
        for filename in os.listdir(TESSDATA_DIR):
            if filename.endswith('.tmp'):
                file_path = os.path.join(TESSDATA_DIR, filename)
                try:
                    # Check file age to avoid deleting active downloads
                    file_mtime = os.path.getmtime(file_path)
                    if file_mtime < cutoff_time:
                        os.remove(file_path)
                        cleaned_count += 1
                        logger.debug(f"Anura Cleanup: Removed orphaned temp file: {filename}")
                except (OSError, PermissionError) as e:
                    logger.warning(f"Anura Cleanup: Failed to remove temp file {filename}: {e}")

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
        cache_dir = os.environ.get("XDG_CACHE_HOME", os.path.expanduser("~/.cache"))
        tts_cache_dir = os.path.join(cache_dir, "anura")

        if os.path.exists(tts_cache_dir):
            for filename in os.listdir(tts_cache_dir):
                if filename.endswith('.mp3'):
                    file_path = os.path.join(tts_cache_dir, filename)
                    cache_info["tts_files"] += 1
                    cache_info["tts_size_bytes"] += os.path.getsize(file_path)

        # Temp files info
        if os.path.exists(TESSDATA_DIR):
            for filename in os.listdir(TESSDATA_DIR):
                if filename.endswith('.tmp'):
                    cache_info["temp_files"] += 1

    except OSError as e:
        logger.debug("Anura Cleanup: Error getting cache info: %s", e)

    return cache_info
