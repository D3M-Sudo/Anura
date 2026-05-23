# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

from gi.repository import GObject, GLib, Gtk, Gio
from loguru import logger
from anura.services.result_dispatcher import get_result_dispatcher
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
        # UI Requests from Dispatcher
        self.connect_tracked(self._dispatcher, "toast-requested",
                           lambda _, msg: self._window.show_toast(msg))
        self.connect_tracked(self._dispatcher, "uri-launch-requested",
                           lambda _, uri: self._window._launch_uri(uri))

        # Backend Responses
        backend = self._window.backend
        self.connect_tracked(backend, "decoded", self._on_shot_done)
        self.connect_tracked(backend, "error", self._on_shot_error)
        self.connect_tracked(backend, "portal-backend-missing", self._on_portal_backend_missing)

        # Banner Interactions
        self.connect_tracked(self._window.portal_banner, "button-clicked",
                           self._on_portal_banner_dismissed)

    def _on_shot_done(self, _sender, text, copy):
        """Handle successful screenshot capture and OCR processing."""
        if hasattr(self._window, "_screenshot_timeout_id") and self._window._screenshot_timeout_id is not None:
            GLib.source_remove(self._window._screenshot_timeout_id)
            self._window._screenshot_timeout_id = None

        self._window.present()
        self._window.welcome_page.reset_drop_area_state()

        if not text:
            return

        try:
            self._window.extracted_page.extracted_text = text
            self._dispatcher.dispatch(text, copy)
            GLib.idle_add(self._navigate_to_extracted_page)
        except Exception as e:
            logger.error(f"OcrController: UI Error in _on_shot_done: {e}")

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
        from anura.config import MAX_IMAGE_SIZE_BYTES
        from anura.utils import validate_image_resource
        from io import BytesIO

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
