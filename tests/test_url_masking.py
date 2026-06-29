from anura.utils.validators import mask_url


def test_mask_url_with_credentials():
    """Verify that credentials are redacted from various URL schemes."""
    assert mask_url("https://user:password@example.com") == "https://***:***@example.com"
    assert mask_url("http://admin@localhost:8080") == "http://***:***@localhost:8080"
    assert (
        mask_url("ftp://guest:secret@ftp.server.org/path") == "ftp://***:***@ftp.server.org/path"
    )


def test_mask_url_no_credentials():
    """Verify that URLs without credentials remain unchanged."""
    assert mask_url("https://google.com") == "https://google.com"
    assert (
        mask_url("https://google.com/path?query=val") == "https://google.com/path?query=val"
    )


def test_mask_url_empty_userinfo():
    """Verify that empty userinfo (e.g. :@) is correctly handled and masked."""
    # urlparse might handle :@ differently, but we want it masked if @ is present
    assert mask_url("https://:@google.com") == "https://***:***@google.com"


def test_mask_url_malformed():
    """Verify that malformed URLs are handled gracefully."""
    # Depending on how urlparse handles it, it might return the original or the placeholder
    # For "not a url", urlparse usually returns it as a path if no scheme
    assert mask_url("not a url") == "not a url"

    # Very malformed ones that might raise ValueError during parsing or unparsing
    # (though urlparse is very lenient)
    assert mask_url("http://[invalid-bracket") == "[REDACTED INVALID URL]"


def test_mask_url_edge_cases():
    """Verify edge cases like empty string or None."""
    assert mask_url("") == ""
    assert mask_url(None) == ""


def test_mask_url_schemeless_credentials():
    """Verify that credentials in schemeless URL-like strings are redacted."""
    # Common OCR result for a URL with credentials
    assert mask_url("user:password@example.com") == "***:***@example.com"
    assert mask_url("admin@localhost") == "***:***@localhost"
    assert mask_url(":password@localhost") == "***:***@localhost"
    assert mask_url("user:@localhost") == "***:***@localhost"


def test_mask_url_schemeless_no_credentials():
    """Verify that schemeless strings without credentials remain unchanged."""
    assert mask_url("example.com") == "example.com"
    assert mask_url("google.com/path") == "google.com/path"


def test_mask_url_path_with_at_no_redaction():
    """Verify that '@' in a file path (no credentials) is not over-redacted."""
    # If @ is after a slash, it's treated as part of the path, not credentials
    assert mask_url("/home/user@name/file.txt") == "/home/user@name/file.txt"
    assert mask_url("example.com/path@target") == "example.com/path@target"


def test_mask_url_email_like_strings():
    """Verify how email-like strings are handled by mask_url."""
    # mask_url is primarily for URLs, but it should fail-safe on emails too
    # if they appear before any path separators.
    assert mask_url("user@example.com") == "***:***@example.com"

    # Email in a path (less common, but should be preserved if after /)
    assert mask_url("contact/info@example.com") == "contact/info@example.com"


def test_mask_url_regression_schemed_complex():
    """Verify complex schemed URL masking still works."""
    assert (
        mask_url("https://google.com/path?user=pass@evil.com")
        == "https://google.com/path?user=pass@evil.com"
    )
