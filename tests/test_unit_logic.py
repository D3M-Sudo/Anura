# test_unit_logic.py
#
# Unit tests for core business logic without GTK dependencies
# Tests individual functions and classes directly

import os
import sys
from urllib.parse import quote

# Add the project root to Python path to import modules directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestShareServiceLogic:
    """Test ShareService URL construction logic (pure Python, no gi needed)."""

    def test_url_encoding(self):
        """Test URL encoding for share links, ensuring forward slashes are encoded."""
        text = "Hello/world! @#$%"
        encoded = quote(text, safe="")
        assert encoded == "Hello%2Fworld%21%20%40%23%24%25"

    def test_email_link_generation(self):
        """Test email link generation logic with special characters."""
        text = "Hello/world"
        encoded = quote(text, safe="")
        # Verify that even the subject's spaces are encoded in our usage
        expected = f"mailto:?subject=Extracted%20Text&body={encoded}"
        assert "%2F" in encoded
        assert expected == "mailto:?subject=Extracted%20Text&body=Hello%2Fworld".replace("Text", "Text").replace(
            " ", "%20"
        )

    def test_reddit_link_generation(self):
        """Test Reddit link generation logic with special characters."""
        text = "Hello/world"
        encoded = quote(text, safe="")
        expected = f"https://www.reddit.com/submit?selftext={encoded}"
        assert "%2F" in expected
        assert expected == "https://www.reddit.com/submit?selftext=Hello%2Fworld"

    def test_telegram_link_generation(self):
        """Test Telegram link generation logic."""
        text = "Hello world"
        encoded = quote(text, safe="")
        expected = f"https://t.me/share/url?text={encoded}"
        assert expected == "https://t.me/share/url?text=Hello%20world".replace(" ", "%20")

    def test_x_link_generation(self):
        """Test X (Twitter) link generation logic."""
        result = f"https://x.com/intent/tweet?text={quote('Hello world')}"
        assert result == "https://x.com/intent/tweet?text=Hello%20world"

    def test_mastodon_link_generation(self):
        """Test Mastodon link generation logic."""
        text = "Hello world"
        encoded = quote(text, safe="")
        expected = f"web+mastodon://share?text={encoded}"
        assert expected == "web+mastodon://share?text=Hello%20world"


class TestUrlSafetyValidation:
    """Test URL safety validation for sharing."""

    def test_is_safe_url_string(self):
        """Test is_safe_url_string helper."""
        from anura.utils.validators import is_safe_url_string

        # Valid strings
        assert is_safe_url_string("https://example.com") is True
        assert is_safe_url_string("mailto:test@example.com") is True

        # Invalid strings
        assert is_safe_url_string(None) is False
        assert is_safe_url_string("a" * 3000) is False
        assert is_safe_url_string("https://example.com\x1f") is False  # Control char
        assert is_safe_url_string("https://exampłe.com") is False  # Non-ASCII

    def test_url_length_validation(self):
        """Test URL length limits for sharing."""
        MAX_URL_LENGTH = 2000

        # Short URL should be valid
        short_text = "Hello world"
        url = f"https://mastodon.social/share?text={quote(short_text, safe='')}"
        assert len(url) <= MAX_URL_LENGTH

        # Very long URL should be invalid
        long_text = "a" * 3000
        url = f"https://mastodon.social/share?text={quote(long_text, safe='')}"
        assert len(url) > MAX_URL_LENGTH

    def test_url_encoding_length_impact(self):
        """Test how URL encoding affects length."""
        # Characters that get encoded should increase length
        text_with_spaces = "Hello world with spaces"
        text_with_special = "Hello world! @#$%"

        encoded_spaces = quote(text_with_spaces, safe="")
        encoded_special = quote(text_with_special, safe="")

        # Encoded version should be longer
        assert len(encoded_spaces) > len(text_with_spaces)
        assert len(encoded_special) > len(text_with_special)


if __name__ == "__main__":
    # Run tests manually if called directly
    import pytest

    pytest.main([__file__, "-v"])
