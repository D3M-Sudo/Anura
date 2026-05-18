# tests/test_unit_validators_enterprise.py
import pytest

pytest.importorskip("gi")


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
        "url",
        [
            "https://googlé.com",  # Non-ASCII
            "https://\u0430\u043f\u0440.com",  # Cyrillic homograph
            "https://\u202e/moc.elgoog",  # Right-to-left override
        ],
    )
    def test_non_ascii_and_homograph(self, url):
        """Test non-ASCII characters and potential homograph attacks."""
        assert uri_validator(url) is False

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
        # uri_validator expects a string.
        with pytest.raises(TypeError):
            uri_validator(url)

    def test_referential_transparency(self):
        """Test that the function is pure and returns the same result for the same input."""
        url = "https://google.com"
        assert uri_validator(url) == uri_validator(url)
        assert uri_validator(url) is True
