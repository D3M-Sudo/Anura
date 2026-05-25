# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

from gettext import gettext as _
from gettext import ngettext
from typing import ClassVar

from gi.repository import Gio, GLib, GObject, Gtk
from loguru import logger

from anura.services.result_dispatcher import get_result_dispatcher
from anura.utils import uri_validator
from anura.utils.portal_advice import detect_portal_advice


class OcrController(GObject.GObject):
    """
    Decoupled controller for OCR operations.
    Manages coordination between the Window UI and the ScreenshotService.
    Emits GLib signals for detected text and errors to allow event-driven service integration.
    """

    __gsignals__: ClassVar[dict[str, tuple]] = {
        "text-extracted": (GObject.SignalFlags.RUN_LAST, None, (str, bool)),
        "uri-detected": (GObject.SignalFlags.RUN_LAST, None, (str, bool)),
        "error-occurred": (GObject.SignalFlags.RUN_LAST, None, (str,)),
    }

    def __init__(self, window):
        GObject.GObject.__init__(self)
        import weakref

        self._window = weakref.proxy(window)
        self._dispatcher = get_result_dispatcher()
        self._signal_connections = {}

        # Register for automatic teardown
        if hasattr(window, "register_controller"):
            window.register_controller(self)

        # Connect to window signals and backend
        self._setup_connections()
        logger.debug("OcrController: Initialized and connected to AnuraWindow")

    def connect_tracked(self, emitter, signal_name, callback):
        handler_id = emitter.connect(signal_name, callback)
        if emitter not in self._signal_connections:
            self._signal_connections[emitter] = []
        self._signal_connections[emitter].append(handler_id)
        return handler_id

    def teardown(self) -> None:
        """Unified teardown called by SignalManagerMixin."""
        self.cleanup()

    def _setup_connections(self):
        # Backend Responses
        backend = self._window.backend
        self.connect_tracked(backend, "decoded", self._on_shot_done)
        self.connect_tracked(backend, "error", self._on_shot_error)
        self.connect_tracked(backend, "status-changed", self._on_status_changed)
        self.connect_tracked(backend, "portal-backend-missing", self._on_portal_backend_missing)

        # Banner Interactions
        self.connect_tracked(self._window.portal_banner, "button-clicked", self._on_portal_banner_dismissed)

    def _on_shot_done(self, _sender, text, copy, ocr_result):
        """Handle successful screenshot capture and OCR processing."""
        if hasattr(self._window, "_screenshot_timeout_id") and self._window._screenshot_timeout_id is not None:
            GLib.source_remove(self._window._screenshot_timeout_id)
            self._window._screenshot_timeout_id = None

        self._window.present()
        self._window.welcome_page.reset_drop_area_state()

        if not text:
            self.emit("error-occurred", _("No text found. Try to grab another region."))
            return

        try:
            self._window.extracted_page.extracted_text = text
            extraction_result = self._dispatcher.dispatch(text, ocr_result)
            self._handle_extraction_result(extraction_result, copy)
            GLib.idle_add(self._navigate_to_extracted_page)
        except Exception as e:
            logger.error(f"OcrController: UI Error in _on_shot_done: {e}")

    def _handle_extraction_result(self, result, copy_requested: bool):
        """Handle the extraction result, emitting signals for side effects."""
        if result.is_primary_url:
            url = result.urls[0].strip().strip("\n\r\t\v\f")
            if uri_validator(url):
                self.emit("uri-detected", url, copy_requested)
            else:
                self.emit("text-extracted", url, copy_requested)
        else:
            self.emit("text-extracted", result.text, copy_requested)

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

    def _on_status_changed(self, _sender, status_msg):
        """Handle status updates from backend to prevent Zombie UI."""
        if hasattr(self._window, "show_status"):
            self._window.show_status(status_msg)
        elif hasattr(self._window, "welcome_page"):
            self._window.welcome_page.set_status(status_msg)

    def _on_shot_error(self, _sender, message):
        """Handle screenshot capture errors."""
        if hasattr(self._window, "_screenshot_timeout_id") and self._window._screenshot_timeout_id is not None:
            GLib.source_remove(self._window._screenshot_timeout_id)
            self._window._screenshot_timeout_id = None

        self._window.present()
        self._window.welcome_page.reset_drop_area_state()
        if message:
            self.emit("error-occurred", message)

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

        dialog = Gtk.FileDialog()
        dialog.set_title(_("Choose an image for extraction"))

        all_img_filter = Gtk.FileFilter()
        all_img_filter.set_name(_("All supported images"))

        all_extensions = [
            "png",
            "jpg",
            "jpeg",
            "jpe",
            "jfif",
            "webp",
            "avif",
            "avifs",
            "tif",
            "tiff",
            "bmp",
            "dib",
            "gif",
        ]

        for ext in all_extensions:
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
                    self._window.process_file(file.get_path())
            except Exception:
                pass

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
