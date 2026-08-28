# This file is part of Anura.
# Copyright (C) 2022-2025 Andrey Maksimov (Frog)
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

from typing import ClassVar

try:
    from gi.repository import Gio, GLib
    HAS_GIO = True
except ImportError:
    HAS_GIO = False
    Gio = None
    GLib = None


class NotificationHelpers:
    """
    Helper utilities for notification formatting and validation.
    """

    # Valid priority levels according to XDG Portal specification
    VALID_PRIORITIES: ClassVar[set[str]] = {"low", "normal", "high", "urgent"}

    @staticmethod
    def validate_priority(priority: str) -> str:
        """
        Validate and normalize priority parameter.

        Args:
            priority: Priority level to validate

        Returns:
            Valid priority string (defaults to "normal" if invalid)
        """
        if priority not in NotificationHelpers.VALID_PRIORITIES:
            return "normal"
        return priority

    @staticmethod
    def escape_markup(text: str) -> str:
        """
        Escape Pango markup to prevent injection attacks from OCR'd text.

        Args:
            text: Text to escape

        Returns:
            Escaped text, or original if GLib is unavailable
        """
        if GLib is None:
            return text
        return GLib.markup_escape_text(text)

    @staticmethod
    def map_priority_to_gio(priority: str) -> Gio.NotificationPriority | None:
        """
        Map priority string to Gio.NotificationPriority enum.

        Args:
            priority: Priority string ("low", "normal", "high", "urgent")

        Returns:
            Gio.NotificationPriority enum value, or None if Gio unavailable
        """
        if not HAS_GIO:
            return None

        priority_map = {
            "low": Gio.NotificationPriority.LOW,
            "normal": Gio.NotificationPriority.NORMAL,
            "high": Gio.NotificationPriority.HIGH,
            "urgent": Gio.NotificationPriority.URGENT,
        }
        return priority_map.get(priority, Gio.NotificationPriority.NORMAL)
