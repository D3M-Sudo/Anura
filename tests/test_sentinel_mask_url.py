# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import pytest
from anura.utils.validators import mask_url

@pytest.mark.parametrize("url, expected", [
    # URLs with credentials
    ("http://user:pass@google.com", "http://***:***@google.com"),
    ("https://admin:secret123@github.com/repo", "https://***:***@github.com/repo"),
    ("ftp://anonymous:guest@ftp.example.com", "ftp://***:***@ftp.example.com"),

    # URLs with only username
    ("http://user@google.com", "http://***@google.com"),
    ("ssh://git@github.com", "ssh://***@github.com"),

    # URLs with empty credentials
    ("http://:@google.com", "http://***:***@google.com"),
    ("http://@google.com", "http://***@google.com"),

    # URLs without credentials
    ("https://google.com", "https://google.com"),
    ("http://localhost:8080/path?query=1", "http://localhost:8080/path?query=1"),
    ("file:///etc/passwd", "file:///etc/passwd"),

    # Malformed or edge cases
    ("", ""),
    (None, ""),
    ("not a url", "not a url"),
    ("http://google.com@evil.com", "http://***@evil.com"),
    ("http://user:pass@host:port@extra", "http://***:***@extra"),
])
def test_mask_url(url, expected):
    """Verify that mask_url correctly redacts credentials from various URIs."""
    assert mask_url(url) == expected
