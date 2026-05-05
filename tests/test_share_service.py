# test_share_service.py
#
# Unit tests for ShareService
# Tests URL validation, provider logic, and Mastodon fallback

from unittest.mock import Mock, patch
import pytest

from anura.services.share_service import ShareService


class TestShareService:
    """Test suite for ShareService core functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = ShareService()
        # Mock launcher to avoid Gtk dependency
        self.service.launcher = Mock()

    def test_init(self):
        """Test service initialization."""
        assert self.service.launcher is not None
        assert hasattr(self.service, "MAX_URL_LENGTH")
        assert self.service.MAX_URL_LENGTH == 2000

    def test_providers(self):
        """Test provider list."""
        providers = ShareService.providers()
        expected = ["email", "mastodon", "reddit", "telegram", "x"]
        assert providers == expected

    def test_validate_share_url_valid_http(self):
        """Test validation of valid HTTP URLs."""
        valid_urls = [
            "https://example.com",
            "http://localhost:8080",
            "https://mastodon.social",
            "https://example.com/path?query=value",
        ]

        for url in valid_urls:
            assert ShareService._validate_share_url(url) is True

    def test_validate_share_url_valid_special_schemes(self):
        """Test validation of special scheme URLs."""
        special_urls = [
            "mailto:test@example.com",
            "web+mastodon://share?text=hello",
        ]

        for url in special_urls:
            assert ShareService._validate_share_url(url) is True

    def test_validate_share_url_invalid(self):
        """Test validation of invalid URLs."""
        invalid_urls = [
            "not-a-url",
            "ftp://example.com",
            "javascript:alert('xss')",
            "",
            "   ",
        ]

        for url in invalid_urls:
            assert ShareService._validate_share_url(url) is False

    def test_get_link_email(self):
        """Test email link generation."""
        text = "Hello world"
        link = ShareService.get_link_email(text)
        expected = "mailto:?subject=Extracted%20Text&body=Hello%20world"
        assert link == expected

    def test_get_link_reddit(self):
        """Test Reddit link generation."""
        text = "Hello world"
        link = ShareService.get_link_reddit(text)
        expected = "https://www.reddit.com/submit?selftext=Hello%20world"
        assert link == expected

    def test_get_link_telegram(self):
        """Test Telegram link generation."""
        text = "Hello world"
        link = ShareService.get_link_telegram(text)
        expected = "https://t.me/share/url?text=Hello%20world"
        assert link == expected

    def test_get_link_x(self):
        """Test X (Twitter) link generation."""
        text = "Hello world"
        link = ShareService.get_link_x(text)
        expected = "https://twitter.com/intent/tweet?text=Hello%20world"
        assert link == expected

    def test_get_link_mastodon(self):
        """Test Mastodon link generation."""
        text = "Hello world"
        link = ShareService.get_link_mastodon(text)
        expected = "web+mastodon://share?text=Hello%20world"
        assert link == expected

    def test_share_text_valid_provider(self):
        """Test sharing text with valid provider."""
        with patch("anura.services.share_service.GLib") as mock_glib:
            self.service.share_text("test text", "email")

            self.service.launcher.set_uri.assert_called_once()
            self.service.launcher.launch.assert_called_once()

    def test_share_text_invalid_provider(self):
        """Test sharing text with invalid provider."""
        with patch("anura.services.share_service.GLib") as mock_glib:
            self.service.share_text("test text", "invalid_provider")

            # Should not call launcher
            self.service.launcher.set_uri.assert_not_called()
            self.service.launcher.launch.assert_not_called()

    def test_share_text_blocked_url(self):
        """Test sharing text with blocked URL."""
        # Mock URL validation to return False
        with patch.object(ShareService, "_validate_share_url", return_value=False):
            with patch("anura.services.share_service.GLib") as mock_glib:
                self.service.share_text("test text", "email")

                # Should not call launcher
                self.service.launcher.set_uri.assert_not_called()
                self.service.launcher.launch.assert_not_called()

    def test_share_text_launcher_error(self):
        """Test handling of launcher errors."""
        self.service.launcher.launch.side_effect = Exception("Launcher error")

        with patch("anura.services.share_service.GLib"):
            # Should not raise exception
            self.service.share_text("test text", "email")

    def test_share_mastodon_with_fallback_success(self):
        """Test Mastodon sharing with successful official scheme."""
        with patch("anura.services.share_service.GLib") as mock_glib:
            # Mock successful launch
            self.service.launcher.launch_finish.return_value = True

            self.service._share_mastodon_with_fallback("test text")

            # Should set web+mastodon URL
            self.service.launcher.set_uri.assert_called_once_with("web+mastodon://share?text=test%20text")
            self.service.launcher.launch.assert_called_once()

    def test_share_mastodon_with_fallback_to_dialog(self):
        """Test Mastodon sharing fallback to instance dialog."""
        with patch("anura.services.share_service.GLib") as mock_glib:
            with patch.object(self.service, "_show_mastodon_instance_dialog") as mock_dialog:
                # Mock failed launch
                self.service.launcher.launch_finish.return_value = False

                self.service._share_mastodon_with_fallback("test text")

                # Should call dialog after failed launch
                mock_dialog.assert_called_once_with("test%20text")

    def test_share_mastodon_with_fallback_launch_error(self):
        """Test Mastodon sharing with launch error."""
        with patch("anura.services.share_service.GLib") as mock_glib:
            with patch.object(self.service, "_show_mastodon_instance_dialog") as mock_dialog:
                # Mock launch exception
                self.service.launcher.launch.side_effect = Exception("Launch error")

                self.service._share_mastodon_with_fallback("test text")

                # Should call dialog directly
                mock_dialog.assert_called_once_with("test%20text")

    def test_share_mastodon_url_too_long(self):
        """Test Mastodon sharing with URL too long."""
        long_text = "a" * 3000  # Will exceed MAX_URL_LENGTH

        with patch("anura.services.share_service.GLib") as mock_glib:
            self.service._share_mastodon_with_fallback(long_text)

            # Should emit share failure
            mock_glib.idle_add.assert_called_once()
            args = mock_glib.idle_add.call_args[0]
            assert args[0] == self.service.emit
            assert args[1] == "share"
            assert args[2] is False

    def test_show_mastodon_instance_dialog(self):
        """Test Mastodon instance dialog creation."""
        with patch("anura.services.share_service.Adw") as mock_adw:
            with patch("anura.services.share_service.Gio") as mock_gio:
                with patch("anura.services.share_service.GLib") as mock_glib:
                    # Mock app and window
                    mock_app = Mock()
                    mock_window = Mock()
                    mock_gio.Application.get_default.return_value = mock_app
                    mock_app.get_active_window.return_value = mock_window

                    mock_dialog = Mock()
                    mock_adw.MessageDialog.return_value = mock_dialog

                    self.service._show_mastodon_instance_dialog("test%20text")

                    # Should create dialog with instances
                    mock_adw.MessageDialog.assert_called_once()
                    mock_dialog.set_heading.assert_called_once()
                    mock_dialog.set_body.assert_called_once()
                    mock_dialog.add_response.assert_called()
                    mock_dialog.set_transient_for.assert_called_once_with(mock_window)
                    mock_dialog.present.assert_called_once()

    def test_show_mastodon_instance_dialog_no_window(self):
        """Test Mastodon instance dialog without active window."""
        with patch("anura.services.share_service.Adw") as mock_adw:
            with patch("anura.services.share_service.Gio") as mock_gio:
                with patch("anura.services.share_service.GLib") as mock_glib:
                    # Mock no active window
                    mock_app = Mock()
                    mock_app.get_active_window.return_value = None
                    mock_gio.Application.get_default.return_value = mock_app

                    mock_dialog = Mock()
                    mock_adw.MessageDialog.return_value = mock_dialog

                    self.service._show_mastodon_instance_dialog("test%20text")

                    # Should emit share failure
                    mock_glib.idle_add.assert_called_once()
                    args = mock_glib.idle_add.call_args[0]
                    assert args[0] == self.service.emit
                    assert args[1] == "share"
                    assert args[2] is False
                    mock_dialog.destroy.assert_called_once()

    def test_on_mastodon_instance_selected(self):
        """Test Mastodon instance selection."""
        with patch("anura.services.share_service.GLib") as mock_glib:
            mock_dialog = Mock()

            # Test instance selection
            self.service._on_mastodon_instance_selected(mock_dialog, "instance_mastodon.social", "test%20text")

            # Should launch with selected instance
            expected_url = "https://mastodon.social/share?text=test%20text"
            self.service.launcher.set_uri.assert_called_once_with(expected_url)
            self.service.launcher.launch.assert_called_once()
            mock_dialog.destroy.assert_called_once()

    def test_on_mastodon_instance_selected_cancel(self):
        """Test Mastodon instance dialog cancellation."""
        with patch("anura.services.share_service.GLib") as mock_glib:
            mock_dialog = Mock()

            # Test cancellation
            self.service._on_mastodon_instance_selected(mock_dialog, "cancel", "test%20text")

            # Should not launch, just destroy dialog
            self.service.launcher.set_uri.assert_not_called()
            self.service.launcher.launch.assert_not_called()
            mock_dialog.destroy.assert_called_once()

    def test_on_share_callback(self):
        """Test share completion callback."""
        with patch("anura.services.share_service.GLib") as mock_glib:
            mock_result = Mock()
            self.service.launcher.launch_finish.return_value = True

            self.service._on_share(None, mock_result)

            # Should emit share success
            mock_glib.idle_add.assert_called_once()
            args = mock_glib.idle_add.call_args[0]
            assert args[0] == self.service.emit
            assert args[1] == "share"
            assert args[2] is True

    def test_on_share_callback_error(self):
        """Test share completion callback with error."""
        with patch("anura.services.share_service.GLib") as mock_glib:
            mock_result = Mock()
            self.service.launcher.launch_finish.side_effect = Exception("Share error")

            self.service._on_share(None, mock_result)

            # Should emit share failure
            mock_glib.idle_add.assert_called_once()
            args = mock_glib.idle_add.call_args[0]
            assert args[0] == self.service.emit
            assert args[1] == "share"
            assert args[2] is False
