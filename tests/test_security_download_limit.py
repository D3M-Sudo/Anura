# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

from unittest.mock import MagicMock, patch

import pytest
import requests

from anura.config import MAX_MODEL_SIZE_BYTES
from anura.services.language_manager import get_language_manager


@pytest.mark.parametrize("quality", ["best", "standard", "fast"])
def test_download_begin_enforces_size_limit_via_header(quality):
    """Verify that download_begin rejects files based on Content-Length header."""
    lm = get_language_manager()

    mock_response = MagicMock()
    mock_response.status_code = 200
    # Set size slightly over the limit
    mock_response.headers = {"content-length": str(MAX_MODEL_SIZE_BYTES + 1)}

    with patch("anura.services.settings.settings.get_string", return_value=quality), \
         patch.object(lm.session, "get", return_value=mock_response), \
         patch("shutil.which", return_value="/usr/bin/tesseract"):

        result = lm.download_begin("fra")
        assert result is None


def test_download_begin_enforces_size_limit_via_streaming():
    """Verify that download_begin aborts when actual streamed bytes exceed limit."""
    lm = get_language_manager()

    mock_response = MagicMock()
    mock_response.status_code = 200
    # No Content-Length header to simulate chunked encoding or unknown size
    mock_response.headers = {}

    # Simulate a stream that yields a chunk that puts it over the limit
    def iter_content(chunk_size=8192):
        yield b"A" * MAX_MODEL_SIZE_BYTES
        yield b"B"  # This should trigger the abort

    mock_response.iter_content = iter_content

    with patch("anura.services.settings.settings.get_string", return_value="best"), \
         patch.object(lm.session, "get", return_value=mock_response), \
         patch("shutil.which", return_value="/usr/bin/tesseract"), \
         patch("tempfile.NamedTemporaryFile") as mock_tmp:

        # Mock temp file to avoid actual disk I/O
        mock_file = MagicMock()
        mock_tmp.return_value.__enter__.return_value.name = "/tmp/fake.tmp"
        mock_tmp.return_value.__enter__.return_value.open.return_value.__enter__.return_value = mock_file

        result = lm.download_begin("fra")
        assert result is None
