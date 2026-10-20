# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

from gettext import gettext as _
from typing import ClassVar

import gi

# Set GTK version requirements before imports
gi.require_version("GObject", "2.0")

from gi.repository import GObject  # noqa: E402
from loguru import logger  # noqa: E402

from anura.services.clipboard_service import get_clipboard_service  # noqa: E402
from anura.utils.signal_manager import SignalManagerMixin  # noqa: E402


class HistoryController(GObject.GObject, SignalManagerMixin):
    """Coordinates actions on stored history entries (History V2).

    Logic-only: the controller never touches widgets. Outcomes are reported
    through GObject signals so ``AnuraWindow`` can surface them as toasts,
    the same way it does for ``OcrController`` and ``TtsController``.
    """

    __gtype_name__ = "HistoryController"

    __gsignals__: ClassVar[dict[str, tuple]] = {
        # The stored text was handed to the clipboard.
        "copied": (GObject.SignalFlags.RUN_LAST, None, ()),
        # Localised, user-facing message describing why an action failed.
        "error-occurred": (GObject.SignalFlags.RUN_LAST, None, (str,)),
    }

    def __init__(self, window: object) -> None:
        GObject.GObject.__init__(self)
        SignalManagerMixin.__init__(self)

        # Register for automatic teardown with the host window.
        if hasattr(window, "register_controller"):
            window.register_controller(self)

        logger.debug("HistoryController: Initialized")

    def copy_entry_text(self, text: str) -> bool:
        """Copy the stored text of a history entry to the system clipboard.

        Returns True only when the text reached the clipboard service; on any
        other outcome an ``error-occurred`` signal explains why and False is
        returned, so callers never show success feedback for a failed copy.
        """
        if not text:
            self.emit("error-occurred", _("No text to copy"))
            return False

        try:
            get_clipboard_service().set(text)
        except RuntimeError as e:
            # ClipboardService.clipboard raises RuntimeError when no GTK
            # display is available; anything else is a bug and must surface.
            logger.error(f"HistoryController: Clipboard unavailable: {e}")
            self.emit("error-occurred", _("Failed to copy text to clipboard"))
            return False

        self.emit("copied")
        return True

    def teardown(self) -> None:
        """Unified teardown called by SignalManagerMixin."""
        self.cleanup()

    def cleanup(self) -> None:
        """Explicit cleanup to prevent memory leaks."""
        try:
            self.disconnect_all_signals()
        except (TypeError, RuntimeError) as e:
            logger.debug(f"HistoryController: Signal disconnection omitted or failed during cleanup: {e}")
        logger.debug("HistoryController: Cleaned up and disconnected")
