# This file is part of Anura.
# Copyright (C) 2022-2025 Andrey Maksimov (Frog)
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

from gi.repository import Gio, GLib
from loguru import logger

from anura.config import MAX_IMAGE_SIZE_BYTES, MAX_IMAGE_SIZE_MB


class WindowDnDMixin:
    """Mixin class for AnuraWindow to handle drag-and-drop logic."""

    def _setup_controllers(self) -> None:
        """Centralized event controller setup."""
        # Note: Drag and drop is now handled within the WelcomePage widget
        # to ensure better isolation and resolve potential race conditions.
        pass

    def process_dnd_file_sync(self, file_path: str | None) -> None:
        """Process a dropped file synchronously with explicit path validation."""
        from gettext import gettext as _
        import os

        if not file_path:
            logger.error("DnD: process_dnd_file_sync called with invalid or null path (None).")
            self.welcome_page.reset_drop_area_state()
            self.show_toast(_("Failed to load dropped file (invalid path)."))
            return

        logger.debug(f"DnD: Processing dropped file: {file_path}")

        try:
            # Hardening: check for missing or 0-byte physical files
            if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
                logger.error(f"Anura OCR: File missing or empty: {file_path}")
                self.welcome_page.reset_drop_area_state()
                self.show_toast(_("File not accessible or empty."))
                return

            # Validate file size
            file_size = os.path.getsize(file_path)
            if file_size > MAX_IMAGE_SIZE_BYTES:
                self.welcome_page.reset_drop_area_state()
                self.show_toast(
                    _("Image too large: {size}MB (max {max}MB)").format(
                        size=round(file_size / (1024 * 1024), 1),
                        max=MAX_IMAGE_SIZE_MB,
                    ),
                )
                return

            # Process image following Frog's pattern - pass path directly to decode_image
            lang = self.get_language()
            from anura.atomic_task_manager import get_atomic_manager

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
