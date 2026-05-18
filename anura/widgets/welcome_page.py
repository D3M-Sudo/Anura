# welcome_page.py
#
# Copyright 2021-2025 Andrey Maksimov
# Copyright 2026 D3M-Sudo (Anura fork and modifications)

import contextlib
from gettext import gettext as _
from mimetypes import guess_type
import os

from gi.repository import Adw, Gdk, Gio, GLib, Gtk
from loguru import logger

from anura.config import RESOURCE_PREFIX
from anura.language_manager import language_manager
from anura.services.settings import settings
from anura.types.language_item import LanguageItem
from anura.widgets.language_popover import LanguagePopover


@Gtk.Template(resource_path=f"{RESOURCE_PREFIX}/welcome_page.ui")
class WelcomePage(Adw.NavigationPage):
    __gtype_name__ = "WelcomePage"

    spinner: Gtk.Spinner = Gtk.Template.Child()
    welcome: Adw.StatusPage = Gtk.Template.Child()
    lang_combo: Gtk.MenuButton = Gtk.Template.Child()
    language_popover: LanguagePopover = Gtk.Template.Child()
    drop_button: Gtk.Button = Gtk.Template.Child()
    drop_area: Gtk.Box = Gtk.Template.Child()
    drop_area_label: Gtk.Label = Gtk.Template.Child()

    _language_changed_handler_id: int | None = None
    _drop_button_handler_id: int | None = None

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)

        self.settings = settings

        self._language_changed_handler_id = self.language_popover.connect("language-changed", self._on_language_changed)

        current_lang_code = self.settings.get_string("active-language")
        self.lang_combo.set_label(
            language_manager.get_language(current_lang_code),
        )

        self._drop_button_handler_id = self.drop_button.connect("clicked", self._on_drop_button_clicked)
        self._setup_drop_target()

    def _setup_drop_target(self) -> None:
        """Configure drop target with DropTargetAsync and explicit text/uri-list.

        We deliberately request only 'text/uri-list' and NOT Gdk.FileList.

        Why: Gtk.DropTarget(Gdk.FileList) in a Flatpak causes GTK to prefer
        'application/vnd.portal.filetransfer'. In VirtualBox guests (where VBoxClient
        --draganddrop intercepts DnD), the portal transfer hangs because xdg-desktop-portal
        is not properly available in non-GNOME (LXDE/XFCE) guests.

        By requesting 'text/uri-list' explicitly, GDK uses the raw Xdnd protocol
        (which PCManFM, Thunar and all standard file managers provide directly)
        and bypasses the portal entirely.

        The stream read is done fully asynchronously (read_bytes_async, NOT read_upto)
        so the GTK main loop is never blocked.
        """
        formats = Gdk.ContentFormats.new(["text/uri-list"])
        self._drop_target = Gtk.DropTargetAsync(
            formats=formats,
            actions=Gdk.DragAction.COPY,
        )
        self._drop_cancellable: Gio.Cancellable | None = None

        # Track internal drop target handlers for cleanup
        self._dnd_drop_handler_id = self._drop_target.connect("drop", self._on_dnd_drop)
        self._dnd_enter_handler_id = self._drop_target.connect("drag-enter", self._on_dnd_enter)
        self._dnd_leave_handler_id = self._drop_target.connect("drag-leave", self._on_dnd_leave)

        self.add_controller(self._drop_target)

    def _on_drop_button_clicked(self, _: Gtk.Button) -> None:
        """Toggle the visibility of the dedicated drop area."""
        try:
            is_visible = self.drop_area.get_visible()
            self.drop_area.set_visible(not is_visible)
            if not is_visible:
                self.drop_button.add_css_class("suggested-action")
            else:
                self.drop_button.remove_css_class("suggested-action")
        except Exception:
            logger.exception("Anura: Failed to handle drop button click")

    def _on_dnd_enter(self, target: Gtk.DropTargetAsync, drop: Gdk.Drop, x: float, y: float) -> Gdk.DragAction:
        """Visual feedback when drag enters the drop area."""
        try:
            self.drop_area.set_visible(True)
            self.drop_area.add_css_class("drag-hover")
            self.welcome.set_description(_("Drop image to extract text"))
        except Exception:
            logger.exception("Anura: Failed to handle DnD enter")
        return Gdk.DragAction.COPY

    def _on_dnd_leave(self, target: Gtk.DropTargetAsync, drop: Gdk.Drop) -> None:
        """Remove visual feedback when drag leaves the drop area."""
        try:
            self.drop_area.remove_css_class("drag-hover")
            # Only hide if it wasn't already visible (user clicked button)
            if not self.drop_button.has_css_class("suggested-action"):
                self.drop_area.set_visible(False)
            self.welcome.set_description(_("Extract text from anywhere"))
        except Exception:
            logger.exception("Anura: Failed to handle DnD leave")

    def _on_dnd_drop(self, target: Gtk.DropTargetAsync, drop: Gdk.Drop, x: float, y: float) -> bool:
        """Handle drop signal. Initiates a fully async stream read.

        We start an async read of text/uri-list and return True immediately so GTK
        does not reject the drop. The actual processing happens in callbacks.
        drop.finish() MUST be called in the final callback (Xdnd protocol requirement).
        """
        self.drop_area.remove_css_class("drag-hover")

        # Cancel any previous in-flight drop
        if self._drop_cancellable:
            self._drop_cancellable.cancel()
        self._drop_cancellable = Gio.Cancellable()

        drop.read_async(
            ["text/uri-list"],
            GLib.PRIORITY_DEFAULT,
            self._drop_cancellable,
            self._on_drop_stream_ready,
            drop,
        )
        return True  # Accept the drop; we will finish() in the final callback

    def _on_drop_stream_ready(
        self,
        source_object: Gdk.Drop,
        result: Gio.AsyncResult,
        drop: Gdk.Drop,
    ) -> None:
        """Called when the Xdnd stream is ready. Starts async byte read.

        source_object is the Gdk.Drop that initiated read_async (not an InputStream).
        We immediately start read_bytes_async — no blocking calls here.
        """
        try:
            input_stream, _mime_type = source_object.read_finish(result)
        except GLib.Error as e:
            logger.error(f"DnD: Failed to open drop stream: {e}")
            drop.finish(Gdk.DragAction.COPY)  # Always finish, even on error
            return

        input_stream.read_bytes_async(
            65536,  # 64 KB — more than enough for any URI list
            GLib.PRIORITY_DEFAULT,
            self._drop_cancellable,
            self._on_drop_bytes_ready,
            (input_stream, drop),
        )

    def _on_drop_bytes_ready(
        self,
        input_stream: Gio.InputStream,
        result: Gio.AsyncResult,
        user_data: tuple,
    ) -> None:
        """Called when bytes are available. Parses URIs and triggers OCR.

        This is the end of the async chain. We call drop.finish() here (required),
        then process the first valid local image path.
        """
        stream, drop = user_data

        try:
            gbytes = stream.read_bytes_finish(result)
        except GLib.Error as e:
            logger.error(f"DnD: Failed to read drop bytes: {e}")
            drop.finish(Gdk.DragAction.COPY)
            return
        finally:
            self._drop_cancellable = None

        # Xdnd protocol: always call finish BEFORE processing
        drop.finish(Gdk.DragAction.COPY)

        raw = gbytes.get_data() if gbytes else None
        if not raw:
            logger.error("DnD: Received empty data from drop stream")
            self._show_error_toast(_("No file data received from drop"))
            return

        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            text = raw.decode("latin-1", errors="replace")

        # Parse text/uri-list: skip comment lines (#) and empty lines
        uris = [line.strip() for line in text.splitlines() if line.strip() and not line.startswith("#")]

        if not uris:
            logger.error("DnD: No valid URIs found in drop data")
            self._show_error_toast(_("No valid file found in drop"))
            return

        # Anura processes one image at a time — take the first URI
        gfile = Gio.File.new_for_uri(uris[0])
        local_path = gfile.get_path()

        if not local_path:
            logger.error(f"DnD: URI has no local path: {uris[0]}")
            self._show_error_toast(_("Only local files can be dropped"))
            return

        if not os.path.exists(local_path):
            logger.error(f"DnD: File not accessible: {local_path}")
            self._show_error_toast(_("File not accessible. Ensure Anura has permission to access this location."))
            return

        (mimetype, _encoding) = guess_type(local_path)
        logger.debug(f"DnD: Dropped file ({mimetype}): {local_path}")

        if not mimetype or not mimetype.startswith("image"):
            self._show_error_toast(_("Only images can be processed that way."))
            return

        window = self.get_root()
        if not window or not hasattr(window, "process_dnd_file_sync"):
            logger.error("DnD: Root window missing process_dnd_file_sync")
            self._show_error_toast(_("Failed to process dropped file"))
            return

        self._set_drop_area_processing_state(True)
        self.show_spinner()
        window.process_dnd_file_sync(local_path)

    def _show_error_toast(self, message: str) -> None:
        """Show error toast to user."""
        window = self.get_root()
        if window and hasattr(window, "show_toast"):
            window.show_toast(message)
        self._set_drop_area_processing_state(False)
        self.hide_spinner()

    def _set_drop_area_processing_state(self, processing: bool) -> None:
        """Set the drop area visual state to indicate processing (OCR in progress)."""
        if processing:
            self.drop_area.add_css_class("drag-processing")
            if self.drop_area_label:
                self.drop_area_label.set_label(_("Processing..."))
        else:
            self.drop_area.remove_css_class("drag-processing")
            if self.drop_area_label:
                self.drop_area_label.set_label(_("Drop image file here"))

    def reset_drop_area_state(self) -> None:
        """Reset the drop area to its initial state (called after OCR completes)."""
        self._set_drop_area_processing_state(False)
        self.hide_spinner()
        self.drop_area.set_visible(False)
        self.drop_button.remove_css_class("suggested-action")
        self.welcome.set_description(_("Extract text from anywhere"))

    def hide_spinner(self) -> None:
        """Stop and hide the spinner."""
        self.spinner.stop()
        self.spinner.set_visible(False)

    def show_spinner(self) -> None:
        """Start and show the spinner."""
        self.spinner.set_visible(True)
        self.spinner.start()

    def _on_language_changed(self, _: LanguagePopover, language: LanguageItem) -> None:
        self.lang_combo.set_label(language.title)
        self.settings.set_string("active-language", language.code)

    def do_destroy(self) -> None:
        """Clean up signal handlers to prevent memory leaks."""
        if self._language_changed_handler_id is not None:
            with contextlib.suppress(Exception):
                self.language_popover.disconnect(self._language_changed_handler_id)
            self._language_changed_handler_id = None

        if self._drop_button_handler_id is not None:
            with contextlib.suppress(Exception):
                self.drop_button.disconnect(self._drop_button_handler_id)
            self._drop_button_handler_id = None

        # Disconnect any other signals that might have been connected manually

        # Cancel any in-flight drop operation
        drop_cancellable = getattr(self, "_drop_cancellable", None)
        if drop_cancellable:
            drop_cancellable.cancel()
            self._drop_cancellable = None

        # Remove drop target controller and disconnect its internal handlers
        if hasattr(self, "_drop_target") and self._drop_target:
            with contextlib.suppress(Exception):
                if hasattr(self, "_dnd_drop_handler_id") and self._dnd_drop_handler_id:
                    self._drop_target.disconnect(self._dnd_drop_handler_id)
                if hasattr(self, "_dnd_enter_handler_id") and self._dnd_enter_handler_id:
                    self._drop_target.disconnect(self._dnd_enter_handler_id)
                if hasattr(self, "_dnd_leave_handler_id") and self._dnd_leave_handler_id:
                    self._drop_target.disconnect(self._dnd_leave_handler_id)

            self.remove_controller(self._drop_target)
            self._drop_target = None

        super().do_destroy()
