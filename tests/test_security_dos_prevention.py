import builtins
import sys
import unittest
from unittest.mock import MagicMock, patch

# Mock GI modules before they are imported to allow running without GTK
mock_gi = MagicMock()
sys.modules["gi"] = mock_gi
sys.modules["gi.repository"] = MagicMock()
sys.modules["gi.repository.Adw"] = MagicMock()
sys.modules["gi.repository.Gdk"] = MagicMock()
sys.modules["gi.repository.Gio"] = MagicMock()
sys.modules["gi.repository.GLib"] = MagicMock()
sys.modules["gi.repository.GObject"] = MagicMock()
sys.modules["gi.repository.Gtk"] = MagicMock()
sys.modules["gi.repository.GdkPixbuf"] = MagicMock()

# Mock loguru
sys.modules["loguru"] = MagicMock()


# Mock gettext
def mock_gettext(s):
    return s


builtins.__dict__["_"] = mock_gettext
builtins.__dict__["ngettext"] = lambda s, p, n: s if n == 1 else p

# Now import the mixin
# We need to bypass the actual imports in the file if possible or mock them all
with patch("anura.services.clipboard_service.get_clipboard_service"), patch(
    "anura.utils.text_preprocessor.get_text_preprocessor"
), patch("anura.utils.portal_advice.detect_portal_advice"):
    from anura.window_mixins.ocr_mixin import WindowOCRMixin


class TestSecurityDoS(unittest.TestCase):
    def setUp(self):
        # Create a class that implements the mixin
        class TestWindow(WindowOCRMixin):
            def __init__(self):
                self.welcome_page = MagicMock()
                self.welcome_page.spinner = MagicMock()
                self.show_toast = MagicMock()
                self.settings = MagicMock()
                self.backend = MagicMock()
                self.extracted_page = MagicMock()
                self.portal_banner = MagicMock()
                self.split_view = MagicMock()

        self.win = TestWindow()

    @patch("anura.window_mixins.ocr_mixin.MAX_IMAGE_SIZE_BYTES", 100)
    @patch("anura.window_mixins.ocr_mixin.MAX_IMAGE_SIZE_MB", 1)
    def test_on_open_image_info_ready_rejects_large_file(self):
        mock_file = MagicMock()
        mock_result = MagicMock()
        mock_info = MagicMock()

        # Simulate file size > 100
        mock_info.get_size.return_value = 200
        mock_file.query_info_finish.return_value = mock_info

        self.win._on_open_image_info_ready(mock_file, mock_result)

        # Verify load_contents_async was NOT called
        mock_file.load_contents_async.assert_not_called()
        # Verify toast was shown
        self.win.show_toast.assert_called()
        # Verify spinner hidden
        self.win.welcome_page.spinner.set_visible.assert_called_with(False)

    @patch("anura.window_mixins.ocr_mixin.MAX_IMAGE_SIZE_BYTES", 100)
    @patch("anura.window_mixins.ocr_mixin.MAX_IMAGE_SIZE_MB", 1)
    def test_on_open_image_info_ready_accepts_valid_file(self):
        mock_file = MagicMock()
        mock_result = MagicMock()
        mock_info = MagicMock()

        # Simulate file size <= 100
        mock_info.get_size.return_value = 50
        mock_file.query_info_finish.return_value = mock_info

        self.win._on_open_image_info_ready(mock_file, mock_result)

        # Verify load_contents_async WAS called
        mock_file.load_contents_async.assert_called_once()

    def test_on_open_image_result_triggers_query_info(self):
        mock_dialog = MagicMock()
        mock_result = MagicMock()
        mock_file = MagicMock()

        mock_dialog.open_finish.return_value = mock_file

        self.win._on_open_image_result(mock_dialog, mock_result)

        # Verify query_info_async was called with correct number of arguments (5)
        # attributes, flags, io_priority, cancellable, callback
        args, _ = mock_file.query_info_async.call_args
        self.assertEqual(len(args), 5)
        mock_file.load_contents_async.assert_not_called()


if __name__ == "__main__":
    unittest.main()
