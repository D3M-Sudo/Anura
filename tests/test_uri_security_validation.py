# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import pytest

from anura.utils.validators import is_safe_url_string, uri_validator


class TestSentinelUriSecurity:
    """Security tests for URI validation hardening."""

    @pytest.mark.parametrize(
        "char",
        [
            "\x80",
            "\x81",
            "\x90",
            "\x9f",  # C1 Control characters
            "\x00",
            "\x1f",
            "\x7f",  # C0 and DEL
        ],
    )
    def test_control_characters_rejected(self, char):
        url = f"https://example.com/{char}"
        assert is_safe_url_string(url) is False
        assert uri_validator(url) is False

    @pytest.mark.parametrize(
        "char",
        [
            "\u200b",  # Zero Width Space (Cf)
            "\u200c",  # Zero Width Non-Joiner (Cf)
            "\u200d",  # Zero Width Joiner (Cf)
            "\u200e",  # Left-To-Right Mark (Cf)
            "\u200f",  # Right-To-Left Mark (Cf)
            "\u00ad",  # Soft Hyphen (Cf)
        ],
    )
    def test_format_characters_rejected(self, char):
        # Format characters can be used for spoofing or bypassing filters
        url = f"https://example.com/{char}path"
        assert is_safe_url_string(url) is False
        assert uri_validator(url) is False

    def test_valid_url_still_works(self):
        url = "https://example.com/path?query=1"
        assert is_safe_url_string(url) is True
        assert uri_validator(url) is True

    def test_homograph_attack_rejected_via_ascii_check(self):
        # Cyrillic 'a' (U+0430) instead of Latin 'a'
        url = "https://ex\u0430mple.com"
        assert is_safe_url_string(url) is False
        assert uri_validator(url) is False

    def test_idn_userinfo_spoofing_rejected(self):
        # BUG-047: Ensure that if the hostname appears in userinfo, it is not
        # incorrectly replaced during Punycode normalization.
        # This URL has 'münchen.de' as both username and hostname.
        url = "https://m\u00fcnchen.de@m\u00fcnchen.de"
        # is_safe_url_string should return False because after Punycode normalization
        # of the HOSTNAME, the USERNAME still contains non-ASCII characters.
        assert is_safe_url_string(url) is False
        # uri_validator should also reject it (both for unsafe string and for having userinfo)
        assert uri_validator(url) is False

    def test_idn_with_userinfo_normalization(self):
        # Legitimate IDN with ASCII userinfo should normalize correctly
        url = "https://user:pass@m\u00fcnchen.de"
        # It's a "safe" URL string in terms of characters (after normalization it's ASCII)
        assert is_safe_url_string(url) is True
        # But uri_validator rejects it because it has userinfo (security policy)
        assert uri_validator(url) is False

    def test_idn_with_encoded_userinfo(self):
        # BUG-047: Ensure percent-encoding in userinfo is preserved
        # %40 is '@'. Reconstructing from decoded components would break this.
        url = "https://user%40name:pass@m\u00fcnchen.de"
        assert is_safe_url_string(url) is True
        # Result should preserve %40
        from anura.utils.validators import _normalize_idn

        normalized = _normalize_idn(url)
        assert "user%40name" in normalized
        assert "xn--mnchen-3ya.de" in normalized

    def test_idn_with_empty_username(self):
        # BUG-047: Handle empty username with password correctly
        url = "https://:password@m\u00fcnchen.de"
        assert is_safe_url_string(url) is True
        from anura.utils.validators import _normalize_idn

        normalized = _normalize_idn(url)
        assert ":password@" in normalized
        assert "xn--mnchen-3ya.de" in normalized
