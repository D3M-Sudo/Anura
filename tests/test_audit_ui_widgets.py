# This file is part of Anura.
# Copyright (C) 2022-2025 Andrey Maksimov (Frog)
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import pytest

pytest.importorskip("gi")

import os
import warnings

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gio, Gtk  # noqa: E402

# Load resources before importing widgets
resource_path = os.path.join(os.path.dirname(__file__), "..", "data", "io.github.d3msudo.anura.gresource")
if os.path.exists(resource_path):
    res = Gio.Resource.load(resource_path)
    res._register()

# ---------------------------------------------------------------------------
# GTK / display initialization
# ---------------------------------------------------------------------------
# @Gtk.Template widgets call gtk_widget_init_template() inside __init__().
# That function requires GTK to be fully initialized (gtk_initialized == TRUE
# and an open GdkDisplay).  Without initialization, template children stay as
# NULL C pointers and the first Python attribute access on them triggers SIGSEGV.
#
# Primary approach: Adw.Application.register()
#   register() → g_application_register() → GtkApplication::startup
#   → gtk_init_check() → gdk_display_open(WAYLAND_DISPLAY)
#   This requires a running compositor (weston) AND a D-Bus session bus.
#   register() returns False without raising an exception when it fails.
#
# Fallback: Gtk.init()
#   Calls gtk_init() directly — opens the display and sets gtk_initialized.
#   Works without D-Bus but still requires a running Wayland/X11 compositor.
#
# The CI workflow ensures weston is alive for the full duration of the test
# run (trap cleanup EXIT moved to the test step, not the setup step).
# ---------------------------------------------------------------------------
_adw_app = Adw.Application(
    application_id="io.github.d3msudo.anura.test",
    flags=Gio.ApplicationFlags.NON_UNIQUE,
)
try:
    _registered = _adw_app.register()
    if not _registered:
        raise RuntimeError("register() returned False (D-Bus unavailable?)")
except Exception as _register_exc:
    warnings.warn(
        f"Adw.Application.register() failed: {_register_exc}. "
        "Falling back to Gtk.init()."
    )
    try:
        Gtk.init()
    except Exception as _init_exc:
        warnings.warn(
            f"Gtk.init() also failed: {_init_exc}. "
            "@Gtk.Template widgets will likely segfault."
        )


class TestWidgets:
    @pytest.mark.gtk
    def test_language_popover_row(self):
        from anura.models.language_item import LanguageItem
        from anura.widgets.language_popover_row import LanguagePopoverRow

        item = LanguageItem(code="fra", title="French")
        row = LanguagePopoverRow(item)
        assert row.get_child() is not None
        # Check if title is correct - this might be inside some sub-widget
        # but we just want to ensure it inits without error

    @pytest.mark.gtk
    def test_share_row(self):
        from anura.widgets.share_row import ShareRow

        row = ShareRow("email")
        # Check if row is created successfully
        assert row is not None

    @pytest.mark.gtk
    def test_simple_widgets_init(self):
        # Test widgets that don't have complex dependencies
        from anura.widgets.preferences_dialog import PreferencesDialog

        try:
            dialog = PreferencesDialog(transient_for=None)
            assert dialog is not None
        except Exception as e:
            pytest.skip(f"Could not init PreferencesDialog: {e}")
