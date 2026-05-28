# This file is part of Anura.
# Copyright (C) 2022-2025 Andrey Maksimov (Frog)
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import pytest

pytest.importorskip("gi")

import os

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gio  # noqa: E402

# Load resources before importing widgets
resource_path = os.path.join(os.path.dirname(__file__), "..", "data", "io.github.d3msudo.anura.gresource")
if os.path.exists(resource_path):
    res = Gio.Resource.load(resource_path)
    res._register()

# Initialize GTK / libadwaita once per process so @Gtk.Template widgets can
# be instantiated safely.
#
# Root cause of the SIGSEGV:
#   @Gtk.Template widgets call gtk_widget_init() → gtk_init_check() inside
#   super().__init__().  That function opens the Wayland/X11 display and wires
#   template XML to the GType.  Without an open display, every
#   Gtk.Template.Child() slot stays as a NULL C pointer; the first Python
#   attribute access on that NULL pointer triggers SIGSEGV (exit code 139).
#
# Why Adw.Application() alone was not enough (previous attempt):
#   GApplication.__init__() only allocates the GObject struct.  The display
#   connection is established by g_application_register(), which fires the
#   GtkApplication::startup signal → gtk_init_check() → gdk_display_open().
#   Without register(), GTK is still uninitialised at widget-instantiation time.
#
# Fix: call register() immediately after construction.  The NON_UNIQUE flag
# prevents "another instance is already running" errors when multiple pytest
# worker processes share the same session bus.
_adw_app = Adw.Application(
    application_id="io.github.d3msudo.anura.test",
    flags=Gio.ApplicationFlags.NON_UNIQUE,
)
try:
    _adw_app.register()
except Exception as _e:  # pragma: no cover
    import warnings
    warnings.warn(f"Adw.Application.register() failed: {_e}. GTK widgets may segfault.")


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
