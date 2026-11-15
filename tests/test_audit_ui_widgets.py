# This file is part of Anura.
# Copyright (C) 2022-2025 Andrey Maksimov (Frog)
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import pytest

pytest.importorskip("gi")

import atexit
import os
import time
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


def _wait_for_gtk_condition(
    condition,
    description: str,
    timeout_seconds: float = 5.0,
    diagnostics=None,
) -> None:
    """Wait for an asynchronous GTK state transition without assuming frame timing."""
    context = GLib.MainContext.default()
    deadline = time.monotonic() + timeout_seconds
    while not condition():
        while context.pending():
            context.iteration(False)
        if time.monotonic() >= deadline:
            detail = f"; GTK state: {diagnostics()}" if diagnostics is not None else ""
            pytest.fail(f"GTK did not {description} within {timeout_seconds:.1f}s{detail}")
        time.sleep(0.01)

def _welcome_popover_diagnostic_state(window, page, events) -> str:
    """Capture GTK state when the compact Welcome Page popover fails to map."""

    def describe(widget):
        parent = widget.get_parent()
        root = widget.get_root()
        return {
            "type": type(widget).__name__,
            "visible": widget.get_visible(),
            "mapped": widget.get_mapped(),
            "size": (widget.get_width(), widget.get_height()),
            "parent": type(parent).__name__ if parent is not None else None,
            "root": type(root).__name__ if root is not None else None,
        }

    return repr(
        {
            "window": describe(window),
            "menu_button": {
                **describe(page.more_options_button),
                "active": page.more_options_button.get_active(),
                "sensitive": page.more_options_button.is_sensitive(),
            },
            "popover": {
                **describe(page.more_options_popover),
                "position": str(page.more_options_popover.get_position()),
                "child": (
                    type(page.more_options_popover.get_child()).__name__
                    if page.more_options_popover.get_child() is not None
                    else None
                ),
            },
            "actions": {
                name: describe(button)
                for name, button in (
                    ("open_image", page.open_image_button),
                    ("paste_image", page.paste_image_button),
                    ("drop", page.drop_button),
                )
            },
            "events": list(events),
        }
    )

def _wait_for_window_allocation(window, widget, timeout_seconds: float = 5.0) -> None:
    """Wait for the Wayland surface and GTK frame clock to allocate real geometry."""
    context = GLib.MainContext.default()
    deadline = time.monotonic() + timeout_seconds
    while not window.get_mapped() or window.get_width() <= 0 or window.get_height() <= 0 or widget.get_width() <= 0:
        while context.pending():
            context.iteration(False)
        if time.monotonic() >= deadline:
            pytest.fail(
                "GTK window/action widget was not allocated within "
                f"{timeout_seconds:.1f}s (mapped={window.get_mapped()}, "
                f"window={window.get_width()}x{window.get_height()}, "
                f"widget_width={widget.get_width()})"
            )
        time.sleep(0.01)


def _present_welcome_page():
    from anura.widgets.welcome_page import WelcomePage

    window = Gtk.Window()
    window.set_default_size(900, 600)
    page = WelcomePage()
    for button in (page.screenshot_button, page.open_image_button, page.paste_image_button, page.drop_button):
        button.set_action_name(None)
        button.set_sensitive(True)
    window.set_child(page)
    window.present()
    _drain_gtk_main_context()
    return window, page


def _focus_is_descendant_of(window, widget):
    focused = window.get_focus()
    while focused is not None:
        if focused is widget:
            return True
        focused = focused.get_parent()
    return False


@pytest.mark.gtk
def test_gtk_accessible_announce_api_is_available():
    from anura.utils.accessibility import announce_accessible

    window = Gtk.Window()
    label = Gtk.Label(label="Status")
    window.set_child(label)
    window.present()
    _drain_gtk_main_context()
    try:
        assert announce_accessible(label, "Status update", Gtk.AccessibleAnnouncementPriority.LOW)
    finally:
        window.destroy()


@pytest.mark.gtk
def test_welcome_initial_tab_focus_is_language_selector():
    window, page = _present_welcome_page()
    try:
        assert window.child_focus(Gtk.DirectionType.TAB_FORWARD)
        assert _focus_is_descendant_of(window, page.lang_combo)
    finally:
        window.destroy()


@pytest.mark.gtk
def test_welcome_wide_action_focus_order():
    window, page = _present_welcome_page()
    try:
        page._set_action_layout(True)
        _drain_gtk_main_context()
        assert page.open_image_button.get_parent() is page.secondary_actions
        assert page.paste_image_button.get_parent() is page.secondary_actions
        assert page.drop_button.get_parent() is page.secondary_actions

        assert page.open_image_button.get_visible(), "wide action button is not visible"
        assert page.open_image_button.get_mapped(), "wide action button is not mapped"
        assert page.open_image_button.get_focusable(), "wide action button is not focusable"
        assert page.open_image_button.grab_focus(), "GTK refused focus for the wide action button"
        assert window.get_focus() is page.open_image_button
        assert page.secondary_actions.child_focus(Gtk.DirectionType.TAB_FORWARD)
        assert window.get_focus() is page.paste_image_button
        assert page.secondary_actions.child_focus(Gtk.DirectionType.TAB_FORWARD)
        assert window.get_focus() is page.drop_button
    finally:
        window.destroy()


@pytest.mark.gtk
def test_welcome_compact_action_focus_order():
    window, page = _present_welcome_page()
    try:
        page._set_action_layout(False)
        _drain_gtk_main_context()
        assert page.more_options_button.get_visible()
        assert page.open_image_button.get_parent() is page.compact_actions
        assert page.paste_image_button.get_parent() is page.compact_actions
        assert page.drop_button.get_parent() is page.compact_actions

        page.more_options_popover.popup()
        _drain_gtk_main_context()
        page.open_image_button.grab_focus()
        assert window.get_focus() is page.open_image_button
        assert window.child_focus(Gtk.DirectionType.TAB_FORWARD)
        assert window.get_focus() is page.paste_image_button
        assert page.drop_button.get_visible(), "compact Drop action is not visible"
        assert page.drop_button.get_mapped(), "compact Drop action is not mapped"
        assert page.drop_button.get_focusable(), "compact Drop action is not focusable"
        assert page.drop_button.is_sensitive(), "compact Drop action is not sensitive"
        assert window.child_focus(Gtk.DirectionType.TAB_FORWARD), "GTK could not advance focus to compact Drop action"
        assert window.get_focus() is page.drop_button
    finally:
        window.destroy()


@pytest.mark.gtk
def test_welcome_focus_restores_after_responsive_reparenting():
    window, page = _present_welcome_page()
    try:
        page._set_action_layout(True)
        _drain_gtk_main_context()
        page.open_image_button.grab_focus()
        assert window.get_focus() is page.open_image_button

        page._set_action_layout(False)
        _drain_gtk_main_context()
        assert _focus_is_descendant_of(window, page.more_options_button)

        page.more_options_popover.popup()
        _drain_gtk_main_context()
        assert page.open_image_button.get_visible(), "compact action button is not visible"
        assert page.open_image_button.get_mapped(), "compact action button is not mapped"
        assert page.open_image_button.get_focusable(), "compact action button is not focusable"
        assert page.open_image_button.grab_focus(), "GTK refused focus for the compact action button"
        page._set_action_layout(True)
        _drain_gtk_main_context()
        assert window.get_focus() is page.open_image_button
    finally:
        window.destroy()


@pytest.mark.gtk
def test_welcome_focus_moves_from_more_options_to_primary_when_layout_expands():
    window, page = _present_welcome_page()
    try:
        page._set_action_layout(False)
        _drain_gtk_main_context()
        page.more_options_button.grab_focus()
        assert _focus_is_descendant_of(window, page.more_options_button)

        page._set_action_layout(True)
        _drain_gtk_main_context()
        assert window.get_focus() is page.screenshot_button
    finally:
        window.destroy()


@pytest.mark.gtk
@pytest.mark.parametrize(
    ("screen_width", "screen_height"),
    [(360, 600), (640, 480), (900, 600), (1280, 800)],
)
def test_welcome_responsive_layout_uses_allocated_viewport(screen_width: int, screen_height: int) -> None:
    """Exercise the real GTK allocation and responsive breakpoint per M2-B viewport."""
    from gi.repository import Gtk

    from anura.widgets.welcome_page import WelcomePage

    window = Gtk.Window()
    window.set_default_size(screen_width, screen_height)
    page = WelcomePage()
    for button in (page.screenshot_button, page.open_image_button, page.paste_image_button, page.drop_button):
        button.set_action_name(None)
        button.set_sensitive(True)
    window.set_child(page)
    window.present()

    try:
        _wait_for_window_allocation(window, page.action_clamp)
        _drain_gtk_main_context()
        assert window.get_width() > 0
        assert window.get_height() > 0
        assert page.action_clamp.get_width() > 0
        assert page.screenshot_button.get_visible()
        assert page.screenshot_button.get_mapped()
        assert page.screenshot_button.get_focusable()

        page._update_action_layout()
        _drain_gtk_main_context()
        wide = page.action_clamp.get_width() >= page._get_wide_action_threshold()

        assert page.secondary_actions.get_visible() is wide
        assert page.more_options_button.get_visible() is (not wide)
        assert all(
            button.get_parent() is (page.secondary_actions if wide else page.compact_actions)
            for button in page.action_buttons
        )
        assert len({id(button) for button in page.action_buttons}) == 3

        scroller = page.action_clamp.get_child()
        assert isinstance(scroller, Gtk.ScrolledWindow)
        horizontal_policy, vertical_policy = scroller.get_policy()
        assert horizontal_policy == Gtk.PolicyType.NEVER
        assert vertical_policy == Gtk.PolicyType.AUTOMATIC
        assert page.action_clamp.get_width() <= window.get_width()

        if not wide:
            assert page.more_options_button.get_mapped(), "compact More options trigger is not mapped"
            popover_events = []
            for signal in ("map", "unmap", "closed"):
                page.more_options_popover.connect(
                    signal,
                    lambda _widget, *_args, event=signal: popover_events.append(f"popover:{event}"),
                )
            page.more_options_popover.connect(
                "notify::visible",
                lambda *_args: popover_events.append(f"popover:visible={page.more_options_popover.get_visible()}"),
            )
            page.more_options_button.connect(
                "notify::active",
                lambda *_args: popover_events.append(f"menu-button:active={page.more_options_button.get_active()}"),
            )
            page.more_options_button.set_active(True)
            _wait_for_gtk_condition(
                lambda: (
                    page.more_options_popover.get_mapped()
                    and all(button.get_mapped() for button in page.action_buttons)
                ),
                "map the compact More options popover and its secondary actions",
                diagnostics=lambda: _welcome_popover_diagnostic_state(window, page, popover_events),
            )
            for button in page.action_buttons:
                assert button.get_visible()
                assert button.get_mapped()
                assert button.get_focusable()
            page.more_options_popover.popdown()
    finally:
        window.destroy()
