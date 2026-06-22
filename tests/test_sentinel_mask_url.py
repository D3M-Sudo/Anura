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
            ("https://user:pass@example.com", "https://***@example.com"),
            ("http://user@example.com", "http://***@example.com"),
            ("https://:pass@example.com", "https://***@example.com"),
            ("https://user:pass@example.com:8080/path?query=1#hash", "https://***@example.com:8080/path?query=1#hash"),
            ("https://example.com/path", "https://example.com/path"),
            ("mailto:user@example.com", "mailto:user@example.com"),  # mailto doesn't have netloc with @ in this way
            ("http://:@example.com", "http://***@example.com"),
            ("https://user%40name:password@example.com", "https://***@example.com"),
            ("https://example.com/path/user@domain.com", "https://example.com/path/user@domain.com"),
            ("https://user:pass@example.com/path/user@domain.com", "https://***@example.com/path/user@domain.com"),
            ("invalid-url-with-@:pass@example.com://", "invalid-url-with-@:pass@example.com://"),
            (None, "None"),
            (123, "123"),
            ("", ""),
        ],
    )
    def test_mask_url(self, url, expected):
        assert mask_url(url) == expected

    def test_mask_url_idna(self):
        # IDN should still have host part visible
        url = "https://user:pass@m\u00fcnchen.de"
        masked = mask_url(url)
        assert "***@" in masked
        assert "m\u00fcnchen.de" in masked or "xn--mnchen-3ya.de" in masked

    def test_mask_url_no_userinfo(self):
        url = "https://example.com"
        assert mask_url(url) == url

    def test_mask_url_multiple_at(self):
        # Should only mask the userinfo part
        url = "https://user:pass@host.com/path@something"
        assert mask_url(url) == "https://***@host.com/path@something"
