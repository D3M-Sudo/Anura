# tests/test_integration_cli_enterprise.py
import pytest
from unittest.mock import MagicMock, patch
from gi.repository import Gio, GLib
from anura.main import AnuraApplication

class TestCLIIntegrationEnterprise:
    """
    Integration tests for CLI argument handling in AnuraApplication.
    """

    @pytest.fixture
    def app(self):
        with patch('anura.main._load_gresource_bundle', return_value=True), \
             patch('anura.main.ScreenshotService'), \
             patch('anura.main.NotificationService'), \
             patch('anura.main.get_clipboard_service'):
            app = AnuraApplication()
            # Mock settings to avoid GSettings dependency if possible,
            # or rely on builddir schema setup
            app.settings = MagicMock()
            app.backend = MagicMock()
            return app

    def test_handle_extract_to_clipboard(self, app):
        """Test the -e / --extract-to-clipboard CLI flow."""
        app.settings.get_string.return_value = "eng"
        exit_code = app._handle_extract_to_clipboard()

        assert exit_code == 0
        app.backend.capture.assert_called_once_with("eng", copy=True)

    def test_handle_file_option_silent(self, app):
        """Test the -f --silent CLI flow."""
        file_path = "/tmp/test.png"
        with patch('os.path.exists', return_value=True), \
             patch('os.access', return_value=True), \
             patch.object(app, '_run_silent_mode', return_value=0) as mock_silent:

            exit_code = app._handle_file_option(file_path, is_silent=True)
            assert exit_code == 0
            mock_silent.assert_called_once_with(file_path)

    def test_handle_file_option_gui(self, app):
        """Test the -f (without --silent) CLI flow."""
        file_path = "/tmp/test.png"
        with patch('os.path.exists', return_value=True), \
             patch('os.access', return_value=True), \
             patch.object(app, '_activate_window_and_process_file') as mock_gui:

            exit_code = app._handle_file_option(file_path, is_silent=False)
            assert exit_code == 0
            mock_gui.assert_called_once_with(file_path)

    def test_handle_inaccessible_file_silent(self, app):
        """Test handling of inaccessible files in silent mode."""
        file_path = "/root/secret.png"
        with patch('os.path.exists', return_value=True), \
             patch('os.access', return_value=False):

            exit_code = app._handle_file_option(file_path, is_silent=True)
            assert exit_code == 1

    def test_do_command_line_routing(self, app):
        """Test that do_command_line correctly routes to specific handlers."""
        # Mock Gio.ApplicationCommandLine
        cmd_line = MagicMock(spec=Gio.ApplicationCommandLine)

        # Test -e
        cmd_line.get_options_dict().end().unpack.return_value = {"extract_to_clipboard": True}
        with patch.object(app, '_handle_extract_to_clipboard', return_value=0) as mock_extract:
            app.do_command_line(cmd_line)
            mock_extract.assert_called_once()

        # Test -f
        cmd_line.get_options_dict().end().unpack.return_value = {"file": "image.png"}
        with patch.object(app, '_handle_file_option', return_value=0) as mock_file:
            app.do_command_line(cmd_line)
            mock_file.assert_called_once_with("image.png", False)

    def test_on_decoded_no_window(self, app):
        """Test application-level on_decoded when no GUI window is present."""
        # active-window is a read-only GObject property, we need to mock the props object
        with patch.object(app, 'props') as mock_props:
            mock_props.active_window = None

        # Case: No text found
        app.on_decoded(None, "", copy=False)
        app.notification_service.show_notification.assert_called_with(
            title="Anura OCR", body="No text found. Try to grab another region."
        )

        # Case: Success with copy
        with patch('anura.main.get_clipboard_service') as mock_get_cb:
            mock_cb = mock_get_cb.return_value
            app.on_decoded(None, "found text", copy=True)
            mock_cb.set.assert_called_with("found text")
            app.notification_service.show_notification.assert_any_call(
                title="Anura OCR", body="Text extracted and copied to clipboard."
            )
