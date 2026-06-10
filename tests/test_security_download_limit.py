# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import os
from unittest.mock import MagicMock, patch

import pytest

from anura.services.language_manager import LanguageManager
from anura.config import MAX_MODEL_SIZE_BYTES

class TestSecurityDownloadLimit:
    """Security tests for LanguageManager download size enforcement."""

    @pytest.fixture
    def manager(self, tmp_path):
        # Patch TESSDATA_DIR to a temporary directory for each test
        with (
            patch("anura.services.language_manager.TESSDATA_DIR", str(tmp_path)),
            patch("anura.services.language_manager.TESSDATA_SYSTEM_DIR", str(tmp_path / "system")),
            patch("anura.services.language_manager.settings") as mock_settings
        ):
            mock_settings.get_string.return_value = "standard"
            os.makedirs(tmp_path / "system", exist_ok=True)
            yield LanguageManager()

    @patch("requests.Session.get")
    def test_download_blocked_by_content_length(self, mock_get, manager):
        """Test that download is blocked if Content-Length exceeds limit."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        # Exceed limit by 1 byte
        mock_response.headers = {"content-length": str(MAX_MODEL_SIZE_BYTES + 1)}
        mock_get.return_value = mock_response

        with patch("shutil.which", return_value="/usr/bin/tesseract"):
            result = manager.download_begin("fra")
            assert result is None, "Download should be blocked by Content-Length header"

    @patch("requests.Session.get")
    def test_download_aborted_during_streaming(self, mock_get, manager):
        """Test that download is aborted if actual bytes exceed limit (Content-Length missing/wrong)."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        # Content-Length is within limit or missing
        mock_response.headers = {"content-length": "0"}

        # Simulate streaming chunks that eventually exceed the limit
        def iter_content(chunk_size=1):
            yield b"a" * (MAX_MODEL_SIZE_BYTES)
            yield b"exceed"

        mock_response.iter_content.side_effect = iter_content
        mock_get.return_value = mock_response

        with patch("shutil.which", return_value="/usr/bin/tesseract"):
            result = manager.download_begin("fra")
            assert result is None, "Download should be aborted during streaming when limit is exceeded"
