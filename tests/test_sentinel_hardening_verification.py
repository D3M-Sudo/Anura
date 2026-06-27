# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import pytest
from anura.utils.validators import sanitize_text, is_safe_url_string

def test_verify_hardening():
    """
    Verify the hardened behavior.
    """
    # 1. sanitize_text should now strip \r
    assert "\r" not in sanitize_text("line1\r\nline2")
    assert sanitize_text("line1\r\nline2") == "line1\nline2"

    # 2. is_safe_url_string should now block < > "
    assert is_safe_url_string("https://example.com/<script>") is False
    assert is_safe_url_string("https://example.com/>") is False
    assert is_safe_url_string('https://example.com/"') is False

    # Ensure backslashes are still blocked (regression check)
    assert is_safe_url_string("https://example.com\\evil") is False

if __name__ == "__main__":
    pytest.main([__file__])
