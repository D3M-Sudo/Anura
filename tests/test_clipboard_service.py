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
        ):
            mock_cb_prop.return_value = mock_clipboard
            service.copy_text("Enterprise Audit")
            # GTK4: set_content() replaces the removed set_text()
            mock_clipboard.set_content.assert_called_once_with(mock_content_provider)

    def test_cancel_pending_operations(self, service):
        """Test atomic cancellation logic."""
        mock_cancellable = MagicMock()
        mock_cancellable.is_cancelled.return_value = False
        service._cancellable = mock_cancellable
        service._clipboard_timeout_id = 1234

        with (
            patch("gi.repository.GLib.source_remove") as mock_remove,
            patch("gi.repository.GLib.MainContext.default") as mock_ctx_get,
        ):
            mock_ctx = MagicMock()
            mock_ctx_get.return_value = mock_ctx
            # Simulate source found
            mock_ctx.find_source_by_id.return_value = MagicMock()

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

    def test_fallback_texture_to_uri_list_success(self, service):
        """Test that _fallback_to_uri_list_read is called when texture read fails."""
        from unittest.mock import PropertyMock

        from gi.repository import Gio, GLib

        mock_clipboard = MagicMock()
        mock_texture_result = MagicMock()

        # Mock read_texture_finish to raise error (trigger fallback)
        error = GLib.Error.new_literal(Gio.io_error_quark(), "Texture read failed", Gio.IOErrorEnum.FAILED)
        service.clipboard.read_texture_finish.side_effect = error

        with (
            patch.object(ClipboardService, "clipboard", new_callable=PropertyMock) as mock_cb_prop,
            patch.object(service, "_fallback_to_uri_list_read") as mock_fallback,
        ):
            mock_cb_prop.return_value = mock_clipboard
            service._cancellable = MagicMock()
            service._cancellable.is_cancelled.return_value = False
            service._fallback_attempted = False

            # Trigger the callback
            service._on_read_texture(None, mock_texture_result)

            # Verify fallback was attempted
            assert service._fallback_attempted is True
            mock_fallback.assert_called_once()

    def test_fallback_guard_prevents_infinite_loop(self, service):
        """Test that _fallback_attempted guard prevents infinite fallback loops."""
        from unittest.mock import PropertyMock

        from gi.repository import Gio, GLib

        mock_clipboard = MagicMock()
        mock_texture_result = MagicMock()

        # Mock read_texture_finish to raise error
        error = GLib.Error.new_literal(Gio.io_error_quark(), "Texture read failed", Gio.IOErrorEnum.FAILED)
        service.clipboard.read_texture_finish.side_effect = error

        with (
            patch.object(ClipboardService, "clipboard", new_callable=PropertyMock) as mock_cb_prop,
            patch.object(service, "_fallback_to_uri_list_read") as mock_fallback,
            patch.object(service, "_emit_clipboard_error") as mock_error,
        ):
            mock_cb_prop.return_value = mock_clipboard
            service._cancellable = MagicMock()
            service._cancellable.is_cancelled.return_value = False

            # First call: fallback should be attempted
            service._fallback_attempted = False
            service._on_read_texture(None, mock_texture_result)
            assert service._fallback_attempted is True
            mock_fallback.assert_called_once()

            # Second call with guard set: should emit error instead of looping
            mock_fallback.reset_mock()
            service._fallback_attempted = True
            service._on_read_texture(None, mock_texture_result)
            mock_fallback.assert_not_called()
            mock_error.assert_called_once()

    def test_uri_list_no_file_uri(self, service):
        """Test _on_uri_list_bytes emits error when no file:// URI in list."""
        with patch("gi.repository.GLib.idle_add") as mock_idle_add:
            # Call with non-file URI data
            service._on_uri_list_bytes(b"http://example.com/image.png\r\n")
            # Verify error was emitted
            assert mock_idle_add.called

    def test_uri_list_file_not_exists(self, service):
        """Test _on_uri_list_bytes emits error when file doesn't exist."""
        with (
            patch("gi.repository.GLib.filename_from_uri", return_value=("/tmp/nonexistent.png", "")),
            patch("pathlib.Path.exists", return_value=False),
            patch.object(service, "_emit_clipboard_error") as mock_error,
        ):
            # Call with file URI data for non-existent file
            service._on_uri_list_bytes(b"file:///tmp/nonexistent.png\r\n")
            # Verify error was emitted
            mock_error.assert_called_once()

    def test_emit_texture_from_file_success(self, service):
        """Test _emit_texture_from_file success path."""
        mock_texture = MagicMock()

        with (
            patch("anura.services.clipboard_service.validate_image_resource", return_value=(True, 1024, None)),
            patch("PIL.Image.open") as mock_image_open,
            patch("gi.repository.Gdk.Texture.new_from_bytes", return_value=mock_texture),
            patch("gi.repository.GLib.Bytes.new"),
            patch("gi.repository.GLib.idle_add") as mock_idle_add,
        ):
            # Mock PIL image operations
            mock_img = MagicMock()
            mock_img.mode = "RGB"
            mock_image_open.return_value.__enter__.return_value = mock_img

            # Trigger the method
            service._emit_texture_from_file("/tmp/test.png")

            # Verify success signal was emitted
            assert mock_idle_add.called

    def test_emit_texture_from_file_pil_failure(self, service):
        """Test _emit_texture_from_file PIL decode failure."""
        from PIL import Image

        with (
            patch("anura.services.clipboard_service.validate_image_resource", return_value=(True, 1024, None)),
            patch("PIL.Image.open", side_effect=Image.UnidentifiedImageError("Cannot identify image file")),
            patch("gi.repository.GLib.idle_add") as mock_idle_add,
        ):
            # Trigger the method
            service._emit_texture_from_file("/tmp/test.png")

            # Verify error signal was emitted
            assert mock_idle_add.called

    def test_emit_texture_from_file_gdk_failure(self, service):
        """Test _emit_texture_from_file Gdk.Texture failure."""
        from gi.repository import Gio, GLib

        with (
            patch("anura.services.clipboard_service.validate_image_resource", return_value=(True, 1024, None)),
            patch("PIL.Image.open") as mock_image_open,
            patch("gi.repository.Gdk.Texture.new_from_bytes", side_effect=GLib.Error.new_literal(Gio.io_error_quark(), "Texture creation failed", Gio.IOErrorEnum.FAILED)),
            patch("gi.repository.GLib.Bytes.new"),
            patch("gi.repository.GLib.idle_add") as mock_idle_add,
        ):
            # Mock PIL image operations
            mock_img = MagicMock()
            mock_img.mode = "RGB"
            mock_image_open.return_value.__enter__.return_value = mock_img

            # Trigger the method
            service._emit_texture_from_file("/tmp/test.png")

            # Verify error signal was emitted
            assert mock_idle_add.called
