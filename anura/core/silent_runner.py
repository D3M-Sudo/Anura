# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

from collections.abc import Callable
import signal as sig
import threading
from types import FrameType
from typing import Any

from gi.repository import GLib
from loguru import logger

from anura.services.clipboard_service import get_clipboard_service

_SignalHandler = sig.Handlers | Callable[[int, FrameType | None], Any] | int | None

# How long the silent process keeps serving the clipboard when no clipboard manager took
# the text over (the text is only pasteable while the process is alive).
_CLIPBOARD_LINGER_SECONDS = 30


class SilentRunner:
    """Headless engine for running OCR without UI."""

    def __init__(self, app, file_path: str):
        self.app = app
        self.file_path = file_path
        self.interrupted = threading.Event()
        self._old_handlers: dict[str, _SignalHandler] = {}

    def run(self) -> int:
        """Execute OCR in silent mode and return exit code."""
        self._setup_signal_handlers()
        try:
            return self._execute_silent_ocr()
        finally:
            self._restore_signal_handlers()

    def _setup_signal_handlers(self):
        def on_signal(signum, _frame):
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
        self._ocr_success = False
        self._timed_out = False

        def check_interrupted(*_args):
            if self.interrupted.is_set():
                loop.quit()
                return False
            return True

        check_source = GLib.timeout_source_new(100)
        check_source.set_callback(check_interrupted)
        check_source.attach(ctx)
        sources.append(check_source)

        def do_ocr(*_args):
            if self.interrupted.is_set():
                loop.quit()
                return False

            try:
                success, text, error_message, ocr_result, _applied_name = (
                    self.app._decode_image_synchronously(self.file_path)
                )

                if self.interrupted.is_set():
                    loop.quit()
                    return False

                if success and text:
                    # Headless/Silent mode: perform direct dispatching
                    from anura.models.ocr import OcrResult
                    from anura.services.result_dispatcher import get_result_dispatcher

                    result = get_result_dispatcher().dispatch(
                        text, ocr_result if isinstance(ocr_result, OcrResult) else None
                    )

                    get_clipboard_service().set(result.text)
                    self._ocr_success = True
                    logger.info("Anura: OCR completed successfully in silent mode.")
                else:
                    logger.error(f"Anura: Silent mode failed: {error_message}")
            except (RuntimeError, OSError) as e:
                logger.error(f"Anura: Silent mode unexpected error: {e}")

            loop.quit()
            return False

        idle_source = GLib.idle_source_new()
        idle_source.set_callback(do_ocr)
        idle_source.attach(ctx)
        sources.append(idle_source)

        def on_timeout(*_args):
            logger.error("Anura: Silent mode timed out after 60 seconds.")
            self._timed_out = True
            loop.quit()
            return False

        # 60s timeout
        timeout_source = GLib.timeout_source_new_seconds(60)
        timeout_source.set_callback(on_timeout)
        timeout_source.attach(ctx)
        sources.append(timeout_source)

        if not ctx.acquire():
            logger.error("Anura: Could not acquire GLib MainContext for silent mode.")
            return 1

        ctx.push_thread_default()
        try:
            loop.run()
        finally:
            ctx.pop_thread_default()
            ctx.release()

        for source in sources:
            source.destroy()

        if self.interrupted.is_set():
            return 130
        if self._timed_out:
            return 124  # Standard timeout exit code
        if not self._ocr_success:
            return 1

        self._keep_clipboard_available()
        return 0

    def _keep_clipboard_available(self) -> None:
        """Make sure the copied text is still pasteable after this process exits.

        The clipboard belongs to the process that set it: exiting right after set() leaves
        nothing to paste unless a clipboard manager took the text over. Hand it to the
        manager if there is one; otherwise keep serving it until another application copies
        something or the linger timeout expires. A signal during the wait just ends it: the
        OCR already succeeded.

        The wait must iterate the *default* main context: GDK answers paste requests from
        there, while the OCR loop above iterates a private context (checked: a process that
        only iterates a private context cannot be pasted from, even while it is alive).
        """
        service = get_clipboard_service()
        if service.hand_off_to_manager():
            logger.info("Anura: Clipboard content handed over to the clipboard manager.")
            return

        logger.info(
            f"Anura: No clipboard manager; serving the clipboard for up to {_CLIPBOARD_LINGER_SECONDS}s "
            "or until another application replaces it."
        )
        if service.wait_until_replaced(_CLIPBOARD_LINGER_SECONDS, self.interrupted.is_set):
            logger.info("Anura: Clipboard replaced by another application, exiting.")
