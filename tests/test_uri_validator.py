# tests/test_uri_validator.py
#
# Tests for anura.utils.validators.uri_validator() — the security layer before Gtk.UriLauncher.

import pytest

from anura.utils.validators import uri_validator


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

    # ── Security: Blocked userinfo spoofing ──────────────────────────────────

    def test_userinfo_spoofing_blocked(self):
        assert uri_validator("http://google.com@evil.com") is False
        assert uri_validator("http://user:pass@example.com") is False
        assert uri_validator("https://admin:secret@localhost:8080") is False

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
