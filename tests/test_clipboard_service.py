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

    def test_copy_text_publishes_a_plain_string(self, service):
        """set()/copy_text() must hand GTK a plain string, never a GLib.Variant.

        Regression (F-13): the text used to be wrapped in GLib.Variant("s", ...), which
        GTK publishes only as the "GVariant" format, so no other application could
        paste it. The ContentProvider has to carry a G_TYPE_STRING value so that GTK
        advertises text/plain. The previous version of this test replaced both the
        provider factory and GLib.Variant with mocks and only asserted that
        set_content was called, so it passed with the broken implementation.
        """
        from unittest.mock import PropertyMock

        from gi.repository import GLib, GObject

        mock_clipboard = MagicMock()
        mock_content_provider = MagicMock()

        with (
            patch.object(ClipboardService, "clipboard", new_callable=PropertyMock) as mock_cb_prop,
            patch("gi.repository.Gdk.ContentProvider.new_for_value", return_value=mock_content_provider) as factory,
        ):
            mock_cb_prop.return_value = mock_clipboard
            service.copy_text("Enterprise Audit")

        factory.assert_called_once()
        value = factory.call_args.args[0]
        assert not isinstance(value, GLib.Variant)
        # A plain str and a G_TYPE_STRING GObject.Value are equivalent for GTK.
        if isinstance(value, GObject.Value):
            assert value.g_type == GObject.TYPE_STRING
            value = value.get_string()
        assert value == "Enterprise Audit"
        mock_clipboard.set_content.assert_called_once_with(mock_content_provider)

    def test_set_ignores_empty_text(self, service):
        from unittest.mock import PropertyMock

        mock_clipboard = MagicMock()
        with patch.object(ClipboardService, "clipboard", new_callable=PropertyMock) as mock_cb_prop:
            mock_cb_prop.return_value = mock_clipboard
            service.set("")

        mock_clipboard.set_content.assert_not_called()

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


class TestClipboardRealRoundtrip:
    """Tests against the real display clipboard (no mocks).

    The mocked tests above cannot tell whether the text is actually pasteable. These
    ones publish text through ClipboardService and read it back from the same
    clipboard, and check which formats other applications are offered.
    """

    SAMPLE = "Testo OCR: àèì — “ok” 日本語 😀\nsecond line & <b>tag</b>"

    @pytest.fixture
    def real_service(self):
        import gi

        gi.require_version("Gdk", "4.0")
        gi.require_version("Gtk", "4.0")
        from gi.repository import Gdk, Gtk

        if not Gtk.init_check() or Gdk.Display.get_default() is None:
            pytest.skip("no GDK display available")
        service = ClipboardService()
        service.init()
        return service

    @staticmethod
    def _read_text(clipboard, timeout_seconds: float = 5.0):
        """Read the clipboard text asynchronously, pumping the default main context."""
        import time

        from gi.repository import GLib

        result: dict[str, str] = {}

        def done(source, async_result):
            try:
                result["text"] = source.read_text_finish(async_result)
            except GLib.Error as e:
                result["error"] = e.message

        clipboard.read_text_async(None, done)
        context = GLib.MainContext.default()
        deadline = time.monotonic() + timeout_seconds
        while "text" not in result and "error" not in result and time.monotonic() < deadline:
            context.iteration(False)
            time.sleep(0.005)
        return result

    def test_set_text_is_readable_from_the_clipboard(self, real_service):
        real_service.set(self.SAMPLE)

        result = self._read_text(real_service.clipboard)

        assert result == {"text": self.SAMPLE}

    def test_set_text_advertises_plain_text_formats_to_other_apps(self, real_service):
        from gi.repository import GObject

        real_service.set(self.SAMPLE)

        formats = real_service.clipboard.get_formats()
        assert formats.contain_gtype(GObject.TYPE_STRING)
        assert formats.contain_mime_type("text/plain;charset=utf-8")
        assert formats.contain_mime_type("text/plain")


class TestClipboardLifetime:
    """hand_off_to_manager() and wait_until_replaced(): short-lived processes (silent mode)."""

    @staticmethod
    def _service_with(clipboard):
        from unittest.mock import PropertyMock

        service = ClipboardService()
        patcher = patch.object(ClipboardService, "clipboard", new_callable=PropertyMock, return_value=clipboard)
        patcher.start()
        return service, patcher

    def test_hand_off_reports_success_when_the_manager_takes_the_content(self):
        clipboard = MagicMock()
        clipboard.store_async.side_effect = lambda _prio, _cancellable, callback: callback(clipboard, "result")
        clipboard.store_finish.return_value = True
        service, patcher = self._service_with(clipboard)
        try:
            assert service.hand_off_to_manager(timeout_seconds=1.0) is True
        finally:
            patcher.stop()

    def test_hand_off_reports_failure_when_there_is_no_manager(self):
        from gi.repository import Gio, GLib

        clipboard = MagicMock()
        clipboard.store_async.side_effect = lambda _prio, _cancellable, callback: callback(clipboard, "result")
        clipboard.store_finish.side_effect = GLib.Error.new_literal(
            Gio.io_error_quark(), "Cannot store clipboard. No clipboard manager is active.", Gio.IOErrorEnum.NOT_SUPPORTED
        )
        service, patcher = self._service_with(clipboard)
        try:
            assert service.hand_off_to_manager(timeout_seconds=1.0) is False
        finally:
            patcher.stop()

    def test_hand_off_gives_up_and_cancels_when_the_manager_never_answers(self):
        clipboard = MagicMock()  # store_async never calls its callback
        service, patcher = self._service_with(clipboard)
        try:
            assert service.hand_off_to_manager(timeout_seconds=0.1) is False
        finally:
            patcher.stop()
        cancellable = clipboard.store_async.call_args.args[1]
        assert cancellable.is_cancelled()

    def test_wait_until_replaced_returns_true_once_another_app_owns_the_clipboard(self):
        clipboard = MagicMock()
        clipboard.is_local.side_effect = [True, True, False]
        service, patcher = self._service_with(clipboard)
        try:
            assert service.wait_until_replaced(timeout_seconds=5.0) is True
        finally:
            patcher.stop()

    def test_wait_until_replaced_times_out_while_we_still_own_the_clipboard(self):
        clipboard = MagicMock()
        clipboard.is_local.return_value = True
        service, patcher = self._service_with(clipboard)
        try:
            assert service.wait_until_replaced(timeout_seconds=0.1) is False
        finally:
            patcher.stop()

    def test_wait_until_replaced_stops_when_asked(self):
        clipboard = MagicMock()
        clipboard.is_local.return_value = True
        service, patcher = self._service_with(clipboard)
        try:
            assert service.wait_until_replaced(timeout_seconds=30.0, should_stop=lambda: True) is False
        finally:
            patcher.stop()

    def test_hand_off_refuses_to_reenter_a_running_default_context(self):
        clipboard = MagicMock()
        context = MagicMock()
        context.is_owner.return_value = True
        service, patcher = self._service_with(clipboard)
        try:
            with patch("gi.repository.GLib.MainContext.default", return_value=context):
                assert service.hand_off_to_manager(timeout_seconds=0.1) is False
        finally:
            patcher.stop()
        clipboard.store_async.assert_not_called()
        context.iteration.assert_not_called()

    def test_hand_off_refuses_when_another_thread_owns_the_default_context(self):
        clipboard = MagicMock()
        context = MagicMock()
        context.is_owner.return_value = False
        context.depth = 1
        service, patcher = self._service_with(clipboard)
        try:
            with patch("gi.repository.GLib.MainContext.default", return_value=context):
                assert service.hand_off_to_manager(timeout_seconds=0.1) is False
        finally:
            patcher.stop()
        clipboard.store_async.assert_not_called()

    def test_wait_until_replaced_refuses_to_reenter_a_running_default_context(self):
        clipboard = MagicMock()
        clipboard.is_local.return_value = True
        context = MagicMock()
        context.is_owner.return_value = True
        service, patcher = self._service_with(clipboard)
        try:
            with patch("gi.repository.GLib.MainContext.default", return_value=context):
                assert service.wait_until_replaced(timeout_seconds=0.1) is False
        finally:
            patcher.stop()
        context.iteration.assert_not_called()


    def test_real_clipboard_hand_off_answers_instead_of_hanging(self):
        """Against the real display: with no clipboard manager this must fail fast, not block."""
        import time

        import gi

        gi.require_version("Gdk", "4.0")
        gi.require_version("Gtk", "4.0")
        from gi.repository import Gdk, Gtk

        if not Gtk.init_check() or Gdk.Display.get_default() is None:
            pytest.skip("no GDK display available")
        service = ClipboardService()
        service.init()
        service.set("hand-off check")

        started = time.monotonic()
        result = service.hand_off_to_manager(timeout_seconds=3.0)

        assert isinstance(result, bool)
        assert time.monotonic() - started < 4.0
