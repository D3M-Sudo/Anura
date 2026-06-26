import pytest
from anura.utils.validators import sanitize_text, is_safe_url_string

def test_sanitize_text_strips_carriage_return():
    """Verify that \r is now stripped to prevent terminal UI spoofing."""
    input_text = "Line 1\rLine 2"
    # Previously this would be "Line 1\rLine 2"
    assert sanitize_text(input_text) == "Line 1Line 2"

def test_is_safe_url_string_blocks_dangerous_chars():
    """Verify that <, >, and \" are now blocked in URLs."""
    assert is_safe_url_string("https://example.com/<script>") is False
    assert is_safe_url_string("https://example.com/>") is False
    assert is_safe_url_string("https://example.com/\"") is False
    # Normal URL should still work
    assert is_safe_url_string("https://example.com/path?q=1") is True

def test_sanitize_text_preserves_allowed_whitespace():
    """Verify that \n is preserved and \t is squashed to space (current behavior)."""
    input_text = "Line 1\n\tLine 2"
    # Note: sanitize_text squashes [ \t]+ to " "
    assert sanitize_text(input_text) == "Line 1\n Line 2"
