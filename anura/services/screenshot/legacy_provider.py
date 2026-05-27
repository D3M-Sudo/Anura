# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

from collections.abc import Callable
import os
import uuid

from gi.repository import Gio, GLib
from loguru import logger

from .base import ScreenshotProvider


class LegacyX11Provider(ScreenshotProvider):
    """Legacy screenshot provider using scrot on X11."""

    def is_available(self) -> bool:
        # Only available on X11
        return bool(os.environ.get("DISPLAY")) and not bool(os.environ.get("WAYLAND_DISPLAY"))

    def capture(self, lang: str, copy: bool, callback: Callable) -> None:
        output_path = f"/tmp/anura-shot-{uuid.uuid4().hex}.png"
        argv = ["scrot", "-s", output_path]

        logger.info(f"LegacyX11Provider: Spawning scrot: {' '.join(argv)}")
        try:
            proc = Gio.Subprocess.new(
                argv,
                Gio.SubprocessFlags.STDERR_PIPE | Gio.SubprocessFlags.STDOUT_PIPE,
            )
            proc.wait_async(None, self._on_finish, (callback, output_path))
        except (AttributeError, RuntimeError, OSError) as e:
            logger.error(f"LegacyX11Provider: Failed to spawn scrot: {e}")
            callback(False, None, str(e))

    def _on_finish(self, proc, res, user_data):
        callback, output_path = user_data
        try:
            proc.wait_finish(res)
            if proc.get_exit_status() == 0:
                uri = GLib.filename_to_uri(output_path, None)
                callback(True, uri, None)
            else:
                callback(False, None, "Screenshot tool exited with error or was cancelled.")
        except (AttributeError, RuntimeError, OSError) as e:
            logger.error(f"LegacyX11Provider: Error waiting for process: {e}")
            callback(False, None, str(e))
