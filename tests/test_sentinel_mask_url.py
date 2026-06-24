# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import pytest

from anura.utils import mask_url


class TestSentinelMaskUrl:
    """Security tests for URL masking logic."""

    @pytest.mark.parametrize(
        "url,expected",
        [
            # Standard URLs without credentials
            ("https://google.com", "https://google.com"),
            ("https://google.com/path?query=1#frag", "https://google.com/path?query=1#frag"),
            ("http://localhost:8080", "http://localhost:8080"),

            # URLs with credentials
            ("https://user:pass@google.com", "https://***:***@google.com"),
            ("http://admin:secret123@internal.net/config", "http://***:***@internal.net/config"),
            ("https://onlyuser@github.com", "https://***@github.com"),
            ("https://:onlypass@example.com", "https://:***@example.com"),

            # Special characters in credentials
            ("https://user%40name:p%23ss@google.com", "https://***:***@google.com"),

            # Empty credentials but @ present
            ("http://:@google.com", "http://:@google.com"),
            ("http://@google.com", "http://@google.com"),

            # IP addresses
            ("https://1.2.3.4", "https://1.2.3.4"),
            ("https://admin:pass@127.0.0.1:8443", "https://***:***@127.0.0.1:8443"),

            # File URIs
            ("file:///etc/passwd", "file:///etc/passwd"),
            ("file://host/path", "file://host/path"),
            ("file://user:pass@host/path", "file://***:***@host/path"),

            # Edge cases and malformed
            (None, None),
            ("", ""),
            (123, 123),
            ("not a url", "not a url"),
            ("https://@malformed", "https://@malformed"),
        ]
    )
    def test_mask_url_behavior(self, url, expected):
        assert mask_url(url) == expected

    def test_mask_url_conservative_fallback(self):
        # Test the fallback logic for malformed strings that look like they have credentials
        malformed = "https://user:pass@malformed:not:a:port"
        # Since urlparse might fail or return weird results, we check if it's at least masked
        result = mask_url(malformed)
        assert "***" in result or "masked" in result

    def test_mask_url_idn(self):
        url = "https://user:pass@m\u00fcnchen.de"
        # It should mask correctly even with IDN in hostname
        result = mask_url(url)
        assert "user" not in result
        assert "pass" not in result
        assert "***:***@" in result
