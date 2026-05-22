# ocr_mixin.py
#
# Copyright 2026 D3M-Sudo (Anura fork and modifications)

from gettext import gettext as _
from gettext import ngettext
from io import BytesIO

from gi.repository import Adw, Gio, GLib, GObject, Gtk
from loguru import logger

from anura.config import MAX_IMAGE_SIZE_BYTES, MAX_IMAGE_SIZE_MB
from anura.gobject_worker import GObjectWorker
from anura.services.clipboard_service import get_clipboard_service
from anura.utils import uri_validator
from anura.utils.portal_advice import detect_portal_advice
from anura.utils.text_preprocessor import get_text_preprocessor


class WindowOCRMixin:
    """Mixin class for AnuraWindow to handle OCR backend signal wiring and processing."""

    def _connect_ocr_signals(self) -> None:
        """Connect OCR backend signals."""
        self._handler_decoded = self.backend.connect("decoded", self.on_shot_done)
        self._handler_error = self.backend.connect("error", self.on_shot_error)
        self._handler_portal_missing = self.backend.connect(
            "portal-backend-missing",
            self._on_portal_backend_missing,
        )
        # Banner's "button-clicked" fires when the user dismisses; hide until
        # the next backend failure re-reveals it.
        self._handler_portal_banner = self.portal_banner.connect("button-clicked", self._on_portal_banner_dismissed)

    def on_shot_done(self, _sender: GObject.GObject, text: str, copy: bool) -> None:
        """Handle successful screenshot capture and OCR processing."""
        # Cancel safety timeout if screenshot succeeded
        if self._screenshot_timeout_id is not None:
            GLib.source_remove(self._screenshot_timeout_id)
            self._screenshot_timeout_id = None

        self.present()
        # Clean up DnD processing state and spinner
        self.welcome_page.reset_drop_area_state()

        if not text:
            return

        try:
            self.extracted_page.extracted_text = text  # type: ignore[method-assign]

            # 1. Extract structured data (emails, URLs, phone numbers) from OCR text
            preprocessor = get_text_preprocessor()
            structured = preprocessor.extract_structured_data(text)

            # 2. Identify if the result is primarily a URL (e.g. from a QR code)
            primary_url = None
            if structured["urls"]:
                # If the entire text is just a URL (allowing for whitespace/newlines)
                candidate = structured["urls"][0]
                if candidate.strip() == text.strip():
                    primary_url = candidate

            # 3. Handle URL Flow (Mode A/B)
            if primary_url:
                # Security: strip all control characters and whitespace
                primary_url = primary_url.strip().strip("\n\r\t\v\f")

                if uri_validator(primary_url):
                    if self.settings.get_boolean("autolinks"):
                        # Behavior A: Open directly in browser (toggle ON)
                        self._launch_uri(primary_url)
                        self.show_toast(_("URL opened automatically"))
                    else:
                        # Behavior B: Send desktop notification with clickable action
                        # Do NOT copy URL to clipboard, do NOT open browser automatically
                        target = GLib.Variant("s", primary_url)
                        app = Gtk.Application.get_default()
                        if app and hasattr(app, "notification_service"):
                            app.notification_service.send_notification_with_action(
                                notification_id="qr-url",
                                title=_("QR Code URL Detected"),
                                body=primary_url,
                                action_id="app.open-qr-url",
                                action_target=target,
                                priority="high",
                            )

                # 4. Handle URL Clipboard (respecting global autocopy)
                if self.settings.get_boolean("autocopy") or copy:
                    clipboard_service_instance = get_clipboard_service()
                    clipboard_service_instance.set(primary_url)
                    # Only show "copied" toast if we didn't open the browser automatically
                    # to avoid toast spam when both are ON.
                    if not self.settings.get_boolean("autolinks"):
                        self.show_toast(_("URL copied to clipboard"))

                logger.debug("Anura: URL-primary result processed")

            else:
                # 4. Handle Regular Text Flow (Clipboard)
                if self.settings.get_boolean("autocopy") or copy:
                    clipboard_service_instance = get_clipboard_service()
                    clipboard_service_instance.set(text)
                    self.show_toast(_("Text copied to clipboard"))

                # Still show toasts for other structured data if found in mixed text
                if structured["emails"]:
                    email_count = len(structured["emails"])
                    self.show_toast(
                        ngettext("{n} email found in text", "{n} emails found in text", email_count).format(
                            n=email_count,
                        ),
                    )

                if structured["phone_numbers"]:
                    phone_count = len(structured["phone_numbers"])
                    self.show_toast(
                        ngettext(
                            "{n} phone number found in text",
                            "{n} phone numbers found in text",
                            phone_count,
                        ).format(n=phone_count),
                    )

            # Defer navigation to ExtractedPage until window is properly mapped
            GLib.idle_add(self._navigate_to_extracted_page)

        except Exception as e:
            logger.error(f"Anura UI Error in on_shot_done: {e}")

    def on_shot_error(self, _sender: GObject.GObject, message: str) -> None:
        """Handle screenshot capture errors."""
        # Cancel safety timeout if screenshot failed
        if self._screenshot_timeout_id is not None:
            GLib.source_remove(self._screenshot_timeout_id)
            self._screenshot_timeout_id = None

        self.present()
        self.welcome_page.reset_drop_area_state()
        if message:
            self.show_toast(message)

    def _on_portal_backend_missing(self, _sender: GObject.GObject) -> None:
        """Reveal the persistent install hint banner with desktop-aware message."""
        try:
            advice = detect_portal_advice()
            self.portal_banner.set_title(advice.short_message)
            self.portal_banner.set_revealed(True)
        except Exception:
            logger.exception("Anura: Unexpected error handling portal backend missing")

    def _on_portal_banner_dismissed(self, _banner: Adw.Banner) -> None:
        """Hide the banner when the user clicks Dismiss."""
        self.portal_banner.set_revealed(False)

    def _on_screenshot_timeout(self) -> bool:
        """Handle screenshot portal timeout."""
        try:
            self._screenshot_timeout_id = None
            self.present()
            self.show_toast(_("Screenshot service did not respond."))
            logger.warning("Anura Screenshot: Portal timeout - window restored.")
        except Exception:
            logger.exception("Anura: Unexpected error in screenshot timeout handler")
        return False  # Don't repeat timeout

    def open_image(self) -> None:
        """Open file dialog to select an image for OCR processing."""
        dialog = Gtk.FileDialog()
        dialog.set_title(_("Choose an image for extraction"))

        # Filtro cumulativo "Tutte le immagini supportate".
        # Usa add_pattern() per ogni variante case (minuscolo + maiuscolo)
        # di ogni estensione, garantendo compatibilità cross-desktop
        # (GTK, LXQt/KDE) e case-insensitivity su filesystem Linux.
        all_img_filter = Gtk.FileFilter()
        all_img_filter.set_name(_("All supported images"))

        _ALL_EXTENSIONS = [
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

        for ext in _ALL_EXTENSIONS:
            all_img_filter.add_pattern(f"*.{ext}")
            all_img_filter.add_pattern(f"*.{ext.upper()}")

        # Helper per creare un filtro individuale per formato
        def _make_format_filter(display_name: str, extensions: list[str]) -> Gtk.FileFilter:
            """Crea un Gtk.FileFilter con nome pulito e pattern case-insensitive.

            Args:
                display_name: Nome localizzato da mostrare nel dropdown
                             (es. "PNG images (*.png)").
                extensions: Lista di estensioni (minuscole) da abbinare.

            Returns:
                Gtk.FileFilter configurato.
            """
            filt = Gtk.FileFilter()
            filt.set_name(display_name)
            for ext in extensions:
                filt.add_pattern(f"*.{ext}")
                filt.add_pattern(f"*.{ext.upper()}")
            return filt

        png_filter = _make_format_filter(_("PNG images (*.png)"), ["png"])

        jpg_filter = _make_format_filter(
            _("JPEG images (*.jpg)"),
            ["jpg", "jpeg", "jpe", "jfif"],
        )

        webp_filter = _make_format_filter(_("WebP images (*.webp)"), ["webp"])

        avif_filter = _make_format_filter(
            _("AVIF images (*.avif)"),
            ["avif", "avifs"],
        )

        tiff_filter = _make_format_filter(
            _("TIFF images (*.tif)"),
            ["tif", "tiff"],
        )

        bmp_filter = _make_format_filter(
            _("BMP images (*.bmp)"),
            ["bmp", "dib"],
        )

        gif_filter = _make_format_filter(_("GIF images (*.gif)"), ["gif"])

        # Catch-all — mostra tutti i file.
        all_files_filter = Gtk.FileFilter()
        all_files_filter.set_name(_("All files (*)"))
        all_files_filter.add_pattern("*")

        # Ordine: cumulativo (default) → individuali per formato → catch-all.
        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(all_img_filter)
        filters.append(png_filter)
        filters.append(jpg_filter)
        filters.append(webp_filter)
        filters.append(avif_filter)
        filters.append(tiff_filter)
        filters.append(bmp_filter)
        filters.append(gif_filter)
        filters.append(all_files_filter)

        dialog.set_filters(filters)
        dialog.set_default_filter(all_img_filter)
        dialog.open(self, None, self._on_open_image_result)

    def _on_open_image_result(self, dialog: Gtk.FileDialog, result: Gio.AsyncResult) -> None:
        """Handle image selection result."""
        try:
            file = dialog.open_finish(result)
            if file:
                self.welcome_page.show_spinner()
                # Security Hardening: Query file info for size validation before loading contents
                # This prevents memory exhaustion (DoS) from extremely large files.
                file.query_info_async(
                    Gio.FILE_ATTRIBUTE_STANDARD_SIZE,
                    Gio.FileQueryInfoFlags.NONE,
                    GLib.PRIORITY_DEFAULT,
                    None,
                    self._on_open_image_info_ready,
                )
        except (GLib.Error, RuntimeError, OSError) as e:
            logger.debug(f"File selection cancelled or failed: {e}")
            # Ensure spinner is hidden on error to prevent UI inconsistency
            self.welcome_page.hide_spinner()

    def _on_open_image_info_ready(self, gfile: Gio.File, result: Gio.AsyncResult) -> None:
        """Handle file info result and validate size before loading content."""
        try:
            info = gfile.query_info_finish(result)
            if info:
                file_size = info.get_size()
                if file_size > MAX_IMAGE_SIZE_BYTES:
                    logger.error(f"Anura OCR: Image too large ({file_size} bytes)")
                    self.welcome_page.spinner.set_visible(False)
                    self.show_toast(
                        _("Image too large: {size}MB (max {max}MB)").format(
                            size=round(file_size / (1024 * 1024), 1),
                            max=MAX_IMAGE_SIZE_MB,
                        ),
                    )
                    return

                # Size is valid, proceed to load contents
                gfile.load_contents_async(None, self._on_file_contents_loaded)
            else:
                self.welcome_page.spinner.set_visible(False)
                self.show_toast(_("Failed to load image file info"))
        except (GLib.Error, OSError, RuntimeError) as e:
            self.welcome_page.spinner.set_visible(False)
            logger.error(f"Failed to query file info: {e}")
            self.show_toast(_("Failed to load image file"))

    def _on_file_contents_loaded(self, gfile: Gio.File, result: Gio.AsyncResult) -> None:
        """Handle file contents loading result."""
        try:
            # NOTE: do not unpack the etag into `_` — that rebinds the
            # module-level gettext alias for the rest of this function.
            ok, contents, _etag = gfile.load_contents_finish(result)
            if ok:
                # Size validation is now performed in _on_open_image_info_ready
                # before loading contents to prevent memory exhaustion DoS.

                # Validate image format before passing to OCR
                try:
                    from gi.repository import GdkPixbuf

                    # Low-overhead variant: validate image header without scaling
                    stream = Gio.MemoryInputStream.new_from_bytes(GLib.Bytes.new(contents))
                    GdkPixbuf.Pixbuf.new_from_stream(stream, None)
                except GLib.Error as e:
                    self.welcome_page.spinner.set_visible(False)
                    if e.matches(GdkPixbuf.pixbuf_error_quark(), GdkPixbuf.PixbufError.CORRUPT_IMAGE):
                        logger.error(f"Validation: Corrupt or unsupported image structure: {e.message}")
                        self.show_toast(_("Corrupt or unsupported image file"))
                        return
                    elif e.matches(GdkPixbuf.pixbuf_error_quark(), GdkPixbuf.PixbufError.UNKNOWN_TYPE):
                        logger.error(f"Validation: Unknown image format: {e.message}")
                        self.show_toast(_("Unsupported image format"))
                        return
                    else:
                        logger.error(f"Validation: Image validation error: {e.message}")
                        self.show_toast(_("Failed to validate image file"))
                        return
                except (ValueError, RuntimeError, TypeError) as e:
                    self.welcome_page.spinner.set_visible(False)
                    logger.error(f"Validation: Unexpected image validation error: {e}")
                    self.show_toast(_("Failed to validate image file"))
                    return

                stream = BytesIO(contents)
                GObjectWorker.call(self.backend.decode_image, (self.get_language(), stream))
            else:
                self.welcome_page.spinner.set_visible(False)
                self.show_toast(_("Failed to load image file"))
        except (GLib.Error, OSError, ValueError, RuntimeError) as e:
            self.welcome_page.spinner.set_visible(False)
            logger.error(f"Failed to load file contents: {e}")
            self.show_toast(_("Failed to load image file"))

    def _navigate_to_extracted_page(self) -> bool:
        """Navigate to the extracted text page after OCR."""
        self.split_view.set_show_content(True)
        # Focus the text view to allow immediate keyboard interaction
        self.extracted_page.text_view.grab_focus()
        return GLib.SOURCE_REMOVE
