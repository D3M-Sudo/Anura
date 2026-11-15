# This file is part of Anura.
# Copyright (C) 2022-2025 Andrey Maksimov (Frog)
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import pytest

pytest.importorskip("gi")

import atexit
import os
import warnings

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gio, GLib, Gtk  # noqa: E402

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
    # Application registration starts GLib/GDBus threads that can keep the
    # test process alive during interpreter shutdown. Stop the application
    # through atexit so those threads can exit cleanly.
    atexit.register(_adw_app.quit)
except Exception as _register_exc:
    warnings.warn(f"Adw.Application.register() failed: {_register_exc}. Falling back to Gtk.init().", stacklevel=2)
    try:
        Gtk.init()
    except Exception as _init_exc:
        warnings.warn(f"Gtk.init() also failed: {_init_exc}. @Gtk.Template widgets will likely segfault.", stacklevel=2)


def test_application_css_provider_loads_and_registers_for_default_display():
    from gi.repository import Gdk

    from anura.core.resources import load_css_provider

    display = Gdk.Display.get_default()
    assert display is not None

    provider = load_css_provider(display)

    assert isinstance(provider, Gtk.CssProvider)


def test_application_css_provider_skips_when_display_is_unavailable():
    from anura.core.resources import load_css_provider

    assert load_css_provider(None) is None


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

        dialog = PreferencesDialog()
        assert dialog is not None



def _drain_gtk_main_context():
    context = GLib.MainContext.default()
    for _ in range(20):
        if not context.pending():
            break
        context.iteration(False)


def _present_welcome_page():
    from anura.widgets.welcome_page import WelcomePage

    window = Gtk.Window()
    window.set_default_size(900, 600)
    page = WelcomePage()
    window.set_child(page)
    window.present()
    _drain_gtk_main_context()
    return window, page


@pytest.mark.gtk
def test_welcome_initial_tab_focus_is_language_selector():
    window, page = _present_welcome_page()
    try:
        assert window.child_focus(Gtk.DirectionType.TAB_FORWARD)
        assert window.get_focus() is page.lang_combo
    finally:
        window.destroy()


@pytest.mark.gtk
def test_welcome_wide_action_focus_order():
    window, page = _present_welcome_page()
    try:
        page._set_action_layout(True)
        _drain_gtk_main_context()
        page.screenshot_button.grab_focus()

        assert window.child_focus(Gtk.DirectionType.TAB_FORWARD)
        assert window.get_focus() is page.open_image_button
    finally:
        window.destroy()


@pytest.mark.gtk
def test_welcome_compact_action_focus_order():
    window, page = _present_welcome_page()
    try:
        page._set_action_layout(False)
        _drain_gtk_main_context()
        page.screenshot_button.grab_focus()

        assert window.child_focus(Gtk.DirectionType.TAB_FORWARD)
        assert window.get_focus() is page.more_options_button
    finally:
        window.destroy()


@pytest.mark.gtk
def test_welcome_focus_restores_after_responsive_reparenting():
    window, page = _present_welcome_page()
    try:
        page._set_action_layout(True)
        _drain_gtk_main_context()
        page.open_image_button.grab_focus()
        page._set_action_layout(False)
        _drain_gtk_main_context()
        assert window.get_focus() is page.more_options_button

        page.more_options_popover.popup()
        _drain_gtk_main_context()
        page.open_image_button.grab_focus()
        page._set_action_layout(True)
        _drain_gtk_main_context()
        assert window.get_focus() is page.open_image_button
    finally:
        window.destroy()
