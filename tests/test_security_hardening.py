
import sys
import os
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
        assert is_safe_url_string("https://google.com\x1F") is False
        assert is_safe_url_string("https://google.com\x7F") is False

    def test_is_safe_url_string_ascii(self):
        assert is_safe_url_string("https://google.com/path") is True
        # Homograph attack (cyrillic 'а')
        assert is_safe_url_string("https://gооgle.com") is False

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
