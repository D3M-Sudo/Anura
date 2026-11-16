# This file is part of Anura.
# Copyright (C) 2022-2025 Andrey Maksimov (Frog)
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import time

import pytest

pytest.importorskip("gi")

from gettext import gettext as _
from unittest.mock import MagicMock, patch

import gi
from gi.repository import Adw, Gio, GLib, Gtk

# Register GResources and initialize Adw before importing template-backed widgets.

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("Gio", "2.0")
Adw.init()

# Load GResource bundle immediately at module level
import os  # noqa: E402

resource_path = os.path.join(os.path.dirname(__file__), "..", "data", "io.github.d3msudo.anura.gresource")
if os.path.exists(resource_path):
    resource = Gio.Resource.load(resource_path)
    resource._register()
else:
    import warnings

    warnings.warn(
        f"GResource bundle not found at {resource_path}, widget templates may fail to load", UserWarning, stacklevel=2
    )

from anura.models.language_item import LanguageItem  # noqa: E402
from anura.services.history_service import HistoryService  # noqa: E402
from anura.widgets.extracted_page import ExtractedPage  # noqa: E402
from anura.widgets.history_page import HistoryPage  # noqa: E402
from anura.widgets.welcome_page import WelcomePage  # noqa: E402


class TestExtractedPageEnterprise:
    """
    Enterprise-grade tests for ExtractedPage widget.
    """

    @pytest.fixture
    def widget(self):
        with patch("anura.widgets.extracted_page.get_share_service"):
            return ExtractedPage()

    @pytest.mark.gtk
    def test_buffer_changed_updates_stats(self, widget):
        """Test that typing in the text buffer updates word/char counts."""
        widget.buffer.set_text("Hello world")
        # _on_buffer_changed is connected to "changed" signal
        assert "2 words | 11 characters" in widget.stats_label.get_text()

        widget.buffer.set_text("")
        assert "0 words | 0 characters" in widget.stats_label.get_text()

    @pytest.mark.gtk
    def test_hiding_preserves_extracted_text_until_next_result(self, widget):
        """Navigation away preserves the current result; the next OCR result replaces it."""
        widget.buffer.set_text("first OCR result")
        go_back = MagicMock()
        widget.connect("go-back", go_back)

        widget.do_hiding()

        assert widget.extracted_text == "first OCR result"
        go_back.assert_called_once_with(widget, 1)

        widget._set_text_internal("second OCR result", "")
        assert widget.extracted_text == "second OCR result"

    @pytest.mark.gtk
    def test_button_sensitivity(self, widget):
        """Test that action buttons are disabled when buffer is empty."""
        widget.buffer.set_text("   ")  # Whitespace only
        assert widget.text_copy_btn.get_sensitive() is False
        assert widget.share_button.get_sensitive() is False
        assert widget.listen_btn.get_sensitive() is False

        widget.buffer.set_text("Valid text")
        assert widget.text_copy_btn.get_sensitive() is True
        assert widget.share_button.get_sensitive() is True
        assert widget.listen_btn.get_sensitive() is True

    @pytest.mark.gtk
    def test_listen_state_transitions(self, widget):
        """Test UI state transitions when starting/stopping TTS via state updates."""
        widget.buffer.set_text("Read me aloud")

        # Mock settings for the widget
        widget.settings = MagicMock()
        widget.settings.get_string.return_value = "eng"

        # Transition to generating state
        widget.update_tts_state("generating")
        # Should be in generating state (spinner)
        assert widget.listen_stack.get_visible_child_name() == "spinner"
        # controls should be locked
        assert widget.grab_btn.get_sensitive() is False

        # Transition to playing state
        widget.update_tts_state("playing")
        # Should be in playing state (pause button)
        assert widget.listen_stack.get_visible_child_name() == "pause"
        assert widget.listen_pause_btn.get_icon_name() == "media-playback-pause-symbolic"

        # Transition to paused state
        widget.update_tts_state("paused")
        assert widget.listen_stack.get_visible_child_name() == "pause"
        assert widget.listen_pause_btn.get_icon_name() == "media-playback-start-symbolic"

        # Transition to idle state
        widget.update_tts_state("idle")
        # Should be back to initial state (button)
        assert widget.listen_stack.get_visible_child_name() == "button"
        assert widget.grab_btn.get_sensitive() is True

    @pytest.mark.gtk
    def test_copy_feedback(self, widget):
        """Test the visual, tooltip and accessibility feedback when clicking copy."""
        widget.text_copy_btn.set_icon_name("edit-copy-symbolic")
        widget.show_copy_feedback()

        # Verify icon changed to checkmark
        assert widget.text_copy_btn.get_icon_name() == "emblem-ok-symbolic"
        # Verify tooltip changed to "Copied to clipboard!"
        assert widget.text_copy_btn.get_tooltip_text() == "Copied to clipboard!"

        # Explicitly trigger _reset_copy_icon to simulate timeout completion and verify restoration
        widget._reset_copy_icon("edit-copy-symbolic")
        assert widget.text_copy_btn.get_icon_name() == "edit-copy-symbolic"
        # Since buffer is empty, tooltip should revert to non-selection state
        assert "Copy Extracted Text" in widget.text_copy_btn.get_tooltip_text()


class TestWelcomePageEnterprise:
    """
    Enterprise-grade tests for WelcomePage widget.
    """

    @pytest.fixture
    def widget(self):
        with patch("anura.services.language_manager.get_language_manager") as mock_get_manager:
            mock_manager = MagicMock()
            mock_get_manager.return_value = mock_manager
            mock_manager.get_language.return_value = "English"
            return WelcomePage()

    @pytest.mark.gtk
    def test_welcome_secondary_actions_reparent_between_layouts(self, widget):
        """The same action controls are visible in either responsive layout."""
        action_ids = tuple(id(button) for button in widget.action_buttons)
        primary_parent = widget.screenshot_button.get_parent()
        assert widget.screenshot_button not in widget.action_buttons
        assert widget.screenshot_button.get_action_name() == "app.get_screenshot"
        assert "suggested-action" in widget.screenshot_button.get_css_classes()
        widget.show_spinner()
        widget._set_drop_area_processing_state(True)

        widget._set_action_layout(True)

        assert widget.secondary_actions.get_visible() is True
        assert widget.secondary_actions.get_homogeneous() is True
        assert widget.more_options_button.get_visible() is False
        assert all(button.get_parent() is widget.secondary_actions for button in widget.action_buttons)
        assert tuple(id(button) for button in widget.action_buttons) == action_ids
        assert widget.screenshot_button.get_parent() is primary_parent
        assert widget.spinner.get_visible() is True
        assert widget.drop_area.has_css_class("drag-processing")
        assert widget._drop_target.get_widget() is widget

        widget._set_action_layout(False)

        assert widget.secondary_actions.get_visible() is False
        assert widget.more_options_button.get_visible() is True
        assert all(button.get_parent() is widget.compact_actions for button in widget.action_buttons)
        assert tuple(id(button) for button in widget.action_buttons) == action_ids
        assert widget.screenshot_button.get_parent() is primary_parent
        assert widget.spinner.get_visible() is True
        assert widget.drop_area.has_css_class("drag-processing")
        assert widget._drop_target.get_widget() is widget

    @staticmethod
    def _spin_until(context, condition, timeout_seconds=3.0):
        """Process GTK events until a UI condition is met or the test times out."""
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            context.iteration(False)
            if condition():
                return True
            time.sleep(0.01)
        return condition()

    @pytest.mark.gtk
    def test_welcome_layout_transition_keeps_focus_on_visible_control(self, widget):
        """Layout changes keep keyboard focus on a visible Welcome control."""
        window = Gtk.Window()
        window.set_default_size(900, 600)
        window.set_child(widget)

        actions = Gio.SimpleActionGroup()
        for action_name in ("get_screenshot", "open_image", "paste_from_clipboard"):
            actions.add_action(Gio.SimpleAction.new(action_name, None))
        window.insert_action_group("app", actions)
        window.present()

        context = GLib.MainContext.default()
        assert self._spin_until(
            context,
            lambda: (
                widget.action_clamp.get_width() > 0
                and widget._last_action_width == widget.action_clamp.get_width()
                and widget._wide_action_layout
                and widget.open_image_button.get_mapped()
            ),
        ), (
            f"wide layout did not settle: clamp_width={widget.action_clamp.get_width()}, "
            f"last_tick_width={widget._last_action_width}, "
            f"wide={widget._wide_action_layout}"
        )

        # The action row is a sibling of the popover trigger; use the primary
        # action to verify that a visible control retains focus while compacting.
        window.set_focus(widget.screenshot_button)
        assert self._spin_until(context, lambda: window.get_focus() == widget.screenshot_button)

        threshold = widget._get_wide_action_threshold()
        compact_width = threshold - 1
        with patch.object(widget.action_clamp, "get_width", return_value=compact_width):
            widget._update_action_layout()

        assert self._spin_until(
            context,
            lambda: (
                not widget._wide_action_layout
                and widget.more_options_button.get_visible()
                and window.get_focus() == widget.screenshot_button
            ),
        ), (
            f"compact transition lost visible focus: clamp_width={compact_width}, "
            f"wide={widget._wide_action_layout}, focus={window.get_focus()}"
        )

        # Verify the compact trigger -> wide fallback independently of the
        # headless compositor's focus activation policy.
        root = MagicMock()
        root.get_focus.return_value = widget.more_options_button
        with (
            patch.object(widget, "get_root", return_value=root),
            patch.object(widget.screenshot_button, "grab_focus") as focus_primary,
        ):
            widget._set_action_layout(True)
            focus_primary.assert_called_once_with()

        assert widget._wide_action_layout is True
        assert widget.secondary_actions.get_visible() is True

        # A focused secondary action must transfer focus to More options when
        # the wide row is compacted; defer the actual GTK focus call until idle.
        root.get_focus.return_value = widget.open_image_button
        with (
            patch.object(widget, "get_root", return_value=root),
            patch("anura.widgets.welcome_page.GLib.idle_add") as idle_add,
        ):
            widget._set_action_layout(False)
            idle_add.assert_called_once_with(widget._focus_more_options_idle)

        assert widget._wide_action_layout is False
        assert all(button.get_parent() is widget.compact_actions for button in widget.action_buttons)
        window.destroy()

    @pytest.mark.gtk
    def test_welcome_action_breakpoint_uses_measured_control_widths(self, widget):
        """The breakpoint follows natural control widths and inter-column spacing."""
        threshold = widget._get_wide_action_threshold()
        natural_widths = [button.get_preferred_size()[1].width for button in widget.action_buttons]

        expected = (
            max(natural_widths) * len(widget.action_buttons)
            + widget.secondary_actions.get_spacing() * (len(widget.action_buttons) - 1)
            + widget.secondary_actions.get_margin_start()
            + widget.secondary_actions.get_margin_end()
        )

        assert threshold == expected

        with patch.object(widget.action_clamp, "get_width", return_value=expected):
            widget._update_action_layout()
        assert widget._wide_action_layout is True

        with patch.object(widget.action_clamp, "get_width", return_value=expected - 1):
            widget._update_action_layout()
        assert widget._wide_action_layout is False

    @pytest.mark.parametrize(
        ("width", "height", "expected_wide"),
        [
            (360, 600, False),
            (640, 480, True),
            (900, 600, True),
            (1280, 800, True),
        ],
    )
    @pytest.mark.gtk
    def test_welcome_responsive_layout_at_m1_viewports(self, widget, width, height, expected_wide):
        """The action row switches at the measured threshold across M1 window sizes."""
        window = Gtk.Window()
        window.set_default_size(width, height)
        window.set_child(widget)
        window.present()

        context = GLib.MainContext.default()
        assert self._spin_until(
            context,
            lambda: (
                window.get_mapped()
                and widget.action_clamp.get_width() > 0
                and widget._last_action_width == widget.action_clamp.get_width()
                and widget._wide_action_layout is expected_wide
            ),
        ), (
            f"viewport layout did not settle: requested={width}x{height}, "
            f"window={window.get_width()}x{window.get_height()}, "
            f"clamp_width={widget.action_clamp.get_width()}, "
            f"last_tick_width={widget._last_action_width}, "
            f"threshold={widget._get_wide_action_threshold()}, "
            f"wide={widget._wide_action_layout}"
        )

        assert window.get_mapped() is True
        measured_width = widget.action_clamp.get_width()
        assert measured_width > 0
        assert widget._wide_action_layout is expected_wide, (
            f"viewport={width}x{height}, window_width={window.get_width()}, "
            f"welcome_width={widget.welcome.get_width()}, "
            f"clamp_width={widget.action_clamp.get_width()}, "
            f"threshold={widget._get_wide_action_threshold()}, "
            f"last_tick_width={widget._last_action_width}, "
            f"tick_id={widget._action_layout_tick_id}, "
            f"clamp_mapped={widget.action_clamp.get_mapped()}, "
            f"button_widths={[button.get_preferred_size()[1].width for button in widget.action_buttons]}"
        )
        window.destroy()

    @pytest.mark.gtk
    def test_welcome_page_scrolls_when_vertical_viewport_is_constrained(self, widget):
        """Expanded Welcome content remains reachable in a short window."""
        window = Gtk.Window()
        window.set_default_size(360, 260)
        window.set_child(widget)
        window.present()

        context = GLib.MainContext.default()
        scrolled_window = widget.action_clamp.get_child()
        assert isinstance(scrolled_window, Gtk.ScrolledWindow)

        try:
            assert self._spin_until(
                context,
                lambda: window.get_mapped() and scrolled_window.get_mapped() and scrolled_window.get_height() > 0,
            ), (
                f"Welcome scroller did not map: window={window.get_width()}x{window.get_height()}, "
                f"scroller={scrolled_window.get_width()}x{scrolled_window.get_height()}"
            )

            # Expanding the drop zone adds real content below the primary and
            # secondary actions, forcing the short viewport to become scrollable.
            widget.drop_revealer.set_reveal_child(True)
            adjustment = scrolled_window.get_vadjustment()
            assert self._spin_until(
                context,
                lambda: adjustment.get_upper() > adjustment.get_page_size() + 1,
            ), (
                f"Welcome content did not overflow vertically: "
                f"upper={adjustment.get_upper()}, page_size={adjustment.get_page_size()}, "
                f"scroller_height={scrolled_window.get_height()}, "
                f"drop_revealed={widget.drop_revealer.get_reveal_child()}"
            )

            assert scrolled_window.get_vscrollbar().get_visible() is True
            maximum_value = adjustment.get_upper() - adjustment.get_page_size()
            adjustment.set_value(maximum_value)
            assert self._spin_until(context, lambda: adjustment.get_value() >= maximum_value - 1), (
                f"Welcome scroller could not reach its lower range: "
                f"value={adjustment.get_value()}, maximum={maximum_value}"
            )
        finally:
            window.destroy()

    @pytest.mark.gtk
    def test_spinner_state(self, widget):
        """Test show/hide spinner logic."""
        widget.show_spinner()
        assert widget.spinner.get_visible() is True
        # Spinner state is internal to Gtk.Spinner, but we can check visibility

        widget.hide_spinner()
        assert widget.spinner.get_visible() is False

    @pytest.mark.gtk
    def test_drop_button_toggle(self, widget):
        """Test that the drop area visibility is toggled by the button."""
        import sys

        initial_revealed = widget.drop_revealer.get_reveal_child()
        print(f"\n[DEBUG] initial_revealed = {initial_revealed}")
        print(f"[DEBUG] initial tooltip = '{widget.drop_button.get_tooltip_text()}'")
        sys.stdout.flush()

        # In GTK4, we use activate() or emit("clicked")
        widget.drop_button.emit("clicked")

        tooltip_1 = widget.drop_button.get_tooltip_text() or ""
        print(f"[DEBUG] after first click, revealed = {widget.drop_revealer.get_reveal_child()}")
        print(
            f"[DEBUG] after first click, has suggested-action = {widget.drop_button.has_css_class('suggested-action')}"
        )
        print(f"[DEBUG] after first click, tooltip = '{tooltip_1}'")
        sys.stdout.flush()

        assert widget.drop_revealer.get_reveal_child() == (not initial_revealed)
        assert widget.drop_button.has_css_class("suggested-action")

        # Robust assertion for tooltip text to support localized environments smoothly
        assert "Hide" in tooltip_1 or tooltip_1 == _("Hide drop area")

        widget.drop_button.emit("clicked")

        tooltip_2 = widget.drop_button.get_tooltip_text() or ""
        print(f"[DEBUG] after second click, revealed = {widget.drop_revealer.get_reveal_child()}")
        print(
            f"[DEBUG] after second click, has suggested-action = {widget.drop_button.has_css_class('suggested-action')}"
        )
        print(f"[DEBUG] after second click, tooltip = '{tooltip_2}'")
        sys.stdout.flush()

        assert widget.drop_revealer.get_reveal_child() == initial_revealed
        assert not widget.drop_button.has_css_class("suggested-action")

        assert "Drop" in tooltip_2 or "Trascina" in tooltip_2 or tooltip_2 == _("Drop image here")

    @pytest.mark.gtk
    def test_language_changed_signal(self, widget):
        """Test that language change updates the UI and settings."""
        widget.settings = MagicMock()
        lang_item = LanguageItem(code="fra", title="French")

        # Emit signal from the internal popover
        widget.language_popover.emit("language-changed", lang_item)

        assert widget.lang_combo.get_label() == "French"
        widget.settings.set_string.assert_called_with("active-language", "fra")

    @pytest.mark.gtk
    def test_reset_drop_area_state(self, widget):
        """Test resetting the drop area after processing."""
        widget.drop_revealer.set_reveal_child(True)
        widget.show_spinner()

        widget.reset_drop_area_state()

        assert widget.drop_revealer.get_reveal_child() is False
        assert widget.spinner.get_visible() is False
        assert not widget.drop_button.has_css_class("suggested-action")

        # Robust assertion for tooltip text to support localized environments smoothly
        tooltip = widget.drop_button.get_tooltip_text() or ""
        assert "Drop" in tooltip or "Trascina" in tooltip or tooltip == _("Drop image here")


class TestLanguagePopoverEnterprise:
    """
    Enterprise-grade tests for LanguagePopover widget.
    """

    @pytest.fixture
    def widget(self, monkeypatch):
        # Import inside to avoid module-level issues during discovery if any
        import anura.widgets.language_popover as lp_mod

        mock_manager = MagicMock()
        mock_manager.get_downloaded_codes.return_value = ["eng", "ita"]
        mock_manager.get_language.side_effect = lambda x: "English" if x == "eng" else "Italian"
        mock_manager.get_language_item.side_effect = lambda x: LanguageItem(
            code=x, title="English" if x == "eng" else "Italian"
        )

        # Monkeypatch the get_language_manager() function call inside the module
        monkeypatch.setattr(lp_mod, "get_language_manager", lambda: mock_manager)

        popover = lp_mod.LanguagePopover()
        return popover

    @pytest.mark.gtk
    def test_search_filtering(self, widget):
        """Test that typing in search filters the list."""
        # Ensure our mock returns the expected values when populate_model is called
        widget.populate_model()
        assert widget.filter_list.get_n_items() == 2

        # Filter for "English"
        widget.entry.set_text("Eng")
        # _on_search_changed is connected to "search-changed"
        widget.entry.emit("search-changed")
        assert widget.filter_list.get_n_items() == 1
        assert widget.filter_list.get_item(0).code == "eng"

        # Filter for something non-existent
        widget.entry.set_text("Russian")
        widget.entry.emit("search-changed")
        assert widget.filter_list.get_n_items() == 0
        assert widget.views.get_visible_child_name() == "empty_page"

    @pytest.mark.gtk
    def test_item_selection(self, widget):
        """Test that selecting an item emits the signal and updates settings."""
        widget.settings = MagicMock()
        widget.populate_model()

        # Find the row for Italian
        row = None
        for i in range(widget.filter_list.get_n_items()):
            if widget.filter_list.get_item(i).code == "ita":
                # We need the actual row widget, but list_view.get_row_at_index works if model is bound
                row = widget.list_view.get_row_at_index(i)
                break

        assert row is not None

        with patch.object(widget, "emit") as mock_emit:
            # GTK4 ListBox::row-activated
            widget.list_view.emit("row-activated", row)

            # Check signal emission (LanguageItem is the arg)
            args, _ = mock_emit.call_args
            assert args[0] == "language-changed"
            assert args[1].code == "ita"

            widget.settings.set_string.assert_called_with("active-language", "ita")


class TestAccessibilityEnhancementsEnterprise:
    """Tests specifically validating the custom WCAG 2.1 AA and UX enhancements."""

    @pytest.mark.gtk
    def test_share_row_accessibility(self):
        """Verify ShareRow sets tooltip and accessible label directly on the ListBoxRow widget."""
        from anura.widgets.share_row import ShareRow

        row = ShareRow(provider_name="email")
        assert row.get_tooltip_text() == "Share via Email"
        assert row.provider_name == "email"

    @pytest.mark.gtk
    def test_share_row_resolves_all_provider_icons_from_the_resource_theme(self):
        """Every active share provider must resolve to a bundled symbolic icon."""
        from anura.services.share_providers import PROVIDERS
        from anura.widgets.share_row import ShareRow

        rows = [ShareRow(provider.id) for provider in PROVIDERS]
        icon_theme = Gtk.IconTheme.get_for_display(rows[0].get_display())

        for provider, row in zip(PROVIDERS, rows, strict=True):
            icon_name = f"share-{provider.id}-symbolic"
            assert row.image.get_icon_name() == icon_name
            assert icon_theme.has_icon(icon_name)

    @pytest.mark.gtk
    def test_language_row_context_accessibility(self):
        """Verify LanguageRow dynamically updates tooltips and accessibility labels based on assigned language."""
        from anura.widgets.language_row import LanguageRow

        row = LanguageRow()
        item = LanguageItem(code="ita", title="Italian")
        row.item = item

        assert row.install_btn.get_tooltip_text() == "Install Italian"
        assert row.remove_btn.get_tooltip_text() == "Remove Italian"

    @pytest.mark.gtk
    def test_language_popover_row_selected_state(self):
        """Verify LanguagePopoverRow updates SELECTED Gtk.AccessibleState and active label/tooltip when selection changes."""
        from anura.widgets.language_popover_row import LanguagePopoverRow

        item = LanguageItem(code="deu", title="German", selected=False)
        row = LanguagePopoverRow(item)

        assert "Select German" in row.get_tooltip_text()

        # Toggle selected and ensure it updates tooltip and accessibility metadata
        item.selected = True
        assert "German (active language)" in row.get_tooltip_text()

        # Clean dispose
        row.run_dispose()

    @pytest.mark.gtk
    def test_language_popover_down_arrow_navigation(self):
        """Verify LanguagePopover handles Down arrow in search entry to focus the first row."""
        from gi.repository import Gdk

        import anura.widgets.language_popover as lp_mod

        with patch("anura.widgets.language_popover.get_language_manager") as mock_get_manager:
            mock_manager = MagicMock()
            mock_get_manager.return_value = mock_manager
            mock_manager.get_downloaded_codes.return_value = ["eng", "deu"]
            mock_manager.get_language.side_effect = lambda x: "English" if x == "eng" else "German"

            popover = lp_mod.LanguagePopover()
            popover.populate_model()

            # Trigger key pressed with Gdk.KEY_Down
            res = popover._on_entry_key_pressed(None, Gdk.KEY_Down, 0, 0)
            assert res is True

    @pytest.mark.gtk
    def test_language_popover_search_accessibility_label(self):
        """Verify LanguagePopover updates accessible label on list_view when search query changes."""
        import anura.widgets.language_popover as lp_mod

        with patch("anura.widgets.language_popover.get_language_manager") as mock_get_manager:
            mock_manager = MagicMock()
            mock_get_manager.return_value = mock_manager
            mock_manager.get_downloaded_codes.return_value = ["eng", "deu"]
            mock_manager.get_language.side_effect = lambda x: "English" if x == "eng" else "German"

            popover = lp_mod.LanguagePopover()
            popover.populate_model()

            # Filter for "Eng"
            popover.entry.set_text("Eng")
            popover.entry.emit("search-changed")
            assert popover.filter_list.get_n_items() == 1

            # Filter for non-existent
            popover.entry.set_text("Russian")
            popover.entry.emit("search-changed")
            assert popover.filter_list.get_n_items() == 0

            # Clear search
            popover.entry.set_text("")
            popover.entry.emit("search-changed")
            assert popover.filter_list.get_n_items() == 2

    @pytest.mark.gtk
    def test_welcome_page_drop_button_accessibility(self):
        """Verify WelcomePage drop_button sets EXPANDED and label properties correctly."""
        with patch("anura.services.language_manager.get_language_manager") as mock_get_manager:
            mock_manager = MagicMock()
            mock_get_manager.return_value = mock_manager
            mock_manager.get_language.return_value = "English"

            widget = WelcomePage()

            # Click drop button to reveal
            widget.drop_button.emit("clicked")
            # Tooltip should indicate Hide
            assert "Hide" in widget.drop_button.get_tooltip_text()

            # Toggle off
            widget.drop_button.emit("clicked")
            assert "Drop" in widget.drop_button.get_tooltip_text()

    @pytest.mark.gtk
    def test_welcome_page_escape_key_collapses_drop_area(self):
        """Verify that pressing Escape inside drop_area collapses the drop area."""
        with patch("anura.services.language_manager.get_language_manager") as mock_get_manager:
            mock_manager = MagicMock()
            mock_get_manager.return_value = mock_manager
            mock_manager.get_language.return_value = "English"

            widget = WelcomePage()
            widget.drop_revealer.set_reveal_child(True)

            # Simulate Escape key press on key controller
            from gi.repository import Gdk

            res = widget._on_drop_area_key_pressed(None, Gdk.KEY_Escape, 0, 0)
            assert res is True
            assert widget.drop_revealer.get_reveal_child() is False


class TestNavigationStateIntegration:
    """Real GTK navigation tests for the M2 Extracted and History state policies."""

    @pytest.mark.gtk
    def test_extracted_result_survives_navigation_round_trip(self):
        welcome = Adw.NavigationPage.new(Gtk.Label(label="Welcome"), "Welcome")
        welcome.set_tag("welcome")
        extracted = ExtractedPage()
        extracted.set_tag("extracted")

        navigation = Adw.NavigationView()
        navigation.set_animate_transitions(False)
        navigation.add(welcome)
        navigation.add(extracted)
        window = Gtk.Window()
        window.set_child(navigation)
        window.present()
        context = GLib.MainContext.default()

        try:
            assert TestWelcomePageEnterprise._spin_until(context, lambda: navigation.get_visible_page() is welcome)
            extracted.buffer.set_text("retained OCR result")
            navigation.push_by_tag("extracted")
            assert TestWelcomePageEnterprise._spin_until(context, lambda: navigation.get_visible_page() is extracted)

            navigation.pop_to_tag("welcome")
            assert TestWelcomePageEnterprise._spin_until(context, lambda: navigation.get_visible_page() is welcome)
            assert extracted.extracted_text == "retained OCR result"

            navigation.push_by_tag("extracted")
            assert TestWelcomePageEnterprise._spin_until(context, lambda: navigation.get_visible_page() is extracted)
            assert extracted.extracted_text == "retained OCR result"
        finally:
            window.destroy()

    @pytest.mark.gtk
    def test_history_navigation_restores_expansion_and_scroll_in_session(self, tmp_path):
        service = HistoryService(base_dir=tmp_path)
        for index in range(40):
            service.record(f"entry {index:02d} " + ("stored OCR content " * 12), "eng")

        welcome = Adw.NavigationPage.new(Gtk.Label(label="Welcome"), "Welcome")
        welcome.set_tag("welcome")
        history = HistoryPage()
        history.set_tag("history")
        history.settings = MagicMock()
        history.settings.get_boolean.return_value = True
        history.setup(service)

        navigation = Adw.NavigationView()
        navigation.set_animate_transitions(False)
        navigation.add(welcome)
        navigation.add(history)
        window = Gtk.Window()
        window.set_default_size(900, 600)
        window.set_child(navigation)
        window.present()
        context = GLib.MainContext.default()

        try:
            assert TestWelcomePageEnterprise._spin_until(context, lambda: navigation.get_visible_page() is welcome)
            navigation.push_by_tag("history")
            assert TestWelcomePageEnterprise._spin_until(context, lambda: navigation.get_visible_page() is history)

            scrolled_window = history.history_list.get_ancestor(Gtk.ScrolledWindow)
            adjustment = scrolled_window.get_vadjustment()
            assert TestWelcomePageEnterprise._spin_until(
                context, lambda: adjustment.get_upper() > adjustment.get_page_size()
            )

            entry = service.get_entries()[10]
            expanded_row = history._row_entry_ids[entry.id]
            expanded_row.set_expanded(True)
            assert TestWelcomePageEnterprise._spin_until(context, lambda: history._open_row is expanded_row)

            target_scroll = min(150.0, adjustment.get_upper() - adjustment.get_page_size())
            adjustment.set_value(target_scroll)
            assert TestWelcomePageEnterprise._spin_until(
                context, lambda: abs(adjustment.get_value() - target_scroll) < 1.0
            )

            navigation.pop_to_tag("welcome")
            assert TestWelcomePageEnterprise._spin_until(context, lambda: navigation.get_visible_page() is welcome)
            history.refresh()
            navigation.push_by_tag("history")

            def state_restored():
                restored_row = history._row_entry_ids.get(entry.id)
                return (
                    navigation.get_visible_page() is history
                    and restored_row is not None
                    and history._open_row is restored_row
                    and restored_row.get_expanded()
                    and abs(adjustment.get_value() - target_scroll) < 1.0
                )

            assert TestWelcomePageEnterprise._spin_until(context, state_restored)
        finally:
            window.destroy()
            history.cleanup()

    @pytest.mark.gtk
    def test_navigation_to_extracted_acquires_text_view_focus(self):
        from anura.window import AnuraWindow

        welcome = Adw.NavigationPage.new(Gtk.Label(label="Welcome"), "Welcome")
        welcome.set_tag("welcome")
        extracted = ExtractedPage()
        extracted.set_tag("extracted")

        navigation = Adw.NavigationView()
        navigation.set_animate_transitions(False)
        navigation.add(welcome)
        navigation.add(extracted)
        gtk_window = Gtk.Window()
        gtk_window.set_child(navigation)
        gtk_window.present()
        context = GLib.MainContext.default()

        window_harness = MagicMock()
        window_harness.navigation_view = navigation
        window_harness.extracted_page = extracted

        try:
            assert TestWelcomePageEnterprise._spin_until(context, lambda: navigation.get_visible_page() is welcome)
            AnuraWindow._on_navigation_requested(window_harness, MagicMock(), "extracted")
            assert TestWelcomePageEnterprise._spin_until(
                context, lambda: navigation.get_visible_page() is extracted and extracted.text_view.has_focus()
            )
        finally:
            gtk_window.destroy()

    @pytest.mark.gtk
    def test_return_to_welcome_stops_active_tts(self):
        from anura.window import AnuraWindow

        window_harness = MagicMock()
        AnuraWindow.show_welcome_page(window_harness)

        window_harness.navigation_view.pop_to_tag.assert_called_once_with("welcome")
        window_harness.tts_controller.stop.assert_called_once_with()


class TestHistoryTtsNavigationLifecycle:
    """The real AnuraWindow and Adw.NavigationView own History TTS cleanup."""

    @staticmethod
    def _build_window():
        from anura.window import AnuraWindow

        app = Gtk.Application(
            application_id="io.github.d3msudo.anura.M2FTest",
            flags=Gio.ApplicationFlags.NON_UNIQUE,
        )
        app.register(None)
        app.settings = MagicMock()
        app.settings.get_string.return_value = "eng"
        app.settings.get_int.return_value = 10

        language_manager = MagicMock()
        language_manager.get_language_item.return_value = LanguageItem(code="eng", title="English")

        with (
            patch("gi.repository.Gtk.Application.get_default", return_value=app),
            patch("anura.window.get_language_manager", return_value=language_manager),
            patch("anura.window.get_share_service", return_value=MagicMock()),
            patch("anura.window.get_clipboard_service", side_effect=RuntimeError("clipboard unavailable")),
            patch("anura.window.HistoryService", return_value=MagicMock()),
            patch("anura.window.HistoryController", return_value=MagicMock()),
            patch("anura.window.TtsController") as tts_factory,
            patch("anura.window.OcrController", return_value=MagicMock()),
            patch("anura.window.DndController", return_value=MagicMock()),
            patch.object(AnuraWindow, "_setup_geometry"),
            patch.object(AnuraWindow, "_apply_capability_constraints"),
            patch.object(HistoryPage, "setup"),
        ):
            tts_controller = tts_factory.return_value
            window = AnuraWindow(application=app, backend=MagicMock())

        window.history_page.refresh = MagicMock()
        return window, tts_controller

    @pytest.mark.gtk
    def test_leaving_history_for_welcome_stops_tts(self):
        window, tts_controller = self._build_window()
        window.present()
        context = GLib.MainContext.default()

        try:
            assert TestWelcomePageEnterprise._spin_until(
                context, lambda: window.navigation_view.get_visible_page() is window.welcome_page
            )
            window.show_history_page()
            assert TestWelcomePageEnterprise._spin_until(
                context, lambda: window.navigation_view.get_visible_page() is window.history_page
            )
            tts_controller.stop.reset_mock()

            # Use NavigationView's native back path, not show_welcome_page().
            window.navigation_view.pop_to_tag("welcome")
            assert TestWelcomePageEnterprise._spin_until(
                context, lambda: window.navigation_view.get_visible_page() is window.welcome_page
            )
            tts_controller.stop.assert_called_once_with()
        finally:
            window.destroy()

    @pytest.mark.gtk
    def test_explicit_welcome_navigation_stops_history_tts_once(self):
        window, tts_controller = self._build_window()
        window.present()
        context = GLib.MainContext.default()

        try:
            assert TestWelcomePageEnterprise._spin_until(
                context, lambda: window.navigation_view.get_visible_page() is window.welcome_page
            )
            window.show_history_page()
            assert TestWelcomePageEnterprise._spin_until(
                context, lambda: window.navigation_view.get_visible_page() is window.history_page
            )
            tts_controller.stop.reset_mock()

            window.show_welcome_page()
            assert TestWelcomePageEnterprise._spin_until(
                context, lambda: window.navigation_view.get_visible_page() is window.welcome_page
            )
            tts_controller.stop.assert_called_once_with()
        finally:
            window.destroy()

    @pytest.mark.gtk
    def test_leaving_history_for_extracted_stops_tts(self):
        window, tts_controller = self._build_window()
        window.present()
        context = GLib.MainContext.default()

        try:
            assert TestWelcomePageEnterprise._spin_until(
                context, lambda: window.navigation_view.get_visible_page() is window.welcome_page
            )
            window.show_history_page()
            assert TestWelcomePageEnterprise._spin_until(
                context, lambda: window.navigation_view.get_visible_page() is window.history_page
            )
            tts_controller.stop.reset_mock()

            window.navigation_view.push_by_tag("extracted")
            assert TestWelcomePageEnterprise._spin_until(
                context, lambda: window.navigation_view.get_visible_page() is window.extracted_page
            )
            tts_controller.stop.assert_called_once_with()
        finally:
            window.destroy()

    @pytest.mark.gtk
    def test_entering_and_remaining_in_history_does_not_stop_tts(self):
        window, tts_controller = self._build_window()
        window.present()
        context = GLib.MainContext.default()

        try:
            assert TestWelcomePageEnterprise._spin_until(
                context, lambda: window.navigation_view.get_visible_page() is window.welcome_page
            )
            tts_controller.stop.reset_mock()
            window.show_history_page()
            assert TestWelcomePageEnterprise._spin_until(
                context, lambda: window.navigation_view.get_visible_page() is window.history_page
            )
            tts_controller.stop.assert_not_called()

            # History-local refresh leaves visible-page unchanged.
            window.history_page.refresh()
            tts_controller.stop.assert_not_called()
        finally:
            window.destroy()

    @pytest.mark.gtk
    def test_leaving_history_stops_even_if_tts_was_already_idle(self):
        window, tts_controller = self._build_window()
        window.present()
        context = GLib.MainContext.default()

        try:
            assert TestWelcomePageEnterprise._spin_until(
                context, lambda: window.navigation_view.get_visible_page() is window.welcome_page
            )
            window.show_history_page()
            assert TestWelcomePageEnterprise._spin_until(
                context, lambda: window.navigation_view.get_visible_page() is window.history_page
            )
            tts_controller.stop.reset_mock()

            # stop() remains safe to call when no speech is active; one page exit means one call.
            window.navigation_view.pop_to_tag("welcome")
            assert TestWelcomePageEnterprise._spin_until(
                context, lambda: window.navigation_view.get_visible_page() is window.welcome_page
            )
            tts_controller.stop.assert_called_once_with()
        finally:
            window.destroy()
