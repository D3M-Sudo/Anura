# This file is part of Anura.
# Copyright (C) 2022-2025 Andrey Maksimov (Frog)
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import pytest

pytest.importorskip("gi")


from unittest.mock import MagicMock, patch

from anura.services.clipboard_service import ClipboardService


class TestClipboardServiceEnterprise:
    """
    Enterprise-grade unit tests for ClipboardService.
    Safe for VM/headless by mocking Gdk.Clipboard.
    """

    @pytest.fixture
    def service(self):
        with patch("gi.repository.Gdk.Display.get_default") as mock_display_get:
            mock_display = MagicMock()
            mock_display_get.return_value = mock_display
            mock_clipboard = MagicMock()
            mock_display.get_clipboard.return_value = mock_clipboard

            # Directly instantiate
            return ClipboardService()

    def test_init(self, service):
        """Test basic initialization."""
        # _clipboard is lazy-initialized in the property, so it starts None
        assert service._clipboard is None
        assert service._cancellable is None

    def test_copy_text_trigger(self, service):
        """Test that copy_text triggers clipboard set_content (GTK4 API).

        GTK4 removed Gdk.Clipboard.set_text().  The production code wraps the
        string in a GLib.Variant("s", ...) and passes it to
        Gdk.ContentProvider.new_for_value(), then calls clipboard.set_content().
        We mock both the ContentProvider factory and the clipboard property so
        the test remains headless-safe and asserts the correct GTK4 call path.
        """
        from unittest.mock import PropertyMock

        mock_clipboard = MagicMock()
        mock_content_provider = MagicMock()

        with (
            patch.object(ClipboardService, "clipboard", new_callable=PropertyMock) as mock_cb_prop,
            patch("gi.repository.Gdk.ContentProvider.new_for_value", return_value=mock_content_provider),
            patch("gi.repository.GLib.Variant"),
            patch("gi.repository.GLib.timeout_add_seconds") as mock_timeout,
        ):
            mock_cb_prop.return_value = mock_clipboard
            service.copy_text("Enterprise Audit")
            # GTK4: set_content() replaces the removed set_text()
            mock_clipboard.set_content.assert_called_once_with(mock_content_provider)
            assert mock_timeout.called

    def test_cancel_pending_operations(self, service):
        """Test atomic cancellation logic."""
        mock_cancellable = MagicMock()
        mock_cancellable.is_cancelled.return_value = False
        service._cancellable = mock_cancellable
        service._clipboard_timeout_id = 1234

        with patch("gi.repository.GLib.source_remove") as mock_remove:
            service.cancel_pending_operations()
            mock_cancellable.cancel.assert_called_once()
            mock_remove.assert_called_with(1234)
            assert service._cancellable is None
            assert service._clipboard_timeout_id is None

    def test_on_clipboard_timeout(self, service):
        """Test timeout handling."""
        mock_cancellable = MagicMock()
        mock_cancellable.is_cancelled.return_value = False
        service._cancellable = mock_cancellable  # Must be the same object for active timeout check

        with patch("gi.repository.GLib.idle_add") as mock_idle:
            # result should be SOURCE_REMOVE (False)
            res = service._on_clipboard_timeout(mock_cancellable)
            assert res is False
            mock_cancellable.cancel.assert_called_once()
            assert mock_idle.called
