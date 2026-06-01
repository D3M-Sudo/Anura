# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

from collections.abc import Callable
import contextlib
from gettext import gettext as _
import os
from pathlib import Path
import tempfile
import threading
import uuid

from gi.repository import Gio, GLib
from loguru import logger
import mss

from .base import ScreenshotProvider


class MssScreenshotProvider(ScreenshotProvider):
    """X11 screenshot fallback using the mss library.

    This provider uses the pure-Python mss library to capture screenshots on X11.
    It is sandbox-friendly (doesn't require breakout) and more robust than
    bundled X11 binaries in many environments.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()

    def is_available(self) -> bool:
        """Available only on X11 (not Wayland)."""
        # mss requires DISPLAY to be set and fails or behaves unexpectedly on Wayland
        # without an XWayland bridge, but even then Portal is preferred.
        return bool(os.environ.get("DISPLAY")) and not os.environ.get("WAYLAND_DISPLAY")

    def cancel(self) -> None:
        """mss capture is synchronous but fast, no specific cancel needed for the capture itself."""
        pass

    def capture(self, lang: str, copy: bool, callback: Callable) -> None:
        """Perform screenshot capture using mss."""
        logger.info("MssScreenshotProvider: Capturing full screen (X11 fallback)")

        # Create a temporary file with restrictive permissions
        try:
            fd, output_path = tempfile.mkstemp(prefix="anura-mss-", suffix=".png")
            os.close(fd)
        except OSError as e:
            logger.error(f"MssScreenshotProvider: Failed to create temporary file: {e}")
            callback(False, None, _("Failed to create temporary file."))
            return

        # mss operations should stay off the main thread to avoid UI stutters
        threading.Thread(
            target=self._capture_worker,
            args=(output_path, callback),
            daemon=True
        ).start()

    def _capture_worker(self, output_path: str, callback: Callable) -> None:
        try:
            with mss.mss() as sct:
                # Capture the primary monitor
                # Note: For a fallback, capturing the whole screen is usually the safest
                # consistent behavior when interactive selection tools fail.
                sct.shot(mon=-1, output=output_path)

            # Success!
            if Path(output_path).exists() and Path(output_path).stat().st_size > 0:
                uri = GLib.filename_to_uri(output_path, None)
                logger.info(f"MssScreenshotProvider: Capture successful → {output_path}")
                GLib.idle_add(callback, True, uri, None)
            else:
                logger.error("MssScreenshotProvider: Capture failed, no file produced.")
                GLib.idle_add(callback, False, None, _("Failed to capture screenshot."))
                self._cleanup_file(output_path)

        except Exception as e:
            logger.exception(f"MssScreenshotProvider: Error during capture: {e}")
            GLib.idle_add(callback, False, None, str(e))
            self._cleanup_file(output_path)

    @staticmethod
    def _cleanup_file(path: str) -> None:
        """Best-effort removal of a temporary screenshot file."""
        if path:
            p = Path(path)
            if p.exists():
                try:
                    p.unlink()
                except OSError:
                    pass
