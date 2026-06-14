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
