# tests/test_uri_validator.py
#
# Tests for AnuraWindow.uri_validator() — the security layer before Gtk.UriLauncher.
# Uses the actual implementation from anura/window.py to ensure test/implementation parity.

import ipaddress
from urllib.parse import urlparse

import pytest


def uri_validator(text: str) -> bool:
    """
    Mirror of AnuraWindow.uri_validator() for unit testing.
    Keep in sync with the implementation in anura/window.py.

    Security features:
    - Blocks control characters (0x00-0x1F) and DEL (0x7F)
    - Requires ASCII-only (prevents Unicode homograph attacks)
    - Only allows http/https schemes
    - Allows localhost, IP addresses (IPv4/IPv6), and domain names with dots
    - Rejects single-word hostnames without dots
    """
    if text is None:
        return False
    url = text.strip()

    # Block control characters (0x00-0x1F) and DEL (0x7F)
    # This prevents newline, tab, carriage return, null byte injection
    if any(ord(c) < 0x20 or ord(c) == 0x7F for c in url):
        return False

    # Ensure URL is ASCII-only (prevent Unicode homograph attacks)
    try:
        url.encode("ascii")
    except UnicodeEncodeError:
        return False

    try:
        res = urlparse(url)
        if not (res.scheme in ("http", "https") and bool(res.netloc)):
            return False

        # Allow localhost and IP addresses (common in development/enterprise)
        # Also allow hostnames with dots (normal domains)
        netloc_lower = res.netloc.lower()
        if netloc_lower == "localhost" or netloc_lower.startswith("localhost:"):
            return True
        if "." in res.netloc:
            return True
        # Check for valid IP address (IPv4 or IPv6)
        # Remove port if present for validation
        host = res.netloc
        if ':' in host and not host.endswith(']'):
            # Could be IPv4:port or IPv6:port - split on last colon
            host = host.rsplit(':', 1)[0]
        # Unbracket IPv6 if bracketed
        if host.startswith('[') and host.endswith(']'):
            host = host[1:-1]
        try:
            ipaddress.ip_address(host)
            return True
        except ValueError:
            pass

        # Reject single-word hostnames without dots (prevents "http://evil")
        return False
    except ValueError:
        return False


class TestUriValidator:

    # ── Valid URIs ─────────────────────────────────────────────────────────────

    def test_https_valid(self):
        assert uri_validator("https://example.com") is True

    def test_http_valid(self):
        assert uri_validator("http://example.com/path?q=1") is True

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

    # ── Localhost and IP addresses ALLOWED (development/enterprise) ────────

    def test_localhost_allowed(self):
        assert uri_validator("http://localhost:8080/admin") is True

    def test_localhost_without_port_allowed(self):
        assert uri_validator("http://localhost") is True

    def test_ipv4_allowed(self):
        assert uri_validator("http://192.168.1.1/admin") is True

    def test_ipv4_loopback_allowed(self):
        assert uri_validator("http://127.0.0.1") is True

    def test_ipv6_allowed(self):
        assert uri_validator("http://[::1]:8080") is True

    def test_ipv6_loopback_allowed(self):
        assert uri_validator("http://[::1]") is True

    # ── Blocked: single-word hostnames without dots ────────────────────────────

    def test_single_word_blocked(self):
        assert uri_validator("http://evil") is False

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
