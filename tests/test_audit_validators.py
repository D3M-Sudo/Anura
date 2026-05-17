import pytest
from anura.utils.validators import uri_validator

class TestAuditValidators:
    def test_uri_validator_basic(self):
        assert uri_validator("https://google.com") is True
        assert uri_validator("http://localhost:8080") is True
        assert uri_validator("https://127.0.0.1") is True

    def test_uri_validator_control_chars(self):
        assert uri_validator("https://google.com\x01") is False
        assert uri_validator("https://google.com\n") is False
        assert uri_validator("https://google.com\r") is False
        assert uri_validator("https://google.com\t") is False

    def test_uri_validator_homographs(self):
        assert uri_validator("https://googlе.com") is False

    def test_uri_validator_userinfo(self):
        assert uri_validator("https://user:pass@google.com") is False
        assert uri_validator("https://google.com@evil.com") is False

    def test_uri_validator_invalid_schemes(self):
        assert uri_validator("file:///etc/passwd") is False
        assert uri_validator("javascript:alert(1)") is False
        assert uri_validator("data:text/plain;base64,SGVsbG8=") is False

    def test_uri_validator_no_dots(self):
        assert uri_validator("https://google") is False
        assert uri_validator("http://myhost") is False

    def test_uri_validator_empty_none(self):
        assert uri_validator("") is False
        assert uri_validator(None) is False

    def test_uri_validator_ipv6(self):
        assert uri_validator("https://[::1]") is True
        assert uri_validator("https://[2001:db8::1]:8080") is True
