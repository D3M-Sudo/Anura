# This file is part of Anura.
# Copyright (C) 2022-2025 Andrey Maksimov (Frog)
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import os
import sys

import pytest

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from anura.utils.validators import is_safe_url_string, uri_validator


class TestSecurityHardeningLogic:
    def test_is_safe_url_string_basic(self):
        assert is_safe_url_string("https://google.com") is True
        assert is_safe_url_string(None) is False
        assert is_safe_url_string("a" * 2049) is False

    def test_is_safe_url_string_control_chars(self):
        assert is_safe_url_string("https://google.com\n") is False
        assert is_safe_url_string("https://google.com\r") is False
        assert is_safe_url_string("https://google.com\x00") is False
        assert is_safe_url_string("https://google.com\x1f") is False
        assert is_safe_url_string("https://google.com\x7f") is False

    def test_is_safe_url_string_ascii(self):
        assert is_safe_url_string("https://google.com/path") is True
        # Homograph attack (cyrillic 'o')
        assert is_safe_url_string("https://g\u043e\u043e\u0433le.com") is False

    def test_is_safe_url_string_punycode_homograph(self):
        # аpple.com in Punycode (with Cyrillic 'а')
        assert is_safe_url_string("https://xn--pple-43d.com") is False
        # googlé.com in Punycode - should be SAFE (Latin-1 supplement)
        assert is_safe_url_string("https://xn--googl-fsa.com") is True

    def test_uri_validator_integration(self):
        # uri_validator uses is_safe_url_string internally
        assert uri_validator("https://google.com\n") is False
        assert uri_validator("https://google.com") is True


def test_quote_safe_behavior():
    from urllib.parse import quote

    text = "hello/world"
    # We want to ensure we ARE using safe="" in our code.
    # This test just verifies what safe="" does.
    assert quote(text, safe="") == "hello%2Fworld"
    assert quote(text) == "hello/world"


if __name__ == "__main__":
    pytest.main([__file__])
