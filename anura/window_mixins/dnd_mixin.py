# This file is part of Anura.
# Copyright (C) 2022-2025 Andrey Maksimov (Frog)
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

from gi.repository import Gio, GLib
from loguru import logger

from anura.atomic_task_manager import get_atomic_manager
from anura.utils import validate_image_resource


class WindowDnDMixin:
    """Mixin class for AnuraWindow to handle drag-and-drop logic.

    Requires the following template children on the main window:
    - welcome_page (WelcomePage): The page containing the drop target area.
    """

    def _setup_controllers(self) -> None:
        """Centralized event controller setup."""
        # Note: Drag and drop is now handled within the WelcomePage widget
        # to ensure better isolation and resolve potential race conditions.
        pass

    def process_dnd_file_sync(self, file_path: str | None) -> None:
        """Process a dropped file synchronously with explicit path validation."""
        from gettext import gettext as _

        if not file_path:
            logger.error("DnD: process_dnd_file_sync called with invalid or null path (None).")
            self.welcome_page.reset_drop_area_state()
            self.show_toast(_("Failed to load dropped file (invalid path)."))
            return

        logger.debug(f"DnD: Processing dropped file: {file_path}")

        try:
            # Security Hardening: Centralized validation for dropped files
            is_valid, _size, error = validate_image_resource(file_path)
            if not is_valid:
                logger.error(f"Anura OCR: {error}")
                self.welcome_page.reset_drop_area_state()
                self.show_toast(_(error) if error else _("Invalid image file"))
                return

            # Process image - pass path directly to decode_image
            lang = self.get_language()
            get_atomic_manager().execute(self.backend.decode_image, (lang, file_path))

        except (OSError, RuntimeError, TypeError) as e:
            logger.error(f"DnD: Critical error accessing dropped file: {e}")
            self.welcome_page.reset_drop_area_state()
            self.show_toast(_("Failed to process the file."))

    def process_gfile(self, gfile: Gio.File) -> bool:
        """Legacy method - kept for compatibility but deprecated."""
        logger.warning("DnD: process_gfile called, use process_dnd_file_sync instead")
        self.process_dnd_file_sync(gfile.get_path())
        return GLib.SOURCE_REMOVE
