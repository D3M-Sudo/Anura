# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import pytest

from anura.utils.validators import is_safe_url_string, sanitize_text


class TestSentinelHardeningVerification:
    """Verification tests for security hardening of URI and text sanitization."""

    @pytest.mark.parametrize(
        "unsafe_char",
        ["|", "^", "`", "{", "}"]
    )
    def test_is_safe_url_string_blocks_additional_unsafe_chars(self, unsafe_char):
        """
        Verify that is_safe_url_string blocks characters that are generally
        considered unsafe in URLs according to RFC 1738 and others.
        Currently, some of these might PASS until the hardening is applied.
        """
        url = f"https://example.com/path?query={unsafe_char}"
        # This test is expected to FAIL before the hardening is applied
        # if the characters are not already blocked.
        assert is_safe_url_string(url) is False

    def test_sanitize_text_strips_carriage_return(self):
        """
        Verify that sanitize_text correctly strips carriage returns (\r)
        to prevent terminal UI spoofing, despite misleading comments in the code.
        """
        text = "line1\rline2"
        sanitized = sanitize_text(text)
        assert "\r" not in sanitized
        assert sanitized == "line1line2"

    def test_sanitize_text_preserves_allowed_whitespace(self):
        """
        Verify that \n and \t are preserved while \r is stripped.
        Note: sanitize_text currently squashes \t to a space via:
        text = re.sub(r"[ \t]+", " ", text)
        """
        text = "newline\nreturn\r"
        sanitized = sanitize_text(text)
        assert "\n" in sanitized
        assert "\r" not in sanitized

    def test_sanitize_text_squashes_tabs(self):
        """
        Verify that tabs are squashed to spaces (existing behavior).
        """
        text = "tab\ttext"
        sanitized = sanitize_text(text)
        assert "\t" not in sanitized
        assert " " in sanitized
