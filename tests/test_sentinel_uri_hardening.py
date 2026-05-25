# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import pytest
from anura.utils.validators import is_safe_url_string, uri_validator

def test_backslash_rejection():
    """Verify that backslashes in URLs are rejected for security hardening."""
    # These currently pass in v0.1.5 but should be rejected
    assert is_safe_url_string("https://google.com\\evil.com") is False
    assert uri_validator("https://google.com\\evil.com") is False

    # Backslash in path should also be rejected to prevent normalization bypasses
    assert is_safe_url_string("https://google.com/path\\next") is False

def test_url_length_limit_hardening():
    """Verify that URL length limit is synchronized to 2000 characters."""
    # 2000 characters should be the new limit to match ShareService
    valid_url = "https://example.com/" + "a" * (2000 - len("https://example.com/"))
    assert is_safe_url_string(valid_url) is True

    invalid_url = "https://example.com/" + "a" * (2001 - len("https://example.com/"))
    assert is_safe_url_string(invalid_url) is False
