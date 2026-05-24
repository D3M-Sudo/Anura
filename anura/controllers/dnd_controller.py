# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

from loguru import logger

from anura.atomic_task_manager import get_atomic_manager
from anura.utils import validate_image_resource


class DndController:
    """
    Decoupled controller for Drag-and-Drop operations.
    """

    def __init__(self, window):
        self._window = window
        logger.debug("DndController: Initialized for AnuraWindow")

    def process_dnd_file_sync(self, file_path: str | None) -> None:
        """Process a dropped file with validation."""
        from gettext import gettext as _

        if not file_path:
            logger.error("DndController: Received invalid or null path.")
            self._window.welcome_page.reset_drop_area_state()
            self._window.show_toast(_("Failed to load dropped file (invalid path)."))
            return

        try:
            is_valid, _size, error = validate_image_resource(file_path)
            if not is_valid:
                logger.error(f"DndController OCR: {error}")
                self._window.welcome_page.reset_drop_area_state()
                self._window.show_toast(_(error) if error else _("Invalid image file"))
                return

            lang = self._window.get_language()
            get_atomic_manager().execute(self._window.backend.decode_image, (lang, file_path))

        except (OSError, RuntimeError, TypeError) as e:
            logger.error(f"DndController: Critical error accessing dropped file: {e}")
            self._window.welcome_page.reset_drop_area_state()
            self._window.show_toast(_("Failed to process the file."))

    def cleanup(self):
        """Explicit cleanup."""
        self._window = None
        logger.debug("DndController: Cleaned up")
