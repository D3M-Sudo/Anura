# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

from anura.utils.validators import sanitize_text


def test_sanitize_text_removes_control_chars():
    # Test Null byte, Bell, and other C0 controls
    input_text = "Hello\x00World\x07!"
    assert sanitize_text(input_text) == "HelloWorld!"

def test_sanitize_text_preserves_formatting():
    # Test newlines, tabs, and carriage returns are preserved
    input_text = "Line 1\nLine 2\tTabbed\rCarriage"
    # Note: squash horizontal whitespace will change "\t" to " "
    expected = "Line 1\nLine 2 Tabbed\rCarriage"
    assert sanitize_text(input_text) == expected

def test_sanitize_text_removes_rtl_override():
    # Test U+202E (Right-to-Left Override) - Category 'Cf'
    input_text = "Check out this link: \u202Emoc.elgoog//:ptth"
    # It should be stripped
    assert sanitize_text(input_text) == "Check out this link: moc.elgoog//:ptth"

def test_sanitize_text_squashes_horizontal_whitespace():
    input_text = "Too    many    spaces\t\tand\ttabs"
    assert sanitize_text(input_text) == "Too many spaces and tabs"

def test_sanitize_text_fixes_url_ocr_errors():
    input_text = "Visit http: //example.com or https:  //secure.site"
    assert sanitize_text(input_text) == "Visit http://example.com or https://secure.site"

def test_sanitize_text_handles_empty_input():
    assert sanitize_text("") == ""
    assert sanitize_text(None) == ""

def test_sanitize_text_strips_outer_whitespace():
    assert sanitize_text("  trimmed  ") == "trimmed"
    assert sanitize_text("\n  trimmed  \n") == "trimmed"

def test_sanitize_text_complex_security_case():
    # Combination of multiple spaces, control chars, and RTL overrides
    input_text = "User: \x00 admin \u202E \x07 (pwned)"
    # 1. Strip Cc/Cf: "User:   admin   (pwned)"
    # 2. Squash spaces: "User: admin (pwned)"
    # 3. Strip outer: "User: admin (pwned)"
    assert sanitize_text(input_text) == "User: admin (pwned)"
