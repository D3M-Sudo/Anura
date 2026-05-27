# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

from collections.abc import Callable
import os
import shutil
import threading
import time
import uuid

from gi.repository import Gio, GLib
from loguru import logger

from .base import ScreenshotProvider

# Flatpak bundles scrot at this fixed path (declared in the Flatpak manifest).
# On a plain host install scrot lives somewhere in PATH — shutil.which() handles that.
_FLATPAK_SCROT_BIN = "/app/bin/scrot"

# Retry parameters for waiting for scrot to flush its output file to disk.
# scrot exits before the filesystem has necessarily flushed the PNG, so we
# poll briefly rather than assuming the file is ready immediately.
_FILE_READY_RETRIES = 10
_FILE_READY_DELAY_S = 0.1  # 100 ms between retries


def _resolve_scrot_binary() -> str | None:
    """Return the absolute path to the scrot binary, or None if not found.

    Priority order:
    1. Flatpak bundled path (/app/bin/scrot) — always preferred inside the sandbox
       because it is the version pinned in the manifest and guaranteed to be there.
    2. System PATH — for host/development installs where scrot is installed globally.
    """
    if os.path.isfile(_FLATPAK_SCROT_BIN) and os.access(_FLATPAK_SCROT_BIN, os.X_OK):
        return _FLATPAK_SCROT_BIN
    return shutil.which("scrot")


class LegacyX11Provider(ScreenshotProvider):
    """X11 screenshot fallback using the bundled scrot utility.

    Activated only when xdg-desktop-portal's Screenshot interface is unavailable
    (e.g. LXQt, Openbox, bare X11 sessions) and DISPLAY is set without
    WAYLAND_DISPLAY, so the sandboxed scrot can read the root window directly via
    the ``--socket=x11`` Flatpak permission.
    """

    def __init__(self) -> None:
        self._proc: Gio.Subprocess | None = None
        self._cancellable: Gio.Cancellable | None = None
        self._lock = threading.Lock()

    def is_available(self) -> bool:
        """Available only on X11 (not Wayland) and only when scrot is reachable."""
        if not os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"):
            return False
        return _resolve_scrot_binary() is not None

    def cancel(self) -> None:
        """Interrupt an in-flight scrot capture."""
        with self._lock:
            if self._cancellable is not None and not self._cancellable.is_cancelled():
                self._cancellable.cancel()
                logger.debug("LegacyX11Provider: Cancelled in-flight scrot capture.")
            self._cancellable = None

    def capture(self, lang: str, copy: bool, callback: Callable) -> None:
        """Spawn scrot interactively and call callback(success, uri, error)."""
        scrot_bin = _resolve_scrot_binary()
        if scrot_bin is None:
            # Should not happen if is_available() was checked first, but be safe.
            logger.error("LegacyX11Provider: scrot binary not found at capture time.")
            callback(False, None, "scrot not found")
            return

        output_path = f"/tmp/anura-shot-{uuid.uuid4().hex}.png"
        argv = [scrot_bin, "-s", output_path]

        logger.info(f"LegacyX11Provider: Spawning scrot from '{scrot_bin}'")

        cancellable = Gio.Cancellable.new()
        with self._lock:
            self._cancellable = cancellable

        try:
            proc = Gio.Subprocess.new(
                argv,
                Gio.SubprocessFlags.STDERR_PIPE | Gio.SubprocessFlags.STDOUT_PIPE,
            )
            with self._lock:
                self._proc = proc
        except GLib.Error as e:
            logger.error(f"LegacyX11Provider: Failed to spawn scrot: {e.message}")
            with self._lock:
                self._cancellable = None
            callback(False, None, e.message)
            return
        except Exception as e:
            logger.error(f"LegacyX11Provider: Failed to spawn scrot: {e}")
            with self._lock:
                self._cancellable = None
            callback(False, None, str(e))
            return

        proc.wait_async(cancellable, self._on_finish, (callback, output_path))

    def _on_finish(
        self,
        proc: Gio.Subprocess,
        res: Gio.AsyncResult,
        user_data: tuple,
    ) -> None:
        callback, output_path = user_data

        with self._lock:
            self._proc = None
            self._cancellable = None

        # --- 1. Collect exit status ---
        try:
            proc.wait_finish(res)
        except GLib.Error as e:
            if e.matches(Gio.io_error_quark(), Gio.IOErrorEnum.CANCELLED):
                logger.debug("LegacyX11Provider: scrot capture cancelled.")
                self._cleanup_file(output_path)
                callback(False, None, None)
                return
            logger.error(f"LegacyX11Provider: Error waiting for scrot process: {e.message}")
            self._cleanup_file(output_path)
            callback(False, None, e.message)
            return
        except Exception as e:
            logger.error(f"LegacyX11Provider: Error waiting for scrot process: {e}")
            self._cleanup_file(output_path)
            callback(False, None, str(e))
            return

        # --- 2. Non-zero exit = user pressed Esc / tool error ---
        if not proc.get_if_exited() or proc.get_exit_status() != 0:
            exit_status = proc.get_exit_status() if proc.get_if_exited() else -1
            logger.info(
                f"LegacyX11Provider: scrot exited with status {exit_status} — "
                "user likely cancelled the selection."
            )
            self._cleanup_file(output_path)
            # Treat non-zero exit as user cancellation (None error = no error toast)
            callback(False, None, None)
            return

        # --- 3. Retry loop: wait for filesystem to flush the PNG ---
        # scrot may exit before the OS has written all bytes to disk.
        file_ready = False
        for attempt in range(_FILE_READY_RETRIES):
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                file_ready = True
                break
            if attempt < _FILE_READY_RETRIES - 1:
                time.sleep(_FILE_READY_DELAY_S)

        if not file_ready:
            logger.warning(
                f"LegacyX11Provider: scrot exited 0 but produced no output after "
                f"{_FILE_READY_RETRIES} retries (path={output_path})."
            )
            self._cleanup_file(output_path)
            callback(False, None, "Screenshot tool produced no output.")
            return

        # --- 4. Success: convert path to file:// URI for the OCR pipeline ---
        try:
            uri = GLib.filename_to_uri(output_path, None)
        except GLib.Error as e:
            logger.error(f"LegacyX11Provider: Failed to build URI for '{output_path}': {e.message}")
            self._cleanup_file(output_path)
            callback(False, None, e.message)
            return

        logger.info(f"LegacyX11Provider: scrot capture successful → {output_path}")
        callback(True, uri, None)

    @staticmethod
    def _cleanup_file(path: str) -> None:
        """Best-effort removal of a temporary screenshot file."""
        if path and os.path.exists(path):
            try:
                os.unlink(path)
                logger.debug(f"LegacyX11Provider: Cleaned up temp file: {path}")
            except OSError as e:
                logger.debug(f"LegacyX11Provider: Cleanup failed for '{path}': {e}")
