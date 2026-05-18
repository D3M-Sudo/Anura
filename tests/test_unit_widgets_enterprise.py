# tests/test_unit_widgets_enterprise.py
from unittest.mock import MagicMock, patch

# We need to register resources and initialize Adw before importing widgets that use templates
import gi
from gi.repository import Adw, Gio
import pytest

pytest.importorskip("gi")


gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("Gio", "2.0")
Adw.init()

# Load GResource bundle immediately at module level
import os  # noqa: E402

resource_path = os.path.join(os.path.dirname(__file__), "..", "data", "com.github.d3msudo.anura.gresource")
if os.path.exists(resource_path):
    resource = Gio.Resource.load(resource_path)
    resource._register()
else:
    raise RuntimeError(f"GResource bundle not found at {resource_path}")

from anura.types.language_item import LanguageItem  # noqa: E402
from anura.widgets.extracted_page import ExtractedPage  # noqa: E402
from anura.widgets.welcome_page import WelcomePage  # noqa: E402


class TestExtractedPageEnterprise:
    """
    Enterprise-grade tests for ExtractedPage widget.
    """

    @pytest.fixture
    def widget(self):
        with (
            patch("anura.widgets.extracted_page.get_share_service"),
            patch("anura.widgets.extracted_page.get_tts_service"),
        ):
            return ExtractedPage()

    @pytest.mark.gtk
    def test_buffer_changed_updates_stats(self, widget):
        """Test that typing in the text buffer updates word/char counts."""
        widget.buffer.set_text("Hello world")
        # _on_buffer_changed is connected to "changed" signal
        assert "Words: 2 | Characters: 11" in widget.stats_label.get_text()

        widget.buffer.set_text("")
        assert "Words: 0 | Characters: 0" in widget.stats_label.get_text()

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
        """Test UI state transitions when starting/stopping TTS."""
        widget.buffer.set_text("Read me aloud")

        # Mock settings for the widget
        widget.settings = MagicMock()
        widget.settings.get_string.return_value = "eng"

        with patch("anura.widgets.extracted_page.GObjectWorker.call"):
            widget.listen()
            # Should be in generating state (spinner)
            assert widget.listen_stack.get_visible_child_name() == "spinner"
            # swap_controls(False) was called in listen(), so buttons should be sensitive
            assert widget.grab_btn.get_sensitive() is True

            # Simulate generation success
            widget._on_generated("/tmp/speech.mp3")
            # Should be in playing state (pause button)
            assert widget.listen_stack.get_visible_child_name() == "pause"

            # Simulate playback end
            widget._on_listen_end(None, True)
            # Should be back to initial state (button)
            assert widget.listen_stack.get_visible_child_name() == "button"
            assert widget.grab_btn.get_sensitive() is True

    @pytest.mark.gtk
    def test_copy_feedback(self, widget):
        """Test the visual feedback when clicking copy."""
        widget.text_copy_btn.set_icon_name("edit-copy-symbolic")
        widget.show_copy_feedback()
        assert widget.text_copy_btn.get_icon_name() == "emblem-ok-symbolic"

        # We don't want to wait 2 seconds in a unit test, so we just verify it set the icon.
        # The timeout logic is standard GLib.


class TestWelcomePageEnterprise:
    """
    Enterprise-grade tests for WelcomePage widget.
    """

    @pytest.fixture
    def widget(self):
        with patch("anura.widgets.welcome_page.language_manager") as mock_manager:
            mock_manager.get_language.return_value = "English"
            return WelcomePage()

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
        initial_visible = widget.drop_area.get_visible()
        # In GTK4, we use activate() or emit("clicked")
        widget.drop_button.emit("clicked")
        assert widget.drop_area.get_visible() == (not initial_visible)
        assert widget.drop_button.has_css_class("suggested-action")

        widget.drop_button.emit("clicked")
        assert widget.drop_area.get_visible() == initial_visible
        assert not widget.drop_button.has_css_class("suggested-action")

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
        widget.drop_area.set_visible(True)
        widget.show_spinner()

        widget.reset_drop_area_state()

        assert widget.drop_area.get_visible() is False
        assert widget.spinner.get_visible() is False
        assert not widget.drop_button.has_css_class("suggested-action")


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

        # Monkeypatch the singleton in the widget module directly on the module object
        monkeypatch.setattr(lp_mod, "language_manager", mock_manager)

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
