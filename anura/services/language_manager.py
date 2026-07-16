# This file is part of Anura.
# Copyright (C) 2022-2025 Andrey Maksimov (Frog)
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import contextlib
from gettext import gettext as _
import os
from pathlib import Path
import re
import shutil
from typing import ClassVar

import gi

# Set GTK version requirements before imports
gi.require_version("GLib", "2.0")
gi.require_version("GObject", "2.0")
gi.require_version("Gio", "2.0")

from gi.repository import Gio, GLib, GObject  # noqa: E402
from loguru import logger  # noqa: E402

from anura.config import (  # noqa: E402
    LANG_CODE_PATTERN,
    TESSDATA_POOL_DIR,
    TESSDATA_SYSTEM_DIR,
)
from anura.models.language_item import LanguageItem  # noqa: E402
from anura.services.language import CacheManager, DownloadManager, LanguageValidator  # noqa: E402
from anura.services.settings import settings  # noqa: E402
from anura.utils.singleton import get_instance  # noqa: E402


class LanguageManager(GObject.GObject):
    """
    Centralized coordinator for Tesseract language models.
    Delegates to specialized managers for downloads, caching, and validation.
    """

    __gtype_name__ = "LanguageManager"

    __gsignals__: ClassVar[dict[str, tuple]] = {
        "added": (GObject.SignalFlags.RUN_FIRST, None, (str,)),
        "downloading": (GObject.SignalFlags.RUN_FIRST, None, (str, int)),
        "downloaded": (GObject.SignalFlags.RUN_FIRST, None, (str,)),
        "download-failed": (GObject.SignalFlags.RUN_FIRST, None, (str,)),
        "removed": (GObject.SignalFlags.RUN_FIRST, None, (str,)),
    }

    _active_language: LanguageItem = LanguageItem(code="eng", title=_("English"))

    def __init__(self) -> None:
        super().__init__()
        self._cache_manager = CacheManager()
        self._download_manager = DownloadManager()
        self._validator = LanguageValidator()

        # Connect download manager signals to forward them
        self._download_manager.connect("downloading", self._on_downloading)
        self._download_manager.connect("downloaded", self._on_downloaded)
        self._download_manager.connect("download-failed", self._on_download_failed)

    @GObject.Property(type=GObject.TYPE_PYOBJECT)
    def active_language(self) -> LanguageItem:
        return self._active_language

    @active_language.setter  # type: ignore[no-redef]
    def active_language(self, language: LanguageItem) -> None:
        self._active_language = language
        self.notify("active-language")

    def _on_downloading(self, _manager: DownloadManager, code: str, progress: int) -> None:
        """Forward downloading signal from DownloadManager."""
        self.emit("downloading", code, progress)

    def _on_downloaded(self, _manager: DownloadManager, code: str) -> None:
        """Forward downloaded signal from DownloadManager and invalidate cache."""
        self._cache_manager.invalidate_cache()
        self.emit("downloaded", code)

    def _on_download_failed(self, _manager: DownloadManager, code: str) -> None:
        """Forward download-failed signal from DownloadManager."""
        self.emit("download-failed", code)

    def init_tessdata(self) -> None:
        """Initialize tessdata directory and clean up orphaned files."""
        self._cache_manager.init_tessdata()

    def get_language(self, code: str) -> str:
        """Returns the human-readable language name for a given ISO code."""
        return self._validator.get_language_name(code)

    def get_language_item(self, code: str) -> LanguageItem | None:
        """Returns a LanguageItem for a given code."""
        return self._validator.get_language_item(code)

    def get_downloaded_codes(self, force: bool = False) -> list[str]:
        """Returns codes of all installed language models (user + system bundled)."""
        return self._cache_manager.get_downloaded_codes(force)

    def get_downloaded_languages(self, force: bool = False) -> list[str]:
        """Returns the names of the installed languages."""
        return self._cache_manager.get_downloaded_languages(self.get_language, force)

    def get_available_codes(self) -> list[str]:
        """Returns all ISO codes supported by Tesseract (installed or not)."""
        return self._validator.get_available_codes()

    def get_language_code(self, name: str) -> str:
        """Reverse lookup: from name to ISO code."""
        return self._validator.get_language_code(name)

    def download(self, code: str, cancellable: Gio.Cancellable | None = None) -> None:
        """Thread-safe asynchronous download process."""
        # Validate code before starting download
        if not self._validator.is_valid_code(code):
            logger.error(f"Anura: Blocked invalid language code download attempt: '{code}'")
            return

        def _on_added_idle(c):
            try:
                self.emit("added", c)
            except (AttributeError, RuntimeError, TypeError) as e:
                logger.exception(f"Anura: Failed to emit 'added' signal for {c}: {e}")
            return GLib.SOURCE_REMOVE

        GLib.idle_add(_on_added_idle, code, priority=GLib.PRIORITY_DEFAULT)

        # Delegate to download manager
        self._download_manager.download(code, cancellable)

    def shutdown(self) -> None:
        """Shut down the download manager."""
        self._download_manager.shutdown()

    def remove_language(self, code: str) -> None:
        """Thread-safe removal of model file from system."""
        # Validate code format only — file on disk is the source of truth
        if not self._validator.is_valid_code_format(code):
            logger.error(f"Anura: Blocked invalid language code removal attempt: '{code}'")
            return

        success = self._cache_manager.remove_model_file(code)
        if success:
            def _on_removed_idle(c):
                try:
                    self.emit("removed", c)
                except (AttributeError, RuntimeError, TypeError) as e:
                    logger.exception(f"Anura: Failed to emit 'removed' for {c}: {e}")
                return GLib.SOURCE_REMOVE

            GLib.idle_add(_on_removed_idle, code, priority=GLib.PRIORITY_DEFAULT)

    def _get_model_quality_dir(self, quality: str | None = None) -> Path:
        """
        Get the directory for the specified model quality.
        Delegates to CacheManager for backward compatibility with tests.
        """
        return self._cache_manager._get_model_quality_dir(quality)


def get_tesseract_config(lang_code: str, task_id: str | None = None) -> str:
    """
    Returns Tesseract config string with correct --tessdata-dir.

    Tesseract only supports a single --tessdata-dir path. For multi-language
    configurations (e.g. 'eng+ita') where models may be split between system
    (/app/share/tessdata) and user (~/.local/share/anura/tessdata) directories,
    this function creates a dynamic pool in the sandbox cache.

    Args:
        lang_code: The ISO 639-2 language code (e.g., 'eng', 'eng+ita')
        task_id: Optional ID for task-isolated pooling (prevents race conditions).

    Returns:
        Config string with --tessdata-dir pointing to the correct directory.
    """
    # Security: Validate lang_code
    if not lang_code or not re.match(LANG_CODE_PATTERN, lang_code):
        logger.error(f"Anura: Invalid language code '{lang_code}' - using 'eng'")
        lang_code = "eng"

    quality = settings.get_string("tessdata-model")
    quality_dir = get_language_manager()._get_model_quality_dir(quality)
    quality_dir_str = str(quality_dir)

    # If it's a single language, use standard priority logic without pooling
    if "+" not in lang_code:
        user_model = quality_dir / f"{lang_code}.traineddata"
        if user_model.exists():
            return f'--tessdata-dir "{quality_dir_str}" --psm 3 --oem 1'

        system_model = Path(TESSDATA_SYSTEM_DIR) / f"{lang_code}.traineddata"
        if system_model.exists():
            return f'--tessdata-dir "{TESSDATA_SYSTEM_DIR}" --psm 3 --oem 1'

        return f'--tessdata-dir "{quality_dir_str}" --psm 3 --oem 1'

    # Multi-language: Dynamic Pooling Approach
    codes = lang_code.split("+")

    # BUG-P1-REPRO / NEW-007: Use task-isolated subdirectories to prevent race conditions.
    # If no task_id provided (e.g. CLI or legacy call), fallback to shared directory.
    pool_dir = Path(TESSDATA_POOL_DIR)
    if task_id:
        pool_dir = pool_dir / task_id

    # Security: Ensure tessdata pool directory has restrictive permissions (0700)
    pool_dir.mkdir(parents=True, exist_ok=True)
    with contextlib.suppress(OSError):
        pool_dir.chmod(0o700)

    for code in codes:
        # Resolve source
        source_path = None
        user_path = quality_dir / f"{code}.traineddata"
        system_path = Path(TESSDATA_SYSTEM_DIR) / f"{code}.traineddata"

        if user_path.exists():
            source_path = user_path
        elif system_path.exists():
            source_path = system_path

        if source_path:
            dest_path = pool_dir / f"{code}.traineddata"
            # NEW-004: Create hard link with fallback to copy (for cross-filesystem)
            try:
                if dest_path.exists():
                    dest_path.unlink()
                os.link(source_path, dest_path)
            except OSError as e:
                import errno

                if e.errno == errno.EXDEV:
                    # Cross-device link failure: use copy instead, suppress error noise
                    try:
                        shutil.copy2(source_path, dest_path)
                    except OSError as copy_err:
                        logger.error(f"Anura Pooling: Failed to copy {code}: {copy_err}")
                else:
                    logger.error(f"Anura Pooling: Failed to link {code}: {e}")
            except AttributeError:
                # Fallback for systems where os.link might be missing
                try:
                    shutil.copy2(source_path, dest_path)
                except OSError as copy_err:
                    logger.error(f"Anura Pooling: Failed to copy {code}: {copy_err}")

    return f'--tessdata-dir "{pool_dir}" --psm 3 --oem 1'


# Thread-safe singleton instance for global app access
def get_language_manager() -> LanguageManager:
    """Get thread-safe language manager singleton."""
    return get_instance(LanguageManager)
