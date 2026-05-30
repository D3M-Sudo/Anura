# This file is part of Anura.
# Copyright (C) 2022-2025 Andrey Maksimov (Frog)
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import pytest
import sys
from unittest.mock import MagicMock, patch

pytest.importorskip("gi")

# Mock Adw before imports
sys.modules['gi.repository.Adw'] = MagicMock()

from anura.services.share_service import ShareService


class TestShareServiceEnterprise:
    """
    Enterprise-grade unit tests for ShareService.
    """

    @pytest.fixture
    def service(self):
        with patch("gi.repository.Gtk.UriLauncher", return_value=MagicMock()):
            return ShareService()

    def test_providers_list(self, service):
        """Test that the providers list is correct and non-empty."""
        providers = service.providers()
        assert isinstance(providers, list)
        assert len(providers) > 0
        assert "email" in providers
        assert "x" in providers
        assert "mastodon" in providers

    @pytest.mark.parametrize(
        "provider, text, expected_part",
        [
            ("telegram", "hello", "t.me/share/url?text=hello"),
            ("x", "hello world", "x.com/intent/tweet?text=hello%20world"),
            ("email", "hi", "mailto:?subject="),
            ("mastodon", "test", "web+mastodon://share?text=test"),
            ("bluesky", "blue", "bsky.app/intent/compose?text=blue"),
            ("reddit", "short", "reddit.com/submit?title=short&selftext=short"),
            ("reddit", "a" * 101, "reddit.com/submit?selftext=" + "a" * 101),
            ("linkedin", "pro", "linkedin.com/sharing/share-offsite/"),
            ("threads", "thread", "threads.net/intent/post?text=thread"),
        ],
    )
    def test_link_generation_happy_path(self, service, provider, text, expected_part):
        """Test that link generation works correctly for various providers."""
        handler = getattr(service, f"get_link_{provider}")
        link = handler(text)
        assert expected_part in link

    @pytest.mark.parametrize("provider", ShareService.providers())
    def test_link_generation_empty_input(self, service, provider):
        """Test link generation with empty or whitespace input."""
        handler = getattr(service, f"get_link_{provider}")
        assert handler("") == ""
        assert handler("   ") == ""
        assert handler(None) == ""

    @pytest.mark.parametrize(
        "url, expected",
        [
            ("mailto:test@example.com", True),
            ("web+mastodon://share?text=hi", True),
            ("https://google.com", True),
            ("http://localhost", True),
            ("ftp://evil.com", False),
            ("file:///etc/passwd", False),
            ("javascript:alert(1)", False),
            ("", False),
            (None, False),
        ],
    )
    def test_validate_share_url(self, url, expected):
        """Test share URL validation logic."""
        assert ShareService._validate_share_url(url) == expected

    def test_share_empty_text(self, service):
        """Test share method with empty text does nothing."""
        with patch("loguru.logger.warning") as mock_log:
            service.share("email", "")
            mock_log.assert_called_with("Anura Share: Attempted to share empty text.")
            service.launcher.launch.assert_not_called()

    def test_share_unknown_provider(self, service):
        """Test share method with unknown provider."""
        with patch("loguru.logger.warning") as mock_log:
            service.share("unknown", "some text")
            mock_log.assert_called_with("Anura Share: Unknown provider 'unknown' - no handler found")
            service.launcher.launch.assert_not_called()

    def test_share_url_too_long(self, service):
        """Test share method with excessively long URL."""
        long_text = "a" * 3000
        with patch("loguru.logger.warning") as mock_log:
            service.share("email", long_text)
            # Check if warning was called with a message containing "too long"
            args, _ = mock_log.call_args
            assert "too long" in args[0]
            service.launcher.launch.assert_not_called()

    @pytest.mark.gtk
    def test_share_happy_path(self, service):
        """Test successful share execution."""
        service.share("email", "valid text")
        service.launcher.set_uri.assert_called()
        service.launcher.launch.assert_called()

    def test_referential_transparency_handlers(self, service):
        """Test that link handlers are pure."""
        text = "stable text"
        for p in service.providers():
            handler = getattr(service, f"get_link_{p}")
            assert handler(text) == handler(text)

    def test_mastodon_special_handling(self, service):
        """Test Mastodon specific share flow with fallback."""
        # Test long URL path for Mastodon
        long_text = "a" * 2500
        with patch("loguru.logger.warning") as mock_log:
            service.share("mastodon", long_text)
            args, _ = mock_log.call_args
            assert "too long" in args[0]

        # Test normal Mastodon share
        service.share("mastodon", "hello")
        service.launcher.set_uri.assert_called_with("web+mastodon://share?text=hello")
        service.launcher.launch.assert_called()
