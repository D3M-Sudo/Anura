# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import gi

gi.require_version("Gtk", "4.0")

from gi.repository import Gtk


def announce_accessible(widget: Gtk.Widget, message: str, priority: object | None = None) -> bool:
    """Ask GTK to announce a concise status message for a mapped widget."""
    if not message or not widget.get_mapped():
        return False

    if priority is None:
        priority = Gtk.AccessibleAnnouncementPriority.MEDIUM

    widget.announce(message, priority)
    return True


def is_reduced_motion_enabled(settings: Gtk.Settings) -> bool:
    """Read the newest GTK reduced-motion preference with an older-version fallback."""
    reduced_motion = False
    if settings.find_property("gtk-interface-reduced-motion") is not None:
        reduced_motion = bool(settings.get_property("gtk-interface-reduced-motion"))

    animations_enabled = bool(settings.get_property("gtk-enable-animations"))
    return reduced_motion or not animations_enabled


def sync_reduced_motion_class(widget: Gtk.Widget, settings: Gtk.Settings) -> bool:
    """Apply the reduced-motion CSS class without changing desktop-wide settings."""
    reduced_motion = is_reduced_motion_enabled(settings)
    if reduced_motion:
        widget.add_css_class("reduced-motion")
    else:
        widget.remove_css_class("reduced-motion")
    return reduced_motion
