# This file is part of Anura.
# Copyright (C) 2022-2025 Andrey Maksimov (Frog)
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import sys
import unittest
from unittest.mock import MagicMock, patch

# To prevent leaking mocks of system modules like 'gi' into other tests,
# we perform all GTK-dependent testing inside a context that patches sys.modules.


class TestSecurityDoS(unittest.TestCase):
    def setUp(self):
        # Create persistent mocks for the system modules we need to fake
        self.mock_gi = MagicMock()
        self.mock_adw = MagicMock()
        self.mock_gio = MagicMock()
        self.mock_glib = MagicMock()
        self.mock_gtk = MagicMock()

        # Setup Gio constants needed by the code under test
        self.mock_gio.FILE_ATTRIBUTE_STANDARD_SIZE = "standard::size"
        self.mock_glib.PRIORITY_DEFAULT = 0

        # Create a mapping of module names to our mocks
        self.module_patcher = patch.dict(
            sys.modules,
            {
                "gi": self.mock_gi,
                "gi.repository": MagicMock(),
                "gi.repository.Adw": self.mock_adw,
                "gi.repository.Gio": self.mock_gio,
                "gi.repository.GLib": self.mock_glib,
                "gi.repository.GObject": MagicMock(),
                "gi.repository.Gtk": self.mock_gtk,
                "gi.repository.Gdk": MagicMock(),
                "gi.repository.GdkPixbuf": MagicMock(),
                "loguru": MagicMock(),
            },
        )
        self.module_patcher.start()

        # Add mock gettext functions to sys.modules['builtins'] manually
        # patch.multiple("builtins", ...) fails if the attribute doesn't exist.
        import builtins

        self._orig_gettext = getattr(builtins, "_", None)
        self._orig_ngettext = getattr(builtins, "ngettext", None)
        builtins._ = lambda s: s
        builtins.ngettext = lambda s, p, n: s if n == 1 else p

        # Now we can safely import the mixin from within the isolated environment.
        # We also mock internal service getters to avoid complex service initialization.
        with (
            patch("anura.services.result_dispatcher.get_result_dispatcher"),
            patch("anura.utils.text_preprocessor.get_text_preprocessor"),
            patch("anura.utils.portal_advice.detect_portal_advice"),
        ):
            from anura.window_mixins.ocr_mixin import WindowOCRMixin

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

    def tearDown(self):
        import builtins

        if self._orig_gettext is None:
            del builtins._
        else:
            builtins._ = self._orig_gettext

        if self._orig_ngettext is None:
            del builtins.ngettext
        else:
            builtins.ngettext = self._orig_ngettext

        self.module_patcher.stop()

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
