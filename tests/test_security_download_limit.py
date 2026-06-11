# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import os
from unittest.mock import MagicMock, patch

import pytest

# Skip this test if GObject Introspection (gi) is missing (e.g. headless CI)
pytest.importorskip("gi")

from anura.config import MAX_MODEL_SIZE_BYTES


@pytest.mark.gtk
class TestSecurityDownloadLimit:
    @pytest.fixture
    def manager(self, tmp_path):
        from anura.services.language_manager import LanguageManager

        # Patch paths and settings to ensure headless safety and isolation
        with (
            patch("anura.services.language_manager.TESSDATA_DIR", str(tmp_path)),
            patch("anura.services.language_manager.TESSDATA_SYSTEM_DIR", str(tmp_path / "system")),
            patch("anura.services.language_manager.settings") as mock_settings,
        ):
            os.makedirs(tmp_path / "system", exist_ok=True)
            yield LanguageManager(), mock_settings

    @pytest.mark.parametrize("quality", ["best", "standard", "fast"])
    def test_download_begin_enforces_size_limit_via_header(self, manager, quality):
        """Verify that download_begin rejects files based on Content-Length header."""
        lm, mock_settings = manager
        mock_settings.get_string.return_value = quality

        mock_response = MagicMock()
        mock_response.status_code = 200
        # Set size slightly over the limit
        mock_response.headers = {"content-length": str(MAX_MODEL_SIZE_BYTES + 1)}

        with patch.object(lm.session, "get", return_value=mock_response), \
             patch("shutil.which", return_value="/usr/bin/tesseract"):

            result = lm.download_begin("fra")
            assert result is None

    def test_download_begin_enforces_size_limit_via_streaming(self, manager):
        """Verify that download_begin aborts when actual streamed bytes exceed limit."""
        lm, mock_settings = manager
        mock_settings.get_string.return_value = "best"

        mock_response = MagicMock()
        mock_response.status_code = 200
        # No Content-Length header to simulate chunked encoding or unknown size
        mock_response.headers = {}

        # Simulate a stream that yields a chunk that puts it over the limit
        def iter_content(chunk_size=8192):
            yield b"A" * MAX_MODEL_SIZE_BYTES
            yield b"B"  # This should trigger the abort

        mock_response.iter_content = iter_content

        with patch.object(lm.session, "get", return_value=mock_response), \
             patch("shutil.which", return_value="/usr/bin/tesseract"), \
             patch("tempfile.NamedTemporaryFile") as mock_tmp:

            # Mock temp file to avoid actual disk I/O
            mock_file = MagicMock()
            mock_tmp.return_value.__enter__.return_value.name = "/tmp/fake.tmp"
            mock_tmp.return_value.__enter__.return_value.open.return_value.__enter__.return_value = mock_file

            result = lm.download_begin("fra")
            assert result is None
