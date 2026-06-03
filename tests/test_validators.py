# This file is part of Anura.
# Copyright (C) 2022-2025 Andrey Maksimov (Frog)
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import pytest

from anura.utils.validators import uri_validator


class TestUriValidatorEnterprise:
    """
    Enterprise-grade unit tests for uri_validator.
    """

    @pytest.mark.parametrize(
        "url",
        [
            "https://google.com",
            "http://example.org",
            "https://sub.domain.tld/path?query=1#fragment",
            "http://localhost:8080",
            "https://127.0.0.1",
            "https://[::1]",
            "https://192.168.1.1/admin",
            "http://my.local.server/api",
        ],
    )
    def test_happy_path(self, url):
        """Test normal, valid URLs."""
        assert uri_validator(url) is True

    @pytest.mark.parametrize(
        "url",
        [
            "",
            "   ",
            None,
        ],
    )
    def test_empty_or_null(self, url):
        """Test empty, null, or whitespace-only input."""
        assert uri_validator(url) is False

    @pytest.mark.parametrize(
        "url",
        [
            "https://a" * 2049,  # Too long
            "https://google.com\x00",  # Null byte
            "https://google.com\n",  # Newline
            "https://google.com\r",  # Carriage return
            "https://google.com\x1f",  # Unit separator
            "https://google.com\x7f",  # DEL
        ],
    )
    def test_invalid_chars_and_length(self, url):
        """Test boundary values for length and control characters."""
        assert uri_validator(url) is False

    @pytest.mark.parametrize(
        "url,expected",
        [
            ("https://googlé.com", True),  # Latin-1 is allowed (NEW-011)
            ("https://münchen.de", True),  # Legitimate IDN allowed
            ("https://\u0430\u043f\u0440.com", False),  # Cyrillic homograph mixed with ASCII (if label was mixed)
            # Note: Pure Cyrillic IDNs are encoded as Punycode and may pass ASCII safety if not mixed.
            # But \u202e (RLO) is stripped/blocked.
            ("https://\u202e/moc.elgoog", False),
        ],
    )
    def test_non_ascii_and_homograph(self, url, expected):
        """Test non-ASCII characters and potential homograph attacks."""
        assert uri_validator(url) is expected

    @pytest.mark.parametrize(
        "text,expected",
        [
            ("Normal text", "Normal text"),
            ("Text with \n newline", "Text with \n newline"),
            ("Text with \uE000 private use", "Text with private use"),
            ("Text with \uD800 surrogate", "Text with surrogate"),
            ("Text with \u202E RLO", "Text with RLO"),
            ("Mixed \uE000 and \n inside", "Mixed and \n inside"),
            ("Text with \u088F unassigned", "Text with unassigned"),  # Cn category
            ("e\u0301", "é"),  # NFC Normalization: 'e' + combining acute -> 'é'
        ],
    )
    def test_sanitize_text_hardening(self, text, expected):
        """Test that sanitize_text strips dangerous Unicode categories and normalizes."""
        from anura.utils.validators import sanitize_text

        assert sanitize_text(text) == expected

    def test_sanitize_text_length_limit(self):
        """Test that sanitize_text enforces the MAX_TEXT_LENGTH limit."""
        from anura.config import MAX_TEXT_LENGTH
        from anura.utils.validators import sanitize_text

        long_text = "a" * (MAX_TEXT_LENGTH + 100)
        sanitized = sanitize_text(long_text)
        assert len(sanitized) == MAX_TEXT_LENGTH
        assert sanitized == "a" * MAX_TEXT_LENGTH

    @pytest.mark.parametrize(
        "url",
        [
            "ftp://example.com",
            "file:///etc/passwd",
            "javascript:alert(1)",
            "data:text/html,<html>",
            "ssh://root@server",
            "gopher://classic.net",
        ],
    )
    def test_unsupported_schemes(self, url):
        """Test unsupported or dangerous URI schemes."""
        assert uri_validator(url) is False

    @pytest.mark.parametrize(
        "url",
        [
            "https://user:pass@google.com",
            "http://admin@evil.com",
            "https://:password@github.com",
        ],
    )
    def test_userinfo_spoofing(self, url):
        """Test prevention of userinfo spoofing."""
        assert uri_validator(url) is False

    @pytest.mark.parametrize(
        "url",
        [
            "http://evil",
            "https://localhost-fake",
            "http://com",
        ],
    )
    def test_single_word_hostnames(self, url):
        """Test rejection of single-word hostnames without dots (except localhost)."""
        assert uri_validator(url) is False

    @pytest.mark.parametrize(
        "url",
        [
            123,
            ["https://google.com"],
            {"url": "https://google.com"},
        ],
    )
    def test_invalid_types(self, url):
        """Test invalid input types."""
        # uri_validator should return False for non-string types
        assert uri_validator(url) is False

    def test_referential_transparency(self):
        """Test that the function is pure and returns the same result for the same input."""
        url = "https://google.com"
        assert uri_validator(url) == uri_validator(url)
        assert uri_validator(url) is True
