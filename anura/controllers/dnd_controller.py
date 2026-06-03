# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

from gi.repository import GObject
from loguru import logger

from anura.utils import validate_image_resource
from anura.utils.signal_manager import SignalManagerMixin


class DndController(GObject.GObject, SignalManagerMixin):
    """
    Decoupled controller for Drag-and-Drop operations.
    """

    __gsignals__: ClassVar[dict[str, tuple]] = {
        "processing-started": (GObject.SignalFlags.RUN_LAST, None, ()),
        "processing-finished": (GObject.SignalFlags.RUN_LAST, None, ()),
        "error-occurred": (GObject.SignalFlags.RUN_LAST, None, (str,)),
    }

    def __init__(self, window):
        GObject.GObject.__init__(self)
        SignalManagerMixin.__init__(self)
        import weakref

        self._window = weakref.proxy(window)

        # Register for automatic teardown
        if hasattr(window, "register_controller"):
            window.register_controller(self)

        logger.debug("DndController: Initialized for AnuraWindow")

    def process_dnd_file_sync(self, file_path: str | None) -> None:
        """Process a dropped file with validation."""
        from gettext import gettext as _

        if not file_path:
            logger.error("DndController: Received invalid or null path.")
            self.emit("error-occurred", _("Failed to load dropped file (invalid path)."))
            return

        try:
            is_valid, _size, error = validate_image_resource(file_path)
            if not is_valid:
                logger.error(f"DndController OCR: {error}")
                self.emit("error-occurred", _(error) if error else _("Invalid image file"))
                return

            lang = self._window.get_language()
            # BUG-029: nested task cancellation. decode_image() internally calls
            # execute_isolated(), which cancels the active task on the manager.
            # If we wrap it in another execute() call here, the inner call
            # cancels the outer one, leading to InterruptedError.
            # We call decode_image() directly (it handles its own thread/process dispatching).
            self._window.backend.decode_image(lang, file_path)

        except (OSError, RuntimeError, TypeError) as e:
            logger.error(f"DndController: Critical error accessing dropped file: {e}")
            self.emit("error-occurred", _("Failed to process the file."))

    def teardown(self) -> None:
        """Unified teardown called by SignalManagerMixin."""
        self.cleanup()

    def cleanup(self):
        """Explicit cleanup to prevent memory leaks."""
        try:
            self.disconnect_all_signals()
        except (TypeError, RuntimeError) as e:
            logger.debug(f"Signal disconnection omitted or failed during cleanup: {e}")
        self._window = None
        logger.debug("DndController: Cleaned up")
