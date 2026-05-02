from gettext import gettext as _
from io import BytesIO
from mimetypes import guess_type
from urllib.parse import urlparse

from gi.repository import Adw, Gdk, Gio, GLib, Gtk
from loguru import logger

from anura.config import APP_ID, RESOURCE_PREFIX
from anura.gobject_worker import GObjectWorker
from anura.language_manager import language_manager
from anura.services.clipboard_service import clipboard_service
from anura.services.screenshot_service import ScreenshotService
from anura.services.share_service import ShareService
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

    def __init__(self, backend: ScreenshotService, **kwargs):
        super().__init__(**kwargs)

        self.settings = Gtk.Application.get_default().props.settings

        language_manager.active_language = language_manager.get_language_item(
            self.settings.get_string("active-language")
        )

        self._setup_geometry()
        self._setup_controllers()
        self.set_icon_name(APP_ID)

        # Safety timeout for portal screenshot (prevents hidden window on D-Bus hang)
        self._screenshot_timeout_id: int | None = None

        # Share service as instance attribute to avoid class-level launcher issues
        self.share_service = ShareService()
        share_action = Gio.SimpleAction.new("share", GLib.VariantType.new("s"))
        share_action.connect("activate", self._on_share)
        self.add_action(share_action)

        self.backend = backend
        self._handler_decoded = self.backend.connect("decoded", self.on_shot_done)
        self._handler_error = self.backend.connect("error", self.on_shot_error)

        self._handler_go_back = self.extracted_page.connect("go-back", self.show_welcome_page)
        self._handler_clipboard = None
        try:
            self._handler_clipboard = clipboard_service.connect("paste_from_clipboard", self._on_paste_from_clipboard)
        except RuntimeError as e:
            logger.warning(f"Clipboard service unavailable: {e}")

    def _setup_geometry(self):
        width = max(400, self.settings.get_int("window-width"))  # Min 400px
        height = max(300, self.settings.get_int("window-height"))  # Min 300px
        self.set_default_size(width, height)

    def _setup_controllers(self):
        drop_target = Gtk.DropTarget.new(type=Gdk.FileList, actions=Gdk.DragAction.COPY)
        drop_target.connect("drop", self.on_dnd_drop)
        self.split_view.add_controller(drop_target)

    def get_language(self) -> str:
        active = self.settings.get_string("active-language")
        extra = self.settings.get_string("extra-language")
        return f"{active}+{extra}" if extra else active

    def get_screenshot(self, copy: bool = False) -> None:
        self.extracted_page.listen_cancel()
        lang = self.get_language()
        self.hide()

        # Safety timeout: if portal doesn't respond within 30s, restore window
        self._screenshot_timeout_id = GLib.timeout_add_seconds(
            30, self._on_screenshot_timeout
        )

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

    def on_shot_done(self, _sender, text: str, copy: bool) -> None:
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

            if self.uri_validator(text):
                if self.settings.get_boolean("autolinks"):
                    launcher = Gtk.UriLauncher.new(text)
                    launcher.launch(self, None, None)
                    self.show_toast(_("URL opened automatically"))
                else:
                    self._show_url_toast(text)

            self.split_view.set_show_content(True)

        except Exception as e:
            logger.error(f"Anura UI Error: {e}")

    def on_shot_error(self, _sender, message: str) -> None:
        # Cancel safety timeout if screenshot failed
        if self._screenshot_timeout_id is not None:
            GLib.source_remove(self._screenshot_timeout_id)
            self._screenshot_timeout_id = None

        self.present()
        self.welcome_page.spinner.set_visible(False)
        if message:
            self.show_toast(message)

    def open_image(self):
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
        import os

        try:
            # Validate file size to prevent memory issues with very large images
            file_size = os.path.getsize(file_path)
            if file_size > self.MAX_IMAGE_SIZE_BYTES:
                self.show_toast(
                    _("Image too large: {size}MB (max {max}MB)").format(
                        size=round(file_size / (1024 * 1024), 1),
                        max=self.MAX_IMAGE_SIZE_MB
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

    def _on_open_image_result(self, dialog, result):
        try:
            file = dialog.open_finish(result)
            if file:
                self.welcome_page.spinner.set_visible(True)
                file.load_contents_async(None, self._on_file_contents_loaded)
        except Exception as e:
            logger.debug(f"File selection cancelled or failed: {e}")

    def _on_file_contents_loaded(self, gfile, result):
        try:
            ok, contents, _ = gfile.load_contents_finish(result)
            if ok:
                # Validate file size before processing (same check as DnD)
                file_size = len(contents)
                if file_size > self.MAX_IMAGE_SIZE_BYTES:
                    self.show_toast(
                        _("Image too large: {size}MB (max {max}MB)").format(
                            size=round(file_size / (1024 * 1024), 1),
                            max=self.MAX_IMAGE_SIZE_MB
                        )
                    )
                    return
                stream = BytesIO(contents)
                GObjectWorker.call(self.backend.decode_image, (self.get_language(), stream))
        except Exception as e:
            logger.error(f"Failed to load file contents: {e}")
            self.show_toast(_("Failed to load image file"))

    def on_dnd_drop(self, __target, value: Gdk.FileList, __x, __y) -> bool:
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
            item
        )
        return True

    def _on_dnd_query_info_done(self, gfile, result, item):
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

    def _on_dnd_file_contents_loaded(self, gfile, result):
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
                        size=round(file_size / (1024 * 1024), 1),
                        max=self.MAX_IMAGE_SIZE_MB
                    )
                )
                return

            stream = BytesIO(contents)
            GObjectWorker.call(self.backend.decode_image, (self.get_language(), stream))
        except Exception as e:
            logger.error(f"Failed to load dropped file: {e}")
            self.show_toast(_("Failed to load dropped file"))

    def _on_paste_from_clipboard(self, _service, texture: Gdk.Texture):
        self.welcome_page.spinner.set_visible(True)
        png_bytes = BytesIO(texture.save_to_png_bytes().get_data())
        GObjectWorker.call(self.backend.decode_image, (self.get_language(), png_bytes))

    def do_close_request(self) -> bool:
        width = self.get_width()
        height = self.get_height()
        self.settings.set_int("window-width", width)
        self.settings.set_int("window-height", height)
        return False

    def do_destroy(self):
        """Clean up signal handlers to prevent memory leaks."""
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

    def show_preferences(self):
        dialog = PreferencesDialog()
        dialog.present(self)

    def show_shortcuts(self):
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

    def show_welcome_page(self, *_):
        self.split_view.set_show_content(False)
        self.extracted_page.listen_cancel()

    def on_listen(self) -> None:
        """Starts TTS playback for the currently extracted text."""
        self.extracted_page.listen()

    def on_listen_cancel(self) -> None:
        """Stops any active TTS playback."""
        self.extracted_page.listen_cancel()

    def _on_share(self, _action, variant: GLib.Variant) -> None:
        """Dispatch share action to the correct provider."""
        provider = variant.get_string()
        text = self.extracted_page.extracted_text
        if not text:
            self.show_toast(_("No text to share."))
            return
        self.share_service.share(provider, text)

    def show_toast(self, title: str, priority=Adw.ToastPriority.NORMAL):
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
        launcher = Gtk.UriLauncher.new(url)
        launcher.launch(self, None, None)

    def uri_validator(self, text: str) -> bool:
        url = text.strip()

        # Block control characters (0x00-0x1F) and DEL (0x7F)
        # This prevents newline, tab, carriage return, null byte injection
        if any(ord(c) < 0x20 or ord(c) == 0x7F for c in url):
            return False

        # Ensure URL is ASCII-only (prevent Unicode homograph attacks)
        try:
            url.encode("ascii")
        except UnicodeEncodeError:
            return False

        try:
            res = urlparse(url)
            # Require valid scheme, netloc, and at least one dot in netloc
            # (prevents "http://localhost" or "http://evil" without TLD)
            return (
                res.scheme in ("http", "https")
                and bool(res.netloc)
                and "." in res.netloc
            )
        except ValueError:
            return False
