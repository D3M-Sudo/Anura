# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import unittest
from unittest.mock import MagicMock, patch

from anura.models.context import ApplicationContext


class TestCapabilityAudit(unittest.TestCase):
    @patch("shutil.which")
    @patch("importlib.util.find_spec")
    @patch("anura.models.context.Path.exists")
    def test_perform_audit_full_capabilities(self, mock_exists, mock_find_spec, mock_which):
        # Setup mocks for full capabilities
        mock_exists.return_value = True
        mock_find_spec.return_value = MagicMock()
        mock_which.return_value = "/usr/bin/executable"

        # Mock gi modules to simulate presence in headless environment
        mock_gi = MagicMock()
        with patch.dict("sys.modules", {"gi": mock_gi, "gi.repository": MagicMock()}):
            ctx = ApplicationContext.perform_audit()

        self.assertTrue(ctx.has_ocr)
        self.assertTrue(ctx.has_barcode)
        self.assertTrue(ctx.has_tts)
        self.assertTrue(ctx.has_scrot)
        self.assertTrue(ctx.is_flatpak)

    @patch("shutil.which")
    @patch("importlib.util.find_spec")
    @patch("anura.models.context.Path.exists")
    def test_perform_audit_missing_dependencies(self, mock_exists, mock_find_spec, mock_which):
        # Setup mocks for missing dependencies
        mock_exists.return_value = False
        mock_find_spec.return_value = None
        mock_which.return_value = None

        ctx = ApplicationContext.perform_audit()

        self.assertFalse(ctx.has_ocr)
        self.assertFalse(ctx.has_barcode)
        self.assertFalse(ctx.has_tts)
        self.assertFalse(ctx.has_scrot)
        self.assertFalse(ctx.is_flatpak)


if __name__ == "__main__":
    unittest.main()
