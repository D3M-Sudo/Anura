# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import os

import pytest


@pytest.mark.gtk
def test_icons_used_by_extracted_and_history_exist_in_gnome_51_runtime():
    if os.environ.get("ANURA_GNOME_RUNTIME_ICON_CHECK") != "1":
        pytest.skip("Run only inside the GNOME 51 runtime validation job")

    gi = pytest.importorskip("gi")
    gi.require_version("Gtk", "4.0")
    from gi.repository import Gdk, Gtk

    Gtk.init()
    display = Gdk.Display.get_default()
    assert display is not None, "GNOME 51 icon test requires a display (Xvfb is sufficient)"

    theme = Gtk.IconTheme.get_for_display(display)
    required_icons = (
        "edit-copy-symbolic",
        "emblem-ok-symbolic",
        "object-select-symbolic",
    )
    missing = [name for name in required_icons if not theme.has_icon(name)]
    assert not missing, f"GNOME 51 icon theme is missing icons used by Extracted/History: {missing}"
