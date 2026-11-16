# This file is part of Anura.
# Copyright (C) 2022-2025 Andrey Maksimov (Frog)
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import contextlib
import os
from pathlib import Path
import shutil
import time

from loguru import logger

from anura.config import TESSDATA_DIR, TESSDATA_POOL_DIR, TESSDATA_POOL_LEASE
from anura.utils.export_files import cleanup_stale_export_files

# A pool directory without a lease file is only considered abandoned after
# this long: a task can legitimately run for hours, and the PID lease is the
# authoritative signal when it exists (#521).
STALE_POOL_DIR_AGE_SECONDS = 24 * 3600


def cleanup_orphaned_resources(active_lang_code: str = "eng") -> None:
    """
    Clean up orphaned temporary files from previous sessions.

    This function safely removes stale temporary files from:
    - TTS cache directory (~/.cache/anura/*.mp3)
    - Tessdata directory (~/.local/share/anura/tessdata/*.tmp)
    - Tessdata pool directory (~/.cache/anura/tessdata_pool/*.traineddata)
    - OCR export directory ($XDG_RUNTIME_DIR/anura/exports or ~/.cache/anura/exports)

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

    # Clean up stale OCR export files (external editor handoff)
    try:
        removed = cleanup_stale_export_files(one_hour_ago)
        if removed > 0:
            logger.info(f"Anura Cleanup: Removed {removed} stale export files")
    except OSError as e:
        logger.error(f"Anura Cleanup: Error cleaning export directory: {e}")


def _cleanup_tts_cache(cutoff_time: float) -> None:
    """Clean up old TTS MP3 files from cache directory."""
    try:
        cache_dir_str = os.environ.get("XDG_CACHE_HOME")
        cache_dir = Path(cache_dir_str) if cache_dir_str else Path.home() / ".cache"

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


def _pid_is_alive(pid: int) -> bool:
    """Return True when a process with *pid* exists (best effort)."""
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        # The process exists but belongs to another user.
        return True
    except OSError:
        # Cannot tell: assume it is alive and keep the files.
        return True
    return True


def _read_lease_pid(directory: Path) -> int | None:
    """Read the owner PID from a task pool directory, or None when absent."""
    try:
        return int((directory / TESSDATA_POOL_LEASE).read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return None


def _cleanup_tessdata_pool(_active_lang_code: str) -> None:
    """Remove only task pool directories that provably have no live owner.

    Top-level ``*.traineddata`` files are **never** removed here: the pool is
    shared by every Anura instance, so deleting the models that do not match
    this instance's active language could remove a file another instance (or a
    long-running OCR task) is reading (#521).

    A task directory is removed only when
      * its ``owner.pid`` lease names a process that no longer exists, or
      * it has no lease (legacy directory) and is older than one day.

    The active language argument is kept for API compatibility; it no longer
    decides what is deleted.
    """
    pool_dir = Path(TESSDATA_POOL_DIR)
    if not pool_dir.exists():
        return

    try:
        removed_count = 0
        legacy_cutoff = time.time() - STALE_POOL_DIR_AGE_SECONDS

        for item in pool_dir.iterdir():
            if not item.is_dir():
                continue
            try:
                owner = _read_lease_pid(item)
                if owner is not None:
                    if _pid_is_alive(owner):
                        logger.debug(f"Anura Cleanup: pool dir {item.name} is owned by live process {owner}")
                        continue
                    stale = True
                else:
                    # Legacy directory: only age can prove it is abandoned.
                    stale = item.stat().st_mtime < legacy_cutoff

                if stale:
                    shutil.rmtree(item)
                    removed_count += 1
            except OSError as e:
                logger.debug(f"Anura Cleanup: Failed to remove pool dir {item.name}: {e}")

        if removed_count > 0:
            logger.info(f"Anura Cleanup: Removed {removed_count} stale pool directories")

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
        cache_dir = Path(cache_dir_str) if cache_dir_str else Path.home() / ".cache"

        tts_cache_dir = cache_dir / "anura"

        if tts_cache_dir.exists():
            for file_path in tts_cache_dir.glob("*.mp3"):
                cache_info["tts_files"] += 1
                with contextlib.suppress(OSError, FileNotFoundError):
                    cache_info["tts_size_bytes"] += file_path.stat().st_size

        # Temp files info
        tessdata_dir = Path(TESSDATA_DIR)
        if tessdata_dir.exists():
            for _ in tessdata_dir.glob("*.tmp"):
                cache_info["temp_files"] += 1

    except OSError as e:
        logger.debug(f"Anura Cleanup: Error getting cache info: {e}")

    return cache_info
