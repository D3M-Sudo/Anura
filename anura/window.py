# This file is part of Anura.
# Copyright (C) 2022-2025 Andrey Maksimov (Frog)
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import contextlib
from gettext import gettext as _
from io import BytesIO
from mimetypes import guess_type

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

from anura.atomic_task_manager import get_atomic_manager  # noqa: E402
from anura.config import APP_ID, RESOURCE_PREFIX  # noqa: E402
from anura.controllers.dnd_controller import DndController  # noqa: E402
from anura.controllers.ocr_controller import OcrController  # noqa: E402
from anura.controllers.tts_controller import TtsController  # noqa: E402
from anura.language_manager import get_language_manager  # noqa: E402
from anura.services.clipboard_service import get_clipboard_service  # noqa: E402
from anura.services.screenshot_service import ScreenshotService  # noqa: E402
from anura.services.share_service import get_share_service  # noqa: E402
from anura.types.context import get_app_context  # noqa: E402
from anura.utils import validate_image_resource  # noqa: E402
from anura.utils.signal_manager import SignalManagerMixin  # noqa: E402
from anura.widgets.extracted_page import ExtractedPage  # noqa: E402
from anura.widgets.preferences_dialog import PreferencesDialog  # noqa: E402
from anura.widgets.welcome_page import WelcomePage  # noqa: E402


@Gtk.Template(resource_path=f"{RESOURCE_PREFIX}/window.ui")
class AnuraWindow(Adw.ApplicationWindow, SignalManagerMixin):
    __gtype_name__ = "AnuraWindow"

    toast_overlay: Adw.ToastOverlay = Gtk.Template.Child()
    split_view: Adw.NavigationSplitView = Gtk.Template.Child()
    welcome_page: WelcomePage = Gtk.Template.Child()
    extracted_page: ExtractedPage = Gtk.Template.Child()
    portal_banner: Adw.Banner = Gtk.Template.Child()

    def __init__(self, backend: ScreenshotService, **kwargs: object) -> None:
        super().__init__(**kwargs)
        SignalManagerMixin.__init__(self)

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

            item = LanguageItem(code="eng", title=_("English"))
        language_manager_instance.active_language = item  # type: ignore[method-assign]

        self._setup_geometry()
        self._apply_capability_constraints()
        self.set_icon_name(APP_ID)

        # Safety timeout for portal screenshot (prevents hidden window on D-Bus hang)
        self._screenshot_timeout_id: int | None = None

        # Use shared singleton instance
        self.share_service = get_share_service()
        share_action = Gio.SimpleAction.new("share", GLib.VariantType.new("s"))
        self.connect_tracked(share_action, "activate", self._on_share)
        self.add_action(share_action)

        self.backend = backend
        self.ocr_controller = OcrController(self)
        self.tts_controller = TtsController(self)
        self.dnd_controller = DndController(self)

        self.connect_tracked(self.extracted_page, "go-back", self.show_welcome_page)  # type: ignore[arg-type]
        self._clipboard_service = None
        try:
            self._clipboard_service = get_clipboard_service()
            self.connect_tracked(
                self._clipboard_service,
                "paste_from_clipboard",
                self._on_paste_from_clipboard_texture,
            )
            self.connect_tracked(
                self._clipboard_service,
                "error",
                self._on_clipboard_error,
            )
        except RuntimeError as e:
            logger.warning(f"Clipboard service unavailable: {e}")

    def _setup_geometry(self) -> None:
        width = max(400, self.settings.get_int("window-width"))  # Min 400px
        height = max(300, self.settings.get_int("window-height"))  # Min 300px
        self.set_default_size(width, height)

        # Connect to surface scale changes to handle multi-monitor DPI scaling
        self.connect("notify::scale-factor", self._on_scale_factor_changed)

    def _apply_capability_constraints(self) -> None:
        """Apply UI sensitivity constraints based on the boot-time capability audit."""
        ctx = get_app_context()

        # If OCR is missing, disable core capture actions
        if not ctx.has_ocr:
            logger.warning("Anura: OCR capability missing. Disabling capture UI.")
            self.welcome_page.screenshot_button.set_sensitive(False)
            self.welcome_page.screenshot_button.set_tooltip_text(_("Tesseract OCR not found on system"))

        # If TTS is missing, disable listen button on extracted page
        if not ctx.has_tts:
            logger.warning("Anura: TTS capability missing. Disabling Listen UI.")
            self.extracted_page.listen_btn.set_sensitive(False)
            self.extracted_page.listen_btn.set_tooltip_text(_("TTS dependencies (gTTS/GStreamer) missing"))

    def _on_scale_factor_changed(self, _window: Gtk.Window, _pspec: GObject.ParamSpec) -> None:
        scale = self.get_scale_factor()
        logger.debug(f"Anura: Window scale factor changed to {scale}")
        # Ensure the window is properly resized/redrawn if needed
        self.queue_resize()

    def get_language(self) -> str:
        """Get current language code from settings or language manager."""
        language_manager_instance = get_language_manager()
        return self.settings.get_string("active-language") or language_manager_instance.active_language.code

    def _on_screenshot_timeout(self) -> bool:
        """Restore window if portal screenshot doesn't respond within 30s."""
        self._screenshot_timeout_id = None
        self.present()
        self.show_toast(_("Screenshot timed out. Please try again."))
        logger.warning("Anura: Screenshot portal timeout — restoring window.")
        return GLib.SOURCE_REMOVE

    def get_screenshot(self, copy: bool = False) -> None:
        """Capture screenshot and process it for OCR."""
        lang = self.get_language()
        self.hide()

        # Safety timeout: if portal doesn't respond within 30s, restore window
        if self._screenshot_timeout_id is not None:
            GLib.source_remove(self._screenshot_timeout_id)

        self._screenshot_timeout_id = GLib.timeout_add_seconds(30, self._on_screenshot_timeout)

        try:
            # Check if backend is already capturing before hiding
            if hasattr(self.backend, "_is_capturing") and self.backend._is_capturing:
                logger.warning("Anura: Capture already in progress, not hiding window.")
                if self._screenshot_timeout_id is not None:
                    GLib.source_remove(self._screenshot_timeout_id)
                    self._screenshot_timeout_id = None
                self.present()
                return

            self.backend.capture(lang, copy)
        except (GLib.Error, RuntimeError, OSError) as e:
            # Clean up timeout and restore window on error
            if self._screenshot_timeout_id is not None:
                GLib.source_remove(self._screenshot_timeout_id)
                self._screenshot_timeout_id = None
            self.present()
            logger.error(f"Anura: Screenshot capture failed: {e}")
            self.show_toast(_("Failed to capture screenshot"))

    def process_file(self, file_path: str) -> None:
        """Process an image file directly from CLI."""
        try:
            is_valid, _size, error = validate_image_resource(file_path)
            if not is_valid:
                logger.error(f"Anura OCR: {error}")
                self.show_toast(_(error) if error else _("Invalid image file"))
                return

            mimetype, _encoding = guess_type(file_path)
            if not mimetype or not mimetype.startswith("image"):
                self.show_toast(_("Unsupported file format: {path}").format(path=file_path))
                return

            self.welcome_page.show_spinner()
            get_atomic_manager().execute(self.backend.decode_image, (self.get_language(), file_path))
        except FileNotFoundError:
            self.show_toast(_("File not found: {path}").format(path=file_path))
        except PermissionError:
            self.show_toast(_("Permission denied: {path}").format(path=file_path))
        except OSError as e:
            logger.error(f"Error accessing file {file_path}: {e}")
            self.show_toast(_("Cannot access file: {path}").format(path=file_path))

    def _do_copy_to_clipboard(self) -> None:
        text = self.extracted_page.extracted_text
        if text:
            get_clipboard_service().set(text)
            self.show_toast(_("Text copied to clipboard"))
            self.extracted_page.show_copy_feedback()
        else:
            self.show_toast(_("No text to copy"))

    def _on_paste_from_clipboard_texture(self, _service: GObject.GObject, texture: Gdk.Texture) -> None:
        self.welcome_page.show_spinner()
        png_bytes = BytesIO(texture.save_to_png_bytes().get_data())
        get_atomic_manager().execute(self.backend.decode_image, (self.get_language(), png_bytes))

    def _on_clipboard_error(self, _service: GObject.GObject, message: str) -> None:
        """Handle clipboard service errors."""
        self.welcome_page.spinner.set_visible(False)
        if message:
            self.show_toast(message)

    def do_close_request(self) -> bool:
        """Handle window close request and save window state."""
        width = self.get_width()
        height = self.get_height()
        self.settings.set_int("window-width", width)
        self.settings.set_int("window-height", height)
        return False

    def do_destroy(self) -> None:
        """Clean up signal handlers and timeouts to prevent memory leaks."""
        if self._screenshot_timeout_id is not None:
            GLib.source_remove(self._screenshot_timeout_id)
            self._screenshot_timeout_id = None

        clipboard_service_instance = get_clipboard_service()
        clipboard_service_instance.cancel_pending_operations()

        # Note: self.teardown_all() is now called automatically by SignalManagerMixin
        # via the 'destroy' signal connection established during __init__.

        super().do_destroy()

    def show_preferences(self) -> None:
        """Show the preferences dialog for application settings."""
        self.set_focus(None)
        dialog = PreferencesDialog()
        language_manager_instance = get_language_manager()
        signal_handlers: list[int] = []

        def on_dialog_close(*args: object) -> None:
            for handler_id in signal_handlers:
                try:
                    language_manager_instance.disconnect(handler_id)
                except (TypeError, RuntimeError):
                    pass

        def _on_downloaded_idle(_mgr, code):
            GLib.idle_add(dialog.on_language_downloaded, code)

        def _on_failed_idle(_mgr, code):
            GLib.idle_add(dialog.on_language_download_failed, code)

        signal_handlers.append(language_manager_instance.connect("downloaded", _on_downloaded_idle))
        signal_handlers.append(language_manager_instance.connect("download-failed", _on_failed_idle))
        dialog.connect("closed", on_dialog_close)
        dialog.present(self)

    def show_shortcuts(self) -> None:
        """Show the keyboard shortcuts overlay."""
        self.set_focus(None)
        try:
            from anura.widgets.shortcuts_overlay import show_shortcuts_overlay

            show_shortcuts_overlay(self)
        except (ImportError, RuntimeError) as e:
            logger.error(f"Failed to show shortcuts overlay: {e}")

    def show_welcome_page(self, *_args: object) -> None:
        """Show the welcome page and hide the extracted content."""
        self.split_view.set_show_content(False)
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

    def _launch_uri(self, url: str) -> None:
        """Open a URI in the default system browser."""
        from anura.utils.validators import launch_uri

        launch_uri(url, window=self, error_callback=lambda msg: self.show_toast(msg))

    def on_listen(self) -> None:
        """Trigger TTS playback on the extracted page."""
        self.extracted_page.listen()

    def on_listen_cancel(self) -> None:
        """Cancel TTS playback."""
        self.extracted_page.listen_cancel()

    def on_listen_pause(self) -> None:
        """Toggle TTS pause/resume."""
        self.extracted_page.listen_pause()

    def close_popovers(self) -> None:
        """Close all open popovers."""
        try:
            share_popover = self.extracted_page.share_button.get_popover()
            if share_popover and share_popover.get_visible():
                share_popover.popdown()
        except (AttributeError, RuntimeError, TypeError):
            pass

        for page in (self.welcome_page, self.extracted_page):
            if page:
                self._close_page_menu_popovers(page)

    def _close_page_menu_popovers(self, page: Adw.NavigationPage) -> None:
        child = page.get_first_child()
        while child is not None:
            if isinstance(child, Adw.ToolbarView):
                self._close_toolbar_view_popovers(child)
                return
            child = child.get_next_sibling()

    def _close_toolbar_view_popovers(self, toolbar_view: Adw.ToolbarView) -> None:
        child = toolbar_view.get_first_child()
        while child is not None:
            if isinstance(child, Adw.HeaderBar):
                self._close_header_bar_popovers(child)
                return
            child = child.get_next_sibling()

    def _close_header_bar_popovers(self, headerbar: Adw.HeaderBar) -> None:
        child = headerbar.get_first_child()
        while child is not None:
            if isinstance(child, Gtk.MenuButton):
                with contextlib.suppress(AttributeError, RuntimeError, TypeError):
                    popover = child.get_popover()
                    if popover and popover.get_visible():
                        popover.popdown()
            child = child.get_next_sibling()
