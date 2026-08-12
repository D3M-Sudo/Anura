# This file is part of Anura.
# Copyright (C) 2022-2025 Andrey Maksimov (Frog)
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
import contextlib
import os
from pathlib import Path
import re
import shutil
import tempfile
import threading
import time
from typing import ClassVar

import gi

gi.require_version("GLib", "2.0")
gi.require_version("GObject", "2.0")
gi.require_version("Gio", "2.0")

from gi.repository import Gio, GLib, GObject  # noqa: E402
from loguru import logger  # noqa: E402
import requests  # noqa: E402

from anura.config import (  # noqa: E402
    LANG_CODE_PATTERN,
    MAX_MODEL_SIZE_BYTES,
    REQUEST_TIMEOUT,
    TESSDATA_BEST_URL,
    TESSDATA_DIR,
    TESSDATA_STANDARD_URL,
    TESSDATA_URL,
    USER_AGENT,
)
from anura.models.download_state import DownloadState  # noqa: E402
from anura.services.settings import settings  # noqa: E402


class DownloadManager(GObject.GObject):
    """
    Manages Tesseract language model downloads.
    Handles HTTP downloads, progress tracking, and atomic file installation.
    """

    __gtype_name__ = "DownloadManager"

    # Mapping for language codes whose Anura internal code differs from the actual
    # filename in the tessdata/tessdata_best repositories.
    _TESSDATA_FILENAME_MAPPING: ClassVar[dict[str, str]] = {}

    __gsignals__: ClassVar[dict[str, tuple]] = {
        "downloading": (GObject.SignalFlags.RUN_FIRST, None, (str, int)),
        "downloaded": (GObject.SignalFlags.RUN_FIRST, None, (str,)),
        "download-failed": (GObject.SignalFlags.RUN_FIRST, None, (str,)),
    }

    def __init__(self) -> None:
        super().__init__()
        self.loading_languages: dict[str, DownloadState] = {}
        self._download_executor: ThreadPoolExecutor | None = None
        self._cache_lock = threading.Lock()

        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})

        # Set retry logic
        adapter = requests.adapters.HTTPAdapter(
            max_retries=requests.adapters.Retry(
                total=3,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504],
            )
        )
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def _get_model_quality_dir(self, quality: str | None = None) -> str:
        """Get the directory for the specified model quality."""
        if quality is None:
            quality = settings.get_string("tessdata-model")

        base_dir = Path(TESSDATA_DIR)
        if quality == "best":
            return str(base_dir / "tessdata_best")
        if quality == "standard":
            return str(base_dir / "tessdata")
        return str(base_dir)

    def _get_model_quality_url(self, quality: str | None = None) -> str:
        """Get the GitHub base URL for the specified model quality."""
        if quality is None:
            quality = settings.get_string("tessdata-model")

        if quality == "best":
            return TESSDATA_BEST_URL
        if quality == "standard":
            return TESSDATA_STANDARD_URL
        return TESSDATA_URL

    def _get_download_executor(self) -> ThreadPoolExecutor:
        """Lazy initialization of the download executor."""
        with self._cache_lock:
            if self._download_executor is None:
                self._download_executor = ThreadPoolExecutor(
                    max_workers=1,
                    thread_name_prefix="AnuraDownloadWorker",
                )
            return self._download_executor

    def download(
        self,
        code: str,
        cancellable: Gio.Cancellable | None = None,
        on_started: Callable | None = None,
    ) -> None:
        """Thread-safe asynchronous download process.

        Args:
            code: Language code to download
            cancellable: Optional Gio.Cancellable for cancellation
            on_started: Optional callback when download starts
        """
        with self._cache_lock:
            if code in self.loading_languages:
                return
            self.loading_languages[code] = DownloadState()

        if on_started:
            def _on_started_idle(c):
                try:
                    on_started(c)
                except (AttributeError, RuntimeError, TypeError) as e:
                    logger.exception(f"Anura: Failed to call on_started for {c}: {e}")
                return GLib.SOURCE_REMOVE

            GLib.idle_add(_on_started_idle, code, priority=GLib.PRIORITY_DEFAULT)

        def download_done_wrapper(future) -> None:
            try:
                result_code = future.result()
            except (AttributeError, RuntimeError, TypeError, ValueError, OSError) as e:
                logger.error(f"Anura: Unexpected error during download of {code}: {e}")
                result_code = None

            def _on_done_idle():
                self.download_done(code, result_code)
                return GLib.SOURCE_REMOVE

            GLib.idle_add(_on_done_idle)

        future = self._get_download_executor().submit(
            self.download_begin,
            code,
            cancellable,
        )
        future.add_done_callback(download_done_wrapper)

    def download_begin(self, code: str, cancellable: Gio.Cancellable | None = None) -> str | None:
        """Performs the physical download of the .traineddata file atomically.

        Args:
            code: Language code to download
            cancellable: Optional Gio.Cancellable for cancellation

        Returns:
            The language code if successful, None otherwise
        """
        # Security: Validate lang_code is a valid ISO 639-2 code
        if not code or not re.match(LANG_CODE_PATTERN, code):
            logger.error(f"Anura: Blocked invalid language code download attempt: '{code}'")
            return None

        # Hardening: verify Tesseract binary availability before downloading models
        tess_bin = os.environ.get("TESSERACT_CMD", "tesseract")
        if not shutil.which(tess_bin):
            logger.error(f"Anura: Cannot download '{code}'; Tesseract binary not found.")
            return None

        # Use filename mapping for language codes with different filenames
        filename_code = self._TESSDATA_FILENAME_MAPPING.get(code, code)

        # Validate filename is safe to prevent path traversal attacks
        if not re.match(r"^[a-zA-Z0-9_-]+$", filename_code):
            logger.error(f"Anura: Unsafe language code '{code}' -> '{filename_code}'")
            return None

        quality = settings.get_string("tessdata-model")
        tessfile = f"{filename_code}.traineddata"
        quality_dir_str = self._get_model_quality_dir(quality)
        quality_dir = Path(quality_dir_str)

        # Security: Ensure quality-specific tessdata directories have restrictive permissions (0700)
        quality_dir.mkdir(parents=True, exist_ok=True)
        with contextlib.suppress(OSError):
            quality_dir.chmod(0o700)

        final_path = quality_dir / f"{code}.traineddata"
        tmp_path = None

        url_base = self._get_model_quality_url(quality)
        try:
            url = url_base + tessfile
            with tempfile.NamedTemporaryFile(
                dir=quality_dir,
                suffix=".tmp",
                delete=False,
            ) as tmp:
                tmp_path = Path(tmp.name)

                try:
                    # Use central session with consistent headers and timeout
                    response = self.session.get(url, timeout=REQUEST_TIMEOUT, stream=True)
                    response.raise_for_status()

                    try:
                        total_size = int(response.headers.get("content-length", 0))
                    except (ValueError, TypeError):
                        total_size = 0

                    # Security: Enforce download size limit via Content-Length header (DoS prevention)
                    if total_size > MAX_MODEL_SIZE_BYTES:
                        logger.error(
                            f"Anura: Blocked oversized model download: {total_size} bytes "
                            f"(max {MAX_MODEL_SIZE_BYTES})"
                        )
                        return None

                    downloaded = 0

                    # Throttle progress updates to prevent main loop saturation
                    last_progress_time = time.monotonic()
                    last_progress_value = 0

                    with tmp_path.open("wb") as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if cancellable and cancellable.is_cancelled():
                                logger.debug(f"Anura: Download of {code} cancelled")
                                return None
                            if chunk:
                                f.write(chunk)
                                downloaded += len(chunk)

                                # Security: Monitor cumulative downloaded bytes
                                if downloaded > MAX_MODEL_SIZE_BYTES:
                                    logger.error(
                                        f"Anura: Aborted oversized model download (stream): {downloaded} bytes "
                                        f"(max {MAX_MODEL_SIZE_BYTES})"
                                    )
                                    return None

                                # Throttle progress updates (max 10/sec)
                                now = time.monotonic()
                                if now - last_progress_time >= 0.1:  # 100ms throttle
                                    with self._cache_lock:
                                        if code in self.loading_languages:
                                            state = self.loading_languages[code]
                                            state.total = total_size
                                            state.progress = downloaded

                                    if total_size > 0:
                                        progress = int(downloaded * 100 / total_size)
                                        if progress != last_progress_value:
                                            def _on_progress_idle(c, p):
                                                try:
                                                    self.emit("downloading", c, p)
                                                except (AttributeError, RuntimeError, TypeError) as e:
                                                    logger.error(f"Anura: Failed to emit 'downloading' for {c}: {e}")
                                                return GLib.SOURCE_REMOVE

                                            GLib.idle_add(
                                                _on_progress_idle,
                                                code,
                                                min(progress, 100),
                                                priority=GLib.PRIORITY_DEFAULT,
                                            )
                                            last_progress_value = progress
                                    else:
                                        # No content-length header, emit indeterminate progress
                                        def _on_progress_idle(c, _):
                                            try:
                                                self.emit("downloading", c, -1)
                                            except (AttributeError, RuntimeError, TypeError) as e:
                                                logger.error(f"Anura: Failed to emit 'downloading' for {c}: {e}")
                                            return GLib.SOURCE_REMOVE

                                        GLib.idle_add(_on_progress_idle, code, -1, priority=GLib.PRIORITY_DEFAULT)
                                    last_progress_time = now

                    # Use copy+delete for cross-filesystem compatibility
                    try:
                        shutil.copy2(tmp_path, final_path)
                        return code
                    except (OSError, shutil.Error) as e:
                        logger.error(f"Anura: Failed to install language file: {e}")
                        return None

                finally:
                    # Ensure temporary file is always cleaned up
                    if tmp_path and tmp_path.exists():
                        try:
                            tmp_path.unlink()
                            tmp_path = None
                        except OSError:
                            logger.warning(f"Anura: Failed to clean up temporary file: {tmp_path}")

        except (requests.RequestException, OSError) as e:
            logger.warning(f"Anura: download failed from {url_base}: {e}")

        logger.error(f"Anura: Failed to download model '{code}' from all sources.")
        return None

    def download_done(self, requested_code: str, result_code: str | None) -> None:
        """Thread-safe callback when download completes.

        Args:
            requested_code: The language code that was requested for download
            result_code: The returned code from download_begin (None if failed)
        """
        with self._cache_lock:
            if requested_code in self.loading_languages:
                self.loading_languages.pop(requested_code)

            if result_code:
                def _on_downloaded_idle(c):
                    try:
                        self.emit("downloaded", c)
                    except (AttributeError, RuntimeError, TypeError) as e:
                        logger.exception(f"Anura: Failed to emit 'downloaded' for {c}: {e}")
                    return GLib.SOURCE_REMOVE

                GLib.idle_add(_on_downloaded_idle, result_code, priority=GLib.PRIORITY_DEFAULT)
            else:
                def _on_failed_idle(c):
                    try:
                        self.emit("download-failed", c)
                    except (AttributeError, RuntimeError, TypeError) as e:
                        logger.exception(f"Anura: Failed to emit 'download-failed' for {c}: {e}")
                    return GLib.SOURCE_REMOVE

                GLib.idle_add(_on_failed_idle, requested_code, priority=GLib.PRIORITY_DEFAULT)

    def shutdown(self) -> None:
        """Shut down the download executor."""
        with self._cache_lock:
            executor = self._download_executor
            self._download_executor = None

        if executor is not None:
            executor.shutdown(wait=False, cancel_futures=True)

    def get_download_state(self, code: str) -> DownloadState | None:
        """Get the current download state for a language code.

        Args:
            code: Language code

        Returns:
            DownloadState if downloading, None otherwise
        """
        with self._cache_lock:
            return self.loading_languages.get(code)
