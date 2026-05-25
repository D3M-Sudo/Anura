# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import signal as sig
import threading

from gi.repository import GLib
from loguru import logger

from anura.services.clipboard_service import get_clipboard_service


class SilentRunner:
    """Headless engine for running OCR without UI."""

    def __init__(self, app, file_path: str):
        self.app = app
        self.file_path = file_path
        self.interrupted = threading.Event()
        self._old_handlers = {}

    def run(self) -> int:
        """Execute OCR in silent mode and return exit code."""
        self._setup_signal_handlers()
        try:
            return self._execute_silent_ocr()
        finally:
            self._restore_signal_handlers()

    def _setup_signal_handlers(self):
        def on_signal(signum, frame):
            logger.info(f"Anura: Received signal {signum}, shutting down silently...")
            self.interrupted.set()

        self._old_handlers["sigint"] = sig.signal(sig.SIGINT, on_signal)
        self._old_handlers["sigterm"] = sig.signal(sig.SIGTERM, on_signal)

    def _restore_signal_handlers(self):
        sig.signal(sig.SIGINT, self._old_handlers.get("sigint", sig.SIG_DFL))
        sig.signal(sig.SIGTERM, self._old_handlers.get("sigterm", sig.SIG_DFL))

    def _execute_silent_ocr(self) -> int:
        ctx = GLib.MainContext.new()
        loop = GLib.MainLoop.new(ctx, False)
        sources = []

        def check_interrupted():
            if self.interrupted.is_set():
                loop.quit()
                return False
            return True

        check_source = GLib.timeout_source_new(100)
        check_source.set_callback(check_interrupted)
        check_source.attach(ctx)
        sources.append(check_source)

        def do_ocr():
            if self.interrupted.is_set():
                loop.quit()
                return False

            try:
                success, text, error_message, _ = self.app._decode_image_synchronously(self.file_path)

                if self.interrupted.is_set():
                    loop.quit()
                    return False

                if success and text:
                    get_clipboard_service().set(text)
                    logger.info("Anura: OCR completed successfully in silent mode.")
                else:
                    logger.error(f"Anura: Silent mode failed: {error_message}")
            except Exception as e:
                logger.exception(f"Anura: Silent mode unexpected error: {e}")

            loop.quit()
            return False

        idle_source = GLib.idle_source_new()
        idle_source.set_callback(do_ocr)
        idle_source.attach(ctx)
        sources.append(idle_source)

        # 60s timeout
        timeout_source = GLib.timeout_source_new_seconds(60)
        timeout_source.set_callback(lambda: loop.quit() or False)
        timeout_source.attach(ctx)
        sources.append(timeout_source)

        if not ctx.acquire():
            logger.error("Anura: Could not acquire GLib MainContext for silent mode.")
            return 1

        ctx.push()
        try:
            loop.run()
        finally:
            ctx.pop()
            ctx.release()

        for source in sources:
            source.destroy()

        return 130 if self.interrupted.is_set() else 0
