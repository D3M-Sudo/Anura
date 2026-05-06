from gettext import gettext as _
from io import BytesIO
from mimetypes import guess_type
import os
import re

from gi.repository import Adw, Gdk, Gio, GLib, GObject, Gtk
from loguru import logger

from anura.config import APP_ID, LANG_CODE_PATTERN, RESOURCE_PREFIX
from anura.gobject_worker import GObjectWorker
from anura.language_manager import language_manager
from anura.services.clipboard_service import clipboard_service
from anura.services.screenshot_service import ScreenshotService
from anura.services.share_service import share_service
from anura.utils import uri_validator
from anura.widgets.extracted_page import ExtractedPage
from anura.widgets.preferences_dialog import PreferencesDialog
from anura.widgets.welcome_page import WelcomePage


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
        item = language_manager.get_language_item(lang_code)
        if item is None:
            item = language_manager.get_language_item("eng")
        if item is None:
            # Ultimate fallback - should never happen for built-in languages
            from anura.types.language_item import LanguageItem
            item = LanguageItem(code="eng", title="English")
        language_manager.active_language = item

        self._setup_geometry()
        self._setup_controllers()
        self.set_icon_name(APP_ID)

        # Safety timeout for portal screenshot (prevents hidden window on D-Bus hang)
        self._screenshot_timeout_id: int | None = None

        # Use shared singleton instance
        self.share_service = share_service
        share_action = Gio.SimpleAction.new("share", GLib.VariantType.new("s"))
        share_action.connect("activate", self._on_share)
        self.add_action(share_action)

        self.backend = backend
        self._handler_decoded = self.backend.connect("decoded", self.on_shot_done)
        self._handler_error = self.backend.connect("error", self.on_shot_error)

        self._handler_go_back = self.extracted_page.connect("go-back", self.show_welcome_page)
        self._handler_clipboard = None
        try:
            self._handler_clipboard = clipboard_service.connect(
                "paste_from_clipboard",
                self._on_paste_from_clipboard_texture
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
        active = self.settings.get_string("active-language")
        extra = self.settings.get_string("extra-language")
        combined = f"{active}+{extra}" if extra else active

        # Validate combined language code against LANG_CODE_PATTERN
        if not re.match(LANG_CODE_PATTERN, combined):
            logger.warning(f"Anura: Invalid combined language code '{combined}', falling back to 'eng'")
            return "eng"

        return combined

    def get_screenshot(self, copy: bool = False) -> None:
        self.extracted_page.listen_cancel()
        lang = self.get_language()
        self.hide()

        # Safety timeout: if portal doesn't respond within 30s, restore window
        self._screenshot_timeout_id = GLib.timeout_add_seconds(30, self._on_screenshot_timeout)

        try:
            self.backend.capture(lang, copy)
        except Exception as e:
            # Clean up timeout and restore window on error
            if self._screenshot_timeout_id is not None:
                GLib.source_remove(self._screenshot_timeout_id)
                self._screenshot_timeout_id = None
            self.present()
            logger.error(f"Anura: Screenshot capture failed: {e}")
            self.show_toast(_("Failed to capture screenshot"))

    def _on_screenshot_timeout(self) -> bool:
        """Callback triggered when screenshot portal times out."""
        self._screenshot_timeout_id = None
        self.present()
        self.show_toast(_("Screenshot service did not respond."))
        logger.warning("Anura Screenshot: Portal timeout - window restored.")
        return False  # Don't repeat timeout

    def on_shot_done(self, _sender: GObject.GObject, text: str, copy: bool) -> None:
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
                clipboard_service.set(text)
                self.show_toast(_("Text copied to clipboard"))

            # Extract URL from OCR text (not just validate entire text as URL)
            extracted_url = self.extract_url_from_text(text)
            if extracted_url:
                if self.settings.get_boolean("autolinks"):
                    self._launch_uri(extracted_url)
                    self.show_toast(_("URL opened automatically"))
                else:
                    self._show_url_toast(extracted_url)

            self.split_view.set_show_content(True)

        except Exception as e:
            logger.error(f"Anura UI Error: {e}")

    def on_shot_error(self, _sender: GObject.GObject, message: str) -> None:
        # Cancel safety timeout if screenshot failed
        if self._screenshot_timeout_id is not None:
            GLib.source_remove(self._screenshot_timeout_id)
            self._screenshot_timeout_id = None

        self.present()
        self.welcome_page.spinner.set_visible(False)
        if message:
            self.show_toast(message)

    def open_image(self) -> None:
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
                        size=round(file_size / (1024 * 1024), 1), max=self.MAX_IMAGE_SIZE_MB
                    )
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
        except Exception as e:
            logger.debug(f"File selection cancelled or failed: {e}")

    def _on_file_contents_loaded(self, gfile: Gio.File, result: Gio.AsyncResult) -> None:
        try:
            ok, contents, _ = gfile.load_contents_finish(result)
            if ok:
                # Validate file size before processing (same check as DnD)
                file_size = len(contents)
                if file_size > self.MAX_IMAGE_SIZE_BYTES:
                    self.show_toast(
                        _("Image too large: {size}MB (max {max}MB)").format(
                            size=round(file_size / (1024 * 1024), 1), max=self.MAX_IMAGE_SIZE_MB
                        )
                    )
                    return

                # Validate image format before passing to OCR
                try:
                    from gi.repository import GdkPixbuf
                    stream = BytesIO(contents)
                    # Try to create a pixbuf to validate the image
                    GdkPixbuf.Pixbuf.new_from_stream_at_scale(
                        Gio.MemoryInputStream.new_from_bytes(GLib.Bytes.new(contents)),
                        -1, -1, False, None
                    )
                except GLib.Error as e:
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
                except Exception as e:
                    logger.error(f"Anura: Unexpected image validation error: {e}")
                    self.show_toast(_("Failed to validate image file"))
                    return

                stream = BytesIO(contents)
                GObjectWorker.call(self.backend.decode_image, (self.get_language(), stream))
        except Exception as e:
            logger.error(f"Failed to load file contents: {e}")
            self.show_toast(_("Failed to load image file"))

    def on_dnd_drop(self, __target: Gtk.DropTarget, value: Gdk.FileList, __x: int, __y: int) -> bool:
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
        except Exception as e:
            logger.error(f"DnD query_info failed: {e}")
            self.welcome_page.spinner.set_visible(False)

    def _on_dnd_file_contents_loaded(self, gfile: Gio.File, result: Gio.AsyncResult) -> None:
        try:
            ok, contents, _ = gfile.load_contents_finish(result)
            if not ok:
                self.show_toast(_("Failed to load dropped file"))
                return

            # Validate file size
            file_size = len(contents)
            if file_size > self.MAX_IMAGE_SIZE_BYTES:
                self.show_toast(
                    _("Image too large: {size}MB (max {max}MB)").format(
                        size=round(file_size / (1024 * 1024), 1), max=self.MAX_IMAGE_SIZE_MB
                    )
                )
                return

            stream = BytesIO(contents)
            GObjectWorker.call(self.backend.decode_image, (self.get_language(), stream))
        except Exception as e:
            logger.error(f"Failed to load dropped file: {e}")
            self.show_toast(_("Failed to load dropped file"))

    def on_copy_to_clipboard(self, _action: Gio.SimpleAction) -> None:
        """Copy the current extracted text to the clipboard."""
        return self._do_copy_to_clipboard()

    def _do_copy_to_clipboard(self) -> None:
        text = self.extracted_page.extracted_text
        if text:
            clipboard_service.set(text)
            self.show_toast(_("Text copied to clipboard"))
        else:
            self.show_toast(_("No text to copy"))

    def copy_to_clipboard_direct(self) -> None:
        """Direct copy method for internal use without action parameter."""
        text = self.extracted_page.extracted_text
        if text:
            clipboard_service.set(text)
            self.show_toast(_("Text copied to clipboard"))
        else:
            self.show_toast(_("No text to copy"))

    def on_paste_from_clipboard(self, _action: Gio.SimpleAction) -> None:
        """Read image from clipboard and perform OCR."""
        self.welcome_page.spinner.set_visible(True)
        clipboard_service.read_texture()

    def _on_paste_from_clipboard_texture(self, _service: GObject.GObject, texture: Gdk.Texture) -> None:
        self.welcome_page.spinner.set_visible(True)
        png_bytes = BytesIO(texture.save_to_png_bytes().get_data())
        GObjectWorker.call(self.backend.decode_image, (self.get_language(), png_bytes))

    def do_close_request(self) -> bool:
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
        clipboard_service.cancel_pending_operations()

        # Disconnect backend signal handlers
        if self.backend:
            if self._handler_decoded:
                try:
                    self.backend.disconnect(self._handler_decoded)
                except (TypeError, RuntimeError):
                    pass  # Handler already disconnected or object disposed
                self._handler_decoded = None
            if self._handler_error:
                try:
                    self.backend.disconnect(self._handler_error)
                except (TypeError, RuntimeError):
                    pass
                self._handler_error = None

        # Disconnect widget signal handlers
        if self._handler_go_back:
            try:
                self.extracted_page.disconnect(self._handler_go_back)
            except (TypeError, RuntimeError):
                pass
            self._handler_go_back = None
        if self._handler_clipboard:
            try:
                clipboard_service.disconnect(self._handler_clipboard)
            except (TypeError, RuntimeError):
                pass
            self._handler_clipboard = None

        # Chain up to parent class
        super().do_destroy()

    def show_preferences(self) -> None:
        dialog = PreferencesDialog()
        dialog.present(self)

    def show_shortcuts(self) -> None:
        try:
            builder = Gtk.Builder.new_from_resource(f"{RESOURCE_PREFIX}/shortcuts.ui")
            shortcuts_window = builder.get_object("shortcuts")

            if shortcuts_window:
                shortcuts_window.set_transient_for(self)
                shortcuts_window.present()
            else:
                logger.error("Failed to locate 'shortcuts' object in the UI resource.")
        except Exception as e:
            logger.error(f"An error occurred while loading shortcuts: {e}")

    def show_welcome_page(self, *_args: object) -> None:
        self.split_view.set_show_content(False)
        self.extracted_page.listen_cancel()

    def on_listen(self) -> None:
        """Starts TTS playback for the currently extracted text."""
        self.extracted_page.listen()

    def on_listen_cancel(self) -> None:
        """Stops any active TTS playback."""
        self.extracted_page.listen_cancel()

    def _on_share(self, _action: Gio.SimpleAction, variant: GLib.Variant) -> None:
        """Dispatch share action to the correct provider."""
        provider = variant.get_string()
        text = self.extracted_page.extracted_text
        if not text:
            self.show_toast(_("No text to share."))
            return
        self.share_service.share(provider, text)

    def show_toast(self, title: str, priority: Adw.ToastPriority = Adw.ToastPriority.NORMAL) -> None:
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

    def uri_validator(self, text: str) -> bool:
        """Delegate to centralized uri_validator from anura.utils."""
        return uri_validator(text)

    # Maximum URL length to prevent issues with extremely long OCR results
    MAX_URL_LENGTH = 2048

    def extract_url_from_text(self, text: str) -> str | None:
        """
        Extract the first valid URL from OCR text using regex.
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
            url = match.group(0).rstrip('.,;:)')
            # Length check to prevent issues with extremely long URLs
            if len(url) > self.MAX_URL_LENGTH:
                logger.warning(f"Anura: URL too long ({len(url)} chars), ignoring.")
                return None
            if self.uri_validator(url):
                return url
        return None
