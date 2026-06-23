# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import pytest

from anura.utils.validators import mask_url


class TestSentinelMaskUrl:
    """Security tests for URL masking logic."""

    @pytest.mark.parametrize(
        "url, expected",
        [
            # Basic masking
            ("https://user:password@example.com", "https://<redacted>@example.com"),
            ("http://admin:secret123@192.168.1.1:8080/path", "http://<redacted>@192.168.1.1:8080/path"),

            # Masking with query parameters and fragments
            ("https://user:pass@example.com/api?key=val#frag", "https://<redacted>@example.com/api?key=val#frag"),

            # Empty userinfo cases (matching uri_validator robust check)
            ("https://:@example.com", "https://<redacted>@example.com"),
            ("https://user@example.com", "https://<redacted>@example.com"),
            ("https://:pass@example.com", "https://<redacted>@example.com"),

            # URLs without userinfo (should remain unchanged)
            ("https://example.com", "https://example.com"),
            ("https://example.com/path?user=admin", "https://example.com/path?user=admin"),
            ("file:///etc/passwd", "file:///etc/passwd"),

            # Complex/Malformed URLs
            ("not a url", "not a url"),
            ("", ""),
            (None, ""),

            # '@' in path or query (should NOT trigger masking if not in netloc)
            ("https://example.com/path@file", "https://example.com/path@file"),
            ("https://example.com/search?q=me@home", "https://example.com/search?q=me@home"),

            # Multiple '@' (last one before host should be the delimiter)
            ("https://user:p@ss@example.com", "https://<redacted>@example.com"),
        ],
    )
    def test_mask_url(self, url, expected):
        assert mask_url(url) == expected
