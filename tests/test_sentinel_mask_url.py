# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import pytest
from anura.utils.validators import mask_url

class TestMaskUrl:
    @pytest.mark.parametrize(
        "url, expected",
        [
            ("http://user:pass@google.com", "http://***:***@google.com"),
            ("https://admin:12345@github.com/path", "https://***:***@github.com/path"),
            ("ftp://user@example.com", "ftp://***@example.com"),
            ("http://:password@google.com", "http://:***@google.com"),
            ("http://user:@google.com", "http://***:@google.com"),
            ("http://:@google.com", "http://:@google.com"),
            ("https://google.com", "https://google.com"),
            ("file:///etc/passwd", "file:///etc/passwd"),
            ("", ""),
            (None, ""),
            ("not-a-url", "not-a-url"),
            ("http://user:pass@evil.com@google.com", "http://***:***@google.com"), # rpartition behavior
        ]
    )
    def test_mask_url(self, url, expected):
        assert mask_url(url) == expected
