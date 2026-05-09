import contextlib
from gettext import gettext as _
from io import BytesIO
from mimetypes import guess_type
import os
import re

import gi

# Set GTK version requirements before imports
gi.require_version("Adw", "1")
gi.require_version("Gdk", "4.0")
gi.require_version("Gio", "2.0")
gi.require_version("GLib", "2.0")
gi.require_version("GObject", "2.0")
gi.require_version("Gtk", "4.0")

from gi.repository import Adw, Gdk, Gio, GLib, GObject, Gtk  # noqa: E402
from loguru import logger  # noqa: E402

from anura.config import APP_ID, RESOURCE_PREFIX  # noqa: E402
from anura.gobject_worker import GObjectWorker  # noqa: E402
from anura.language_manager import get_language_manager  # noqa: E402
from anura.services.clipboard_service import get_clipboard_service  # noqa: E402
from anura.services.screenshot_service import ScreenshotService  # noqa: E402
from anura.services.share_service import get_share_service  # noqa: E402
from anura.utils import uri_validator  # noqa: E402
from anura.widgets.extracted_page import ExtractedPage  # noqa: E402
from anura.widgets.preferences_dialog import PreferencesDialog  # noqa: E402
from anura.widgets.welcome_page import WelcomePage  # noqa: E402


@Gtk.Template(resource_path=f"{RESOURCE_PREFIX}/window.ui")
class AnuraWindow(Adw.ApplicationWindow):
    __gtype_name__ = "AnuraWindow"

    toast_overlay: Adw.ToastOverlay = Gtk.Template.Child()
    split_view: Adw.NavigationSplitView = Gtk.Template.Child()
    welcome_page: WelcomePage = Gtk.Template.Child()
    extracted_page: ExtractedPage = Gtk.Template.Child()

    def __init__(self, backend: ScreenshotService, **kwargs: object) -> None:
        super().__init__(**kwargs)

        app = Gtk.Application.get_default()
        if app is None:
            raise RuntimeError("Cannot get default application")
        self.settings = app.settings

        # Defensive: validate language from settings, fallback to English if corrupted
        lang_code = self.settings.get_string("active-language")
        language_manager_instance = get_language_manager()
        item = language_manager_instance.get_language_item(lang_code)
        if item is None:
            item = language_manager_instance.get_language_item("eng")
        if item is None:
            # Ultimate fallback - should never happen for built-in languages
            from anura.types.language_item import LanguageItem

            item = LanguageItem(code="eng", title="English")
        language_manager_instance.active_language = item

        self._setup_geometry()
        self._setup_controllers()
        self.set_icon_name(APP_ID)

        # Safety timeout for portal screenshot (prevents hidden window on D-Bus hang)
        self._screenshot_timeout_id: int | None = None

        # Use shared singleton instance
        self.share_service = get_share_service()
        share_action = Gio.SimpleAction.new("share", GLib.VariantType.new("s"))
        share_action.connect("activate", self._on_share)
        self.add_action(share_action)

        self.backend = backend
        self._handler_decoded = self.backend.connect("decoded", self.on_shot_done)
        self._handler_error = self.backend.connect("error", self.on_shot_error)

        self._handler_go_back = self.extracted_page.connect("go-back", self.show_welcome_page)
        self._handler_clipboard = None
        self._clipboard_service = None
        try:
            self._clipboard_service = get_clipboard_service()
            self._handler_clipboard = self._clipboard_service.connect(
                "paste_from_clipboard",
                self._on_paste_from_clipboard_texture,
            )
        except RuntimeError as e:
            logger.warning(f"Clipboard service unavailable: {e}")

    def _setup_geometry(self) -> None:
        width = max(400, self.settings.get_int("window-width"))  # Min 400px
        height = max(300, self.settings.get_int("window-height"))  # Min 300px
        self.set_default_size(width, height)

    def _setup_controllers(self) -> None:
        drop_target = Gtk.DropTarget.new(type=Gdk.FileList, actions=Gdk.DragAction.COPY)
        drop_target.connect("drop", self.on_dnd_drop)
        self.split_view.add_controller(drop_target)

    def get_language(self) -> str:
        """Get current language code from settings or language manager."""
        language_manager_instance = get_language_manager()
        return self.settings.get_string("active-language") or language_manager_instance.active_language.code

    def get_screenshot(self, copy: bool = False) -> None:
        """Capture screenshot and process it for OCR."""
        self.extracted_page.swap_controls(True)
        lang = self.get_language()
        self.hide()

        # Safety timeout: if portal doesn't respond within 30s, restore window
        self._screenshot_timeout_id = GLib.timeout_add_seconds(30, self._on_screenshot_timeout)

        try:
            self.backend.capture(lang, copy)
        except (GLib.Error, RuntimeError, OSError) as e:
            # Clean up timeout and restore window on error
            if self._screenshot_timeout_id is not None:
                GLib.source_remove(self._screenshot_timeout_id)
                self._screenshot_timeout_id = None
            self.present()
            logger.error(f"Anura: Screenshot capture failed: {e}")
            self.show_toast(_("Failed to capture screenshot"))

    def _on_screenshot_timeout(self) -> bool:
        """Handle screenshot portal timeout."""
        self._screenshot_timeout_id = None
        self.present()
        self.show_toast(_("Screenshot service did not respond."))
        logger.warning("Anura Screenshot: Portal timeout - window restored.")
        return False  # Don't repeat timeout

    def on_shot_done(self, _sender: GObject.GObject, text: str, copy: bool) -> None:
        """Handle successful screenshot capture and OCR processing."""
        # Cancel safety timeout if screenshot succeeded
        if self._screenshot_timeout_id is not None:
            GLib.source_remove(self._screenshot_timeout_id)
            self._screenshot_timeout_id = None

        self.present()
        self.welcome_page.spinner.set_visible(False)

        if not text:
            return

        try:
            self.extracted_page.extracted_text = text

            if self.settings.get_boolean("autocopy") or copy:
                clipboard_service_instance = get_clipboard_service()
                clipboard_service_instance.set(text)
                self.show_toast(_("Text copied to clipboard"))

            # Extract URL from OCR text (not just validate entire text as URL)
            try:
                extracted_url = self.extract_url_from_text(text)
                if extracted_url:
                    if self.settings.get_boolean("autolinks"):
                        self._launch_uri(extracted_url)
                        self.show_toast(_("URL opened automatically"))
                    else:
                        self._show_url_toast(extracted_url)
            except Exception as e:
                logger.error(f"Anura: Error extracting/launching URL: {e}")
                # Continue without URL functionality - don't crash the entire OCR flow

            # Defer navigation to ExtractedPage until window is properly mapped
            GLib.idle_add(self._navigate_to_extracted_page)

        except (GLib.Error, RuntimeError, AttributeError) as e:
            logger.error(f"Anura UI Error: {e}")

    def on_shot_error(self, _sender: GObject.GObject, message: str) -> None:
        """Handle screenshot capture errors."""
        # Cancel safety timeout if screenshot failed
        if self._screenshot_timeout_id is not None:
            GLib.source_remove(self._screenshot_timeout_id)
            self._screenshot_timeout_id = None

        self.present()
        self.welcome_page.spinner.set_visible(False)
        if message:
            self.show_toast(message)

    def open_image(self) -> None:
        """Open file dialog to select an image for OCR processing."""
        dialog = Gtk.FileDialog()
        dialog.set_title(_("Choose an image for extraction"))

        img_filter = Gtk.FileFilter()
        img_filter.set_name(_("Images"))
        img_filter.add_pixbuf_formats()

        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(img_filter)
        dialog.set_filters(filters)

        dialog.open(self, None, self._on_open_image_result)

    # Maximum image file size: 50MB to prevent memory exhaustion
    MAX_IMAGE_SIZE_MB = 50
    MAX_IMAGE_SIZE_BYTES = MAX_IMAGE_SIZE_MB * 1024 * 1024

    def process_file(self, file_path: str) -> None:
        """Process an image file directly from CLI."""
        try:
            # Validate file size to prevent memory issues with very large images
            # Use lstat to not follow symlinks (security: prevent symlink bypass)
            file_size = os.lstat(file_path).st_size
            if file_size > self.MAX_IMAGE_SIZE_BYTES:
                self.show_toast(
                    _("Image too large: {size}MB (max {max}MB)").format(
                        size=round(file_size / (1024 * 1024), 1),
                        max=self.MAX_IMAGE_SIZE_MB,
                    ),
                )
                return

            mimetype, _encoding = guess_type(file_path)
            if not mimetype or not mimetype.startswith("image"):
                self.show_toast(_("Unsupported file format: {path}").format(path=file_path))
                return

            self.welcome_page.spinner.set_visible(True)
            GObjectWorker.call(self.backend.decode_image, (self.get_language(), file_path))
        except FileNotFoundError:
            self.show_toast(_("File not found: {path}").format(path=file_path))
        except PermissionError:
            self.show_toast(_("Permission denied: {path}").format(path=file_path))
        except OSError as e:
            logger.error(f"Error accessing file {file_path}: {e}")
            self.show_toast(_("Cannot access file: {path}").format(path=file_path))

    def _on_open_image_result(self, dialog: Gtk.FileDialog, result: Gio.AsyncResult) -> None:
        try:
            file = dialog.open_finish(result)
            if file:
                self.welcome_page.spinner.set_visible(True)
                file.load_contents_async(None, self._on_file_contents_loaded)
        except (GLib.Error, RuntimeError, OSError) as e:
            logger.debug(f"File selection cancelled or failed: {e}")
            # Ensure spinner is hidden on error to prevent UI inconsistency
            self.welcome_page.spinner.set_visible(False)

    def _on_file_contents_loaded(self, gfile: Gio.File, result: Gio.AsyncResult) -> None:
        try:
            ok, contents, _ = gfile.load_contents_finish(result)
            if ok:
                # Validate file size before processing (same check as DnD)
                file_size = len(contents)
                if file_size > self.MAX_IMAGE_SIZE_BYTES:
                    self.welcome_page.spinner.set_visible(False)
                    self.show_toast(
                        _("Image too large: {size}MB (max {max}MB)").format(
                            size=round(file_size / (1024 * 1024), 1),
                            max=self.MAX_IMAGE_SIZE_MB,
                        ),
                    )
                    return

                # Validate image format before passing to OCR
                try:
                    from gi.repository import GdkPixbuf

                    stream = BytesIO(contents)
                    # Try to create a pixbuf to validate the image
                    GdkPixbuf.Pixbuf.new_from_stream_at_scale(
                        Gio.MemoryInputStream.new_from_bytes(GLib.Bytes.new(contents)),
                        -1,
                        -1,
                        False,
                        None,
                    )
                except GLib.Error as e:
                    self.welcome_page.spinner.set_visible(False)
                    if e.matches(GdkPixbuf.pixbuf_error_quark(), GdkPixbuf.PixbufError.CORRUPT_IMAGE):
                        logger.error(f"Anura: Corrupt image file: {e.message}")
                        self.show_toast(_("Corrupt or unsupported image file"))
                        return
                    elif e.matches(GdkPixbuf.pixbuf_error_quark(), GdkPixbuf.PixbufError.UNKNOWN_TYPE):
                        logger.error(f"Anura: Unknown image format: {e.message}")
                        self.show_toast(_("Unsupported image format"))
                        return
                    else:
                        logger.error(f"Anura: Image validation error: {e.message}")
                        self.show_toast(_("Failed to validate image file"))
                        return
                except (ValueError, RuntimeError) as e:
                    self.welcome_page.spinner.set_visible(False)
                    logger.error(f"Anura: Unexpected image validation error: {e}")
                    self.show_toast(_("Failed to validate image file"))
                    return

                stream = BytesIO(contents)
                GObjectWorker.call(self.backend.decode_image, (self.get_language(), stream))
            else:
                self.welcome_page.spinner.set_visible(False)
                self.show_toast(_("Failed to load image file"))
        except (OSError, ValueError, RuntimeError) as e:
            self.welcome_page.spinner.set_visible(False)
            logger.error(f"Failed to load file contents: {e}")
            self.show_toast(_("Failed to load image file"))

    def on_dnd_drop(self, __target: Gtk.DropTarget, value: Gdk.FileList, __x: int, __y: int) -> bool:
        """Handle drag-and-drop file operations."""
        files = value.get_files()
        if not files:
            return False

        item = files[0]

        self.welcome_page.spinner.set_visible(True)
        item.query_info_async(
            "standard::content-type",
            Gio.FileQueryInfoFlags.NONE,
            GLib.PRIORITY_DEFAULT,
            None,
            self._on_dnd_query_info_done,
            item,
        )
        return True

    def _on_dnd_query_info_done(self, gfile: Gio.File, result: Gio.AsyncResult, item: Gio.FileInfo) -> None:
        try:
            info = gfile.query_info_finish(result)
            if not info:
                self.welcome_page.spinner.set_visible(False)
                return

            mimetype = info.get_content_type()
            if not mimetype or not mimetype.startswith("image"):
                self.welcome_page.spinner.set_visible(False)
                self.show_toast(_("Unsupported file format."))
                return

            item.load_contents_async(None, self._on_dnd_file_contents_loaded)
        except (GLib.Error, OSError, RuntimeError) as e:
            logger.error(f"DnD query_info failed: {e}")
            self.welcome_page.spinner.set_visible(False)

    def _on_dnd_file_contents_loaded(self, gfile: Gio.File, result: Gio.AsyncResult) -> None:
        try:
            ok, contents, _ = gfile.load_contents_finish(result)
            if not ok:
                self.welcome_page.spinner.set_visible(False)
                self.show_toast(_("Failed to load dropped file"))
                return

            # Validate file size
            file_size = len(contents)
            if file_size > self.MAX_IMAGE_SIZE_BYTES:
                self.welcome_page.spinner.set_visible(False)
                self.show_toast(
                    _("Image too large: {size}MB (max {max}MB)").format(
                        size=round(file_size / (1024 * 1024), 1),
                        max=self.MAX_IMAGE_SIZE_MB,
                    ),
                )
                return

            stream = BytesIO(contents)
            GObjectWorker.call(self.backend.decode_image, (self.get_language(), stream))
        except (OSError, ValueError, RuntimeError) as e:
            self.welcome_page.spinner.set_visible(False)
            logger.error(f"Failed to load dropped file: {e}")
            self.show_toast(_("Failed to load dropped file"))

    def on_copy_to_clipboard(self, _action: Gio.SimpleAction) -> None:
        """Copy the current extracted text to the clipboard."""
        return self._do_copy_to_clipboard()

    def _do_copy_to_clipboard(self) -> None:
        text = self.extracted_page.extracted_text
        if text:
            clipboard_service_instance = get_clipboard_service()
            clipboard_service_instance.set(text)
            self.show_toast(_("Text copied to clipboard"))
        else:
            self.show_toast(_("No text to copy"))

    def on_paste_from_clipboard(self, _action: Gio.SimpleAction) -> None:
        """Read image from clipboard and perform OCR."""
        self.welcome_page.spinner.set_visible(True)
        clipboard_service_instance = get_clipboard_service()
        clipboard_service_instance.read_texture()

    def _on_paste_from_clipboard_texture(self, _service: GObject.GObject, texture: Gdk.Texture) -> None:
        self.welcome_page.spinner.set_visible(True)
        png_bytes = BytesIO(texture.save_to_png_bytes().get_data())
        GObjectWorker.call(self.backend.decode_image, (self.get_language(), png_bytes))

    def do_close_request(self) -> bool:
        """Handle window close request and save window state."""
        width = self.get_width()
        height = self.get_height()
        self.settings.set_int("window-width", width)
        self.settings.set_int("window-height", height)
        return False

    def do_destroy(self) -> None:
        """Clean up signal handlers and timeouts to prevent memory leaks."""
        # Cancel screenshot timeout if active
        if self._screenshot_timeout_id is not None:
            GLib.source_remove(self._screenshot_timeout_id)
            self._screenshot_timeout_id = None

        # Cancel any pending clipboard operations before disconnecting handler
        clipboard_service_instance = get_clipboard_service()
        clipboard_service_instance.cancel_pending_operations()

        # Disconnect backend signal handlers
        if self.backend:
            if self._handler_decoded:
                with contextlib.suppress(TypeError, RuntimeError):
                    # Handler already disconnected or object disposed
                    self.backend.disconnect(self._handler_decoded)
                self._handler_decoded = None
            if self._handler_error:
                with contextlib.suppress(TypeError, RuntimeError):
                    self.backend.disconnect(self._handler_error)
                self._handler_error = None

        # Disconnect widget signal handlers
        if self._handler_go_back:
            with contextlib.suppress(TypeError, RuntimeError):
                self.extracted_page.disconnect(self._handler_go_back)
            self._handler_go_back = None
        if self._handler_clipboard and self._clipboard_service:
            with contextlib.suppress(TypeError, RuntimeError):
                self._clipboard_service.disconnect(self._handler_clipboard)
            self._handler_clipboard = None

        # Chain up to parent class
        super().do_destroy()

    def show_preferences(self) -> None:
        """Show the preferences dialog for application settings."""
        dialog = PreferencesDialog()

        # Get service instances
        language_manager_instance = get_language_manager()

        # Track signal handler IDs for cleanup
        signal_handlers = []

        def on_dialog_close(*args: object) -> None:
            """Clean up signal connections when dialog is closed."""
            for handler_id in signal_handlers:
                try:
                    language_manager_instance.disconnect(handler_id)
                except (TypeError, RuntimeError):
                    pass  # Handler already disconnected or invalid

        # Connect to language manager signals and track handler IDs
        downloaded_handler = language_manager_instance.connect(
            "downloaded",
            lambda _mgr, code: GLib.idle_add(dialog.on_language_downloaded, code),
        )
        signal_handlers.append(downloaded_handler)

        failed_handler = language_manager_instance.connect(
            "download-failed",
            lambda _mgr, code: GLib.idle_add(dialog.on_language_download_failed, code),
        )
        signal_handlers.append(failed_handler)

        # Connect cleanup to dialog close signal
        dialog.connect("close-request", on_dialog_close)

        dialog.present(self)

    def show_shortcuts(self) -> None:
        """Show the keyboard shortcuts overlay."""
        try:
            from anura.widgets.shortcuts_overlay import show_shortcuts_overlay

            show_shortcuts_overlay(self)
        except (ImportError, RuntimeError) as e:
            logger.error(f"Failed to show shortcuts overlay: {e}")

    def _navigate_to_extracted_page(self) -> bool:
        """Navigate to the extracted text page after OCR."""
        self.split_view.set_show_content(True)
        return GLib.SOURCE_REMOVE

    def show_welcome_page(self, *_args: object) -> None:
        """Show the welcome page and hide the extracted content."""
        self.split_view.set_show_content(False)
        self.extracted_page._on_listen_stop()

    def on_listen(self) -> None:
        """Start TTS playback for the currently extracted text."""
        self.extracted_page.listen()

    def on_listen_cancel(self) -> None:
        """Stop any active TTS playback."""
        self.extracted_page._on_listen_stop()

    def _on_share(self, _action: Gio.SimpleAction, variant: GLib.Variant) -> None:
        """Dispatch share action to the correct provider."""
        provider = variant.get_string()
        text = self.extracted_page.extracted_text
        if not text:
            self.show_toast(_("No text to share."))
            return
        self.share_service.share(provider, text)

    def show_toast(self, title: str, priority: Adw.ToastPriority = Adw.ToastPriority.NORMAL) -> None:
        """Show a toast notification to the user."""
        self.toast_overlay.add_toast(Adw.Toast(title=title, priority=priority))

    def _show_url_toast(self, url: str) -> None:
        toast = Adw.Toast(
            title=_("Text contains a link"),
            button_label=_("Open"),
        )
        toast.connect("button-clicked", lambda _: self._launch_uri(url))
        self.toast_overlay.add_toast(toast)

    def _launch_uri(self, url: str) -> None:
        """Open a URI in the default system browser."""
        # Security: validate URL before launching (defense in depth)
        if not uri_validator(url):
            logger.warning(f"Anura: Blocked invalid URL launch: {url}")
            self.show_toast(_("Invalid URL blocked for security"))
            return
        launcher = Gtk.UriLauncher.new(url)
        launcher.launch(self, None, None)

    # Maximum URL length to prevent issues with extremely long OCR results
    MAX_URL_LENGTH = 2048

    def extract_url_from_text(self, text: str) -> str | None:
        """Extract the first valid URL from OCR text using regex.

        Returns the URL if found and valid, None otherwise.
        """
        # Null check to prevent errors with None input
        if text is None:
            return None
        # Regex to find URLs starting with http:// or https://
        # Use * instead of + to apply quantifier to entire character class
        url_pattern = re.compile(r'https?://[^\s<>"{}|\\^`\[\]]*')
        match = url_pattern.search(text)
        if match:
            url = match.group(0).rstrip(".,;:")
            # Length check to prevent issues with extremely long URLs
            if len(url) > self.MAX_URL_LENGTH:
                logger.warning(f"Anura: URL too long ({len(url)} chars), ignoring.")
                return None
            if uri_validator(url):
                return url
        return None
