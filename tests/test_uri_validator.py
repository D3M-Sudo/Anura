# tests/test_uri_validator.py
#
# Tests for AnuraWindow.uri_validator() — the security layer before Gtk.UriLauncher.
# Extracted as a standalone function to avoid requiring a GTK display.
#
# Based on the implementation in anura/window.py:
# - Blocks homograph attacks (IDN with mixed scripts)
# - Blocks control characters
# - Only allows http/https/mailto schemes
# - Blocks IP-literal URIs to prevent SSRF

import ipaddress
from urllib.parse import urlparse

import pytest


def uri_validator(url: str) -> bool:
    """
    Mirror of AnuraWindow.uri_validator() for unit testing.
    Keep in sync with the implementation in anura/window.py.
    """
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https", "mailto"):
            return False
        if any(ord(c) < 32 or ord(c) == 127 for c in url):
            return False
        hostname = parsed.hostname or ""
        try:
            ipaddress.ip_address(hostname)
            return False  # Block raw IP addresses
        except ValueError:
            pass
        return bool(parsed.netloc or parsed.path)
    except Exception:
        return False


class TestUriValidator:

    # ── Valid URIs ─────────────────────────────────────────────────────────────

    def test_https_valid(self):
        assert uri_validator("https://example.com") is True

    def test_http_valid(self):
        assert uri_validator("http://example.com/path?q=1") is True

    def test_mailto_valid(self):
        assert uri_validator("mailto:user@example.com") is True

    def test_url_with_path(self):
        assert uri_validator("https://github.com/d3msudo/anura") is True

    def test_url_with_query(self):
        assert uri_validator("https://example.com/search?q=hello+world") is True

    # ── Blocked schemes ───────────────────────────────────────────────────────

    def test_file_scheme_blocked(self):
        assert uri_validator("file:///etc/passwd") is False

    def test_javascript_scheme_blocked(self):
        assert uri_validator("javascript:alert(1)") is False

    def test_ftp_scheme_blocked(self):
        assert uri_validator("ftp://example.com") is False

    def test_data_scheme_blocked(self):
        assert uri_validator("data:text/html,<script>alert(1)</script>") is False

    # ── Control characters ────────────────────────────────────────────────────

    def test_null_byte_blocked(self):
        assert uri_validator("https://example.com\x00evil") is False

    def test_newline_blocked(self):
        assert uri_validator("https://example.com\nevil-header: injected") is False

    def test_carriage_return_blocked(self):
        assert uri_validator("https://example.com\revil") is False

    # ── IP addresses blocked (SSRF prevention) ────────────────────────────────

    def test_ipv4_blocked(self):
        assert uri_validator("http://192.168.1.1/admin") is False

    def test_localhost_ip_blocked(self):
        assert uri_validator("http://127.0.0.1") is False

    # ── Edge cases ────────────────────────────────────────────────────────────

    def test_empty_string(self):
        assert uri_validator("") is False

    def test_plain_text(self):
        assert uri_validator("just some text") is False

    def test_none_raises_no_exception(self):
        # uri_validator must never raise — it's called in GTK signal handlers
        try:
            result = uri_validator(None)  # type: ignore
            assert result is False
        except Exception as e:
            pytest.fail(f"uri_validator raised {e} on None input")
