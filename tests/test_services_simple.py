# This file is part of Anura.
# Copyright (C) 2022-2025 Andrey Maksimov (Frog)
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import pytest


class TestShareServiceLogic:
    """
    Test ShareService static methods and link generation.

    NOTE: These tests import from `anura.services.share_service` which requires
    `gi` (PyGObject) at module level. If `gi` is unavailable the whole class is
    skipped automatically.
    """

    @pytest.fixture(autouse=True)
    def _skip_without_gi(self):
        pytest.importorskip("gi")
        import gi

        gi.require_version("Gtk", "4.0")
        gi.require_version("Gio", "2.0")
        gi.require_version("GLib", "2.0")
        gi.require_version("GObject", "2.0")
        gi.require_version("Adw", "1")

    def test_validate_share_url_valid_http(self):
        """Test validation of valid HTTP URLs."""
        # Import the validation function from ShareService
        from anura.services.share_service import ShareService

        valid_urls = [
            "https://example.com",
            "http://localhost:8080",
            "https://mastodon.social",
            "https://example.com/path?query=value",
        ]

        for url in valid_urls:
            assert ShareService._validate_share_url(url) is True

    def test_validate_share_url_valid_special_schemes(self):
        """Test validation of special scheme URLs."""
        from anura.services.share_service import ShareService

        special_urls = [
            "mailto:test@example.com",
            "web+mastodon://share?text=hello",
        ]

        for url in special_urls:
            assert ShareService._validate_share_url(url) is True

    def test_validate_share_url_invalid(self):
        """Test validation of invalid URLs."""
        from anura.services.share_service import ShareService

        invalid_urls = [
            "ftp://example.com",
            "javascript:alert('xss')",
            "",
            None,
            "not-a-url",
        ]

        for url in invalid_urls:
            assert ShareService._validate_share_url(url) is False

    def test_get_link_email(self):
        """Test email link generation."""
        from anura.services.share_service import ShareService

        text = "Hello World"
        link = ShareService.get_link_email(text)
        assert link.startswith("mailto:?")
        assert "subject=" in link
        assert "body=" in link
        assert "Hello+World" in link or "Hello%20World" in link

    def test_get_link_reddit(self):
        """Test Reddit link generation."""
        from anura.services.share_service import ShareService

        text = "Hello world"
        link = ShareService.get_link_reddit(text)
        # Since text is short (< 100 char): it should include title
        expected = "https://www.reddit.com/submit?title=Hello%20world&selftext=Hello%20world"
        assert link == expected

    def test_get_link_telegram(self):
        """Test Telegram link generation."""
        from anura.services.share_service import ShareService

        text = "Hello World"
        link = ShareService.get_link_telegram(text)
        assert "t.me/share/url" in link
        assert "text=" in link
        # Check for either URL encoding format
        assert "Hello+World" in link or "Hello%20World" in link or "Hello World" in link

    def test_get_link_x(self):
        """Test X (Twitter) link generation."""
        from anura.services.share_service import ShareService

        text = "Hello world"
        link = ShareService.get_link_x(text)
        assert "x.com/intent/tweet" in link
        assert "text=" in link
        # Check for either URL encoding format
        assert "Hello+world" in link or "Hello%20world" in link or "Hello world" in link

    def test_get_link_mastodon(self):
        """Test Mastodon link generation."""
        from anura.services.share_service import ShareService

        text = "Hello World"
        link = ShareService.get_link_mastodon(text)
        assert "web+mastodon://share" in link
        assert "text=" in link
        # Check for either URL encoding format
        assert "Hello+World" in link or "Hello%20World" in link or "Hello World" in link

    def test_providers(self):
        """Test provider list."""
        from anura.services.share_service import ShareService

        providers = ShareService.providers()
        expected = ["email", "mastodon", "reddit", "telegram", "x", "bluesky", "discord", "linkedin", "threads"]
        assert providers == expected
