import os
import pytest
from unittest.mock import MagicMock, patch
import sys

from anura.main import AnuraApplication

class TestAuditIntegration:
    @pytest.fixture
    def app(self):
        with patch('gi.repository.Adw.init'):
            return AnuraApplication(version="0.1.4.3")

    def test_cli_file_option_accessible(self, app):
        with patch.object(app, '_is_file_accessible', return_value=True), \
             patch.object(app, '_process_accessible_file', return_value=0) as mock_process:

            res = app._handle_file_option("test.png", is_silent=True)

            assert res == 0
            mock_process.assert_called_once_with("test.png", True)

    def test_cli_file_option_inaccessible(self, app):
        with patch.object(app, '_is_file_accessible', return_value=False), \
             patch.object(app, '_handle_inaccessible_file', return_value=1) as mock_handle:

            res = app._handle_file_option("test.png", is_silent=True)
            assert res == 1
            mock_handle.assert_called_once_with("test.png", True)

    @patch('gi.repository.GLib.MainLoop')
    @patch('gi.repository.GLib.MainContext')
    def test_run_silent_mode_loop(self, mock_context, mock_loop, app):
        with patch('signal.signal'), \
             patch.object(app, '_execute_silent_ocr_with_context', return_value=0):

            res = app._run_silent_mode("test.png")
            assert res == 0

    def test_on_shot_done_structured_data(self):
        from anura.window import AnuraWindow
        from anura.services.screenshot_service import ScreenshotService

        mock_backend = MagicMock(spec=ScreenshotService)

        with patch('gi.repository.Gtk.Application.get_default') as mock_app_get:
            mock_app = MagicMock()
            mock_app_get.return_value = mock_app
            mock_app.settings = MagicMock()
            mock_app.settings.get_string.return_value = "eng"
            mock_app.settings.get_int.return_value = 800

            with patch.object(AnuraWindow, '__init__', return_value=None):
                win = AnuraWindow(backend=mock_backend)
                win.settings = mock_app.settings
                win.welcome_page = MagicMock()
                win.extracted_page = MagicMock()
                win._screenshot_timeout_id = None

                with patch('anura.window.get_text_preprocessor') as mock_get_prep, \
                     patch('anura.window.uri_validator', return_value=False), \
                     patch('anura.window.get_clipboard_service'), \
                     patch('gi.repository.GLib.idle_add'), \
                     patch.object(AnuraWindow, 'present'), \
                     patch.object(AnuraWindow, 'show_toast'):

                    mock_prep = MagicMock()
                    mock_get_prep.return_value = mock_prep
                    mock_prep.extract_structured_data.return_value = {
                        "urls": ["https://example.com"],
                        "emails": ["test@example.com"],
                        "phone_numbers": ["123456789"]
                    }

                    AnuraWindow.on_shot_done(win, None, "Check https://example.com", copy=False)

                    assert win.extracted_page.extracted_text == "Check https://example.com"
                    win.show_toast.assert_called()
