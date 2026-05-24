# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

from gettext import gettext as _
from gettext import ngettext

from gi.repository import Gio, GLib, GObject, Gtk
from loguru import logger

from anura.services.clipboard_service import get_clipboard_service
from anura.services.result_dispatcher import get_result_dispatcher
from anura.services.settings import settings
from anura.utils import uri_validator
from anura.utils.portal_advice import detect_portal_advice


class OcrController(GObject.GObject):
    """
    Decoupled controller for OCR operations.
    Manages coordination between the Window UI and the ScreenshotService.
    """

    def __init__(self, window):
        GObject.GObject.__init__(self)
        self._window = window
        self._dispatcher = get_result_dispatcher()
        self._signal_connections = {}

        # Connect to window signals and backend
        self._setup_connections()
        logger.debug("OcrController: Initialized and connected to AnuraWindow")

    def connect_tracked(self, emitter, signal_name, callback):
        handler_id = emitter.connect(signal_name, callback)
        if emitter not in self._signal_connections:
            self._signal_connections[emitter] = []
        self._signal_connections[emitter].append(handler_id)
        return handler_id

    def _setup_connections(self):
        # Backend Responses
        backend = self._window.backend
        self.connect_tracked(backend, "decoded", self._on_shot_done)
        self.connect_tracked(backend, "error", self._on_shot_error)
        self.connect_tracked(backend, "portal-backend-missing", self._on_portal_backend_missing)

        # Banner Interactions
        self.connect_tracked(self._window.portal_banner, "button-clicked",
                           self._on_portal_banner_dismissed)

    def _on_notification_requested(self, _dispatcher, title, body):
        """Bridge notification requests from dispatcher to system notifications."""
        app = Gtk.Application.get_default()
        if app and hasattr(app, "notification_service"):
            app.notification_service.show_notification(title=title, body=body)

    def _on_shot_done(self, _sender, text, copy, ocr_result):
        """Handle successful screenshot capture and OCR processing."""
        if hasattr(self._window, "_screenshot_timeout_id") and self._window._screenshot_timeout_id is not None:
            GLib.source_remove(self._window._screenshot_timeout_id)
            self._window._screenshot_timeout_id = None

        self._window.present()
        self._window.welcome_page.reset_drop_area_state()

        if not text:
            self._on_notification_requested(
                None, _("Anura OCR"), _("No text found. Try to grab another region.")
            )
            return

        try:
            self._window.extracted_page.extracted_text = text
            extraction_result = self._dispatcher.dispatch(text, ocr_result)
            self._handle_extraction_result(extraction_result, copy)
            GLib.idle_add(self._navigate_to_extracted_page)
        except Exception as e:
            logger.error(f"OcrController: UI Error in _on_shot_done: {e}")

    def _handle_extraction_result(self, result, copy_requested: bool):
        """Handle the extraction result, applying settings and triggering side effects."""
        if result.is_primary_url:
            self._handle_url_flow(result.urls[0], copy_requested)
        else:
            self._handle_text_flow(result, copy_requested)

    def _handle_url_flow(self, url: str, copy_requested: bool):
        """Handle dispatching for URL-primary results."""
        url = url.strip().strip("\n\r\t\v\f")

        if not uri_validator(url):
            # Fallback to text flow if URL is invalid
            from anura.types.ocr import ExtractionResult
            fake_result = ExtractionResult(
                text=url, raw_text=url, urls=(), emails=(), phone_numbers=(),
                avg_confidence=0.0, is_primary_url=False
            )
            self._handle_text_flow(fake_result, copy_requested)
            return

        if settings.get_boolean("autolinks"):
            # Behavior A: Open directly in browser
            self._window._launch_uri(url)
            self._window.show_toast(_("URL opened automatically"))
        else:
            # Behavior B: Send desktop notification with clickable action
            target = GLib.Variant("s", url)
            app = Gtk.Application.get_default()
            if app and hasattr(app, "notification_service"):
                app.notification_service.send_notification_with_action(
                    notification_id="qr-url",
                    title=_("QR Code URL Detected"),
                    body=url,
                    action_id="app.open-qr-url",
                    action_target=target,
                    priority="high",
                )
            else:
                self._on_notification_requested(None, _("QR Code URL Detected"), url)

        # Handle URL Clipboard (respecting global autocopy or explicit request)
        if settings.get_boolean("autocopy") or copy_requested:
            get_clipboard_service().set(url)
            # Only show "copied" toast if we didn't open the browser automatically
            if not settings.get_boolean("autolinks"):
                self._window.show_toast(_("URL copied to clipboard"))

    def _handle_text_flow(self, result, copy_requested: bool):
        """Handle dispatching for regular text results."""
        is_window_active = bool(Gtk.Application.get_default().get_active_window())
        text = result.text

        if settings.get_boolean("autocopy") or copy_requested:
            get_clipboard_service().set(text)
            self._window.show_toast(_("Text copied to clipboard"))
            if not is_window_active:
                self._on_notification_requested(
                    None, _("Anura OCR"), _("Text extracted and copied to clipboard.")
                )
        else:
            if not is_window_active:
                self._on_notification_requested(
                    None, _("Anura OCR"), _("Text extracted successfully.")
                )

        # Show toasts for other structured data found in text
        if result.emails:
            count = len(result.emails)
            self._window.show_toast(
                ngettext("{n} email found in text", "{n} emails found in text", count).format(n=count)
            )

        if result.phone_numbers:
            count = len(result.phone_numbers)
            self._window.show_toast(
                ngettext("{n} phone number found in text", "{n} phone numbers found in text", count).format(n=count)
            )

    def _on_shot_error(self, _sender, message):
        """Handle screenshot capture errors."""
        if hasattr(self._window, "_screenshot_timeout_id") and self._window._screenshot_timeout_id is not None:
            GLib.source_remove(self._window._screenshot_timeout_id)
            self._window._screenshot_timeout_id = None

        self._window.present()
        self._window.welcome_page.reset_drop_area_state()
        if message:
            self._window.show_toast(message)

    def _on_portal_backend_missing(self, _sender):
        """Reveal the persistent install hint banner."""
        try:
            advice = detect_portal_advice()
            self._window.portal_banner.set_title(advice.short_message)
            self._window.portal_banner.set_revealed(True)
        except Exception:
            logger.exception("OcrController: Unexpected error handling portal backend missing")

    def _on_portal_banner_dismissed(self, _banner):
        self._window.portal_banner.set_revealed(False)

    def _navigate_to_extracted_page(self):
        self._window.split_view.set_show_content(True)
        self._window.extracted_page.text_view.grab_focus()
        return GLib.SOURCE_REMOVE

    def open_image(self) -> None:
        """Open file dialog to select an image for OCR processing."""
        from gettext import gettext as _
        from io import BytesIO

        from anura.config import MAX_IMAGE_SIZE_BYTES
        from anura.utils import validate_image_resource

        dialog = Gtk.FileDialog()
        dialog.set_title(_("Choose an image for extraction"))

        all_img_filter = Gtk.FileFilter()
        all_img_filter.set_name(_("All supported images"))

        _ALL_EXTENSIONS = [
            "png", "jpg", "jpeg", "jpe", "jfif", "webp", "avif", "avifs",
            "tif", "tiff", "bmp", "dib", "gif",
        ]

        for ext in _ALL_EXTENSIONS:
            all_img_filter.add_pattern(f"*.{ext}")
            all_img_filter.add_pattern(f"*.{ext.upper()}")

        def _make_format_filter(display_name: str, extensions: list[str]) -> Gtk.FileFilter:
            filt = Gtk.FileFilter()
            filt.set_name(display_name)
            for ext in extensions:
                filt.add_pattern(f"*.{ext}")
                filt.add_pattern(f"*.{ext.upper()}")
            return filt

        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(all_img_filter)
        filters.append(_make_format_filter(_("PNG images (*.png)"), ["png"]))
        filters.append(_make_format_filter(_("JPEG images (*.jpg)"), ["jpg", "jpeg", "jpe", "jfif"]))
        filters.append(_make_format_filter(_("WebP images (*.webp)"), ["webp"]))
        filters.append(_make_format_filter(_("AVIF images (*.avif)"), ["avif", "avifs"]))
        filters.append(_make_format_filter(_("TIFF images (*.tif)"), ["tif", "tiff"]))
        filters.append(_make_format_filter(_("BMP images (*.bmp)"), ["bmp", "dib"]))
        filters.append(_make_format_filter(_("GIF images (*.gif)"), ["gif"]))

        all_files_filter = Gtk.FileFilter()
        all_files_filter.set_name(_("All files (*)"))
        all_files_filter.add_pattern("*")
        filters.append(all_files_filter)

        dialog.set_filters(filters)
        dialog.set_default_filter(all_img_filter)

        def _on_open_image_result(dialog, result):
            try:
                file = dialog.open_finish(result)
                if file:
                    self._window.welcome_page.show_spinner()
                    file.query_info_async(
                        Gio.FILE_ATTRIBUTE_STANDARD_SIZE,
                        Gio.FileQueryInfoFlags.NONE,
                        GLib.PRIORITY_DEFAULT,
                        None,
                        _on_open_image_info_ready,
                    )
            except Exception:
                self._window.welcome_page.hide_spinner()

        def _on_open_image_info_ready(gfile, result):
            try:
                info = gfile.query_info_finish(result)
                if info:
                    file_size = info.get_size()
                    if file_size > MAX_IMAGE_SIZE_BYTES:
                        self._window.welcome_page.spinner.set_visible(False)
                        self._window.show_toast(_("Image too large"))
                        return
                    gfile.load_contents_async(None, _on_file_contents_loaded)
                else:
                    self._window.welcome_page.hide_spinner()
            except Exception:
                self._window.welcome_page.hide_spinner()

        def _on_file_contents_loaded(gfile, result):
            try:
                ok, contents, _etag = gfile.load_contents_finish(result)
                if ok:
                    is_valid, _size, error = validate_image_resource(contents)
                    if not is_valid:
                        self._window.welcome_page.spinner.set_visible(False)
                        self._window.show_toast(_(error) if error else _("Invalid image file"))
                        return

                    from anura.atomic_task_manager import get_atomic_manager
                    get_atomic_manager().execute(
                        self._window.backend.decode_image,
                        (self._window.get_language(), BytesIO(contents))
                    )
            except Exception:
                self._window.welcome_page.hide_spinner()

        dialog.open(self._window, None, _on_open_image_result)

    def cleanup(self):
        """Explicit cleanup to prevent memory leaks."""
        for emitter, handler_ids in self._signal_connections.items():
            for handler_id in handler_ids:
                try:
                    emitter.disconnect(handler_id)
                except Exception:
                    pass
        self._signal_connections.clear()
        self._window = None
        logger.debug("OcrController: Cleaned up and disconnected")
