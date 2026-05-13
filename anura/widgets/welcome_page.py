# welcome_page.py
#
# Copyright 2021-2025 Andrey Maksimov
# Copyright 2026 D3M-Sudo (Anura fork and modifications)

import contextlib
from mimetypes import guess_type
import os
import threading

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

    # DnD async operation management
    _dnd_cancellable: Gio.Cancellable | None = None
    _dnd_timeout_id: int | None = None
    _dnd_lock: threading.Lock

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)

        self.settings = settings
        self._dnd_lock = threading.Lock()

        self._language_changed_handler_id = self.language_popover.connect("language-changed", self._on_language_changed)

        current_lang_code = self.settings.get_string("active-language")
        self.lang_combo.set_label(
            language_manager.get_language(current_lang_code),
        )

        self.drop_button.connect("clicked", self._on_drop_button_clicked)
        self._setup_drop_target()

    def _setup_drop_target(self) -> None:
        """Configure the drop target for the dedicated drop area using DropTargetAsync."""
        # Use DropTargetAsync to bypass XDG portal on X11/Flatpak (GTK bugs #4562, #3755, #6769)
        # This prevents gtk_drop_target_handle_event assertion failures and freezes
        # NOTE: Gtk.DropTargetAsync.new() requires (formats, actions) in GTK 4.0+
        formats = Gdk.ContentFormats.new(["text/uri-list"])
        self._drop_target = Gtk.DropTargetAsync.new(formats, Gdk.DragAction.COPY)
        self._drop_target.connect("drop", self._on_dnd_drop_async)
        self.drop_area.add_controller(self._drop_target)

    def _on_drop_button_clicked(self, _: Gtk.Button) -> None:
        """Toggle the visibility of the dedicated drop area."""
        is_visible = self.drop_area.get_visible()
        self.drop_area.set_visible(not is_visible)
        if not is_visible:
            self.drop_button.add_css_class("suggested-action")
        else:
            self.drop_button.remove_css_class("suggested-action")

    def _on_dnd_drop_async(self, target: Gtk.DropTargetAsync, drop: Gdk.Drop, _x: float, _y: float) -> bool:
        """Handle drop event using DropTargetAsync to bypass XDG portal."""
        # Remove hover state immediately
        self.drop_area.remove_css_class("drag-hover")

        # Check if text/uri-list is available
        formats = drop.get_formats()
        if not formats.contain_mime_type("text/uri-list"):
            logger.debug("DnD: text/uri-list not available in drop formats")
            return False

        # Set up cancellable for async operation
        with self._dnd_lock:
            # Cancel any previous DnD operation
            if self._dnd_cancellable is not None:
                self._dnd_cancellable.cancel()
            # Clear previous timeout
            if self._dnd_timeout_id is not None and self._dnd_timeout_id > 0:
                GLib.source_remove(self._dnd_timeout_id)
                self._dnd_timeout_id = None

            # Create new cancellable
            self._dnd_cancellable = Gio.Cancellable()
            cancellable = self._dnd_cancellable

            # Set 30s safety timeout (fail-fast vs 25s D-Bus timeout)
            self._dnd_timeout_id = GLib.timeout_add_seconds(
                30,
                self._on_dnd_timeout,
                cancellable
            )

        # Read the URI list asynchronously using Gio.InputStream (NOT read_value_async - causes SIGABRT in Python)
        drop.read_async(
            ["text/uri-list"],
            GLib.PRIORITY_DEFAULT,
            cancellable,
            self._on_drop_read_ready
        )

        return True  # Accept the drop immediately

    def _on_drop_read_ready(self, drop: Gdk.Drop, result: Gio.AsyncResult) -> None:
        """Callback for reading URI list from drop using DataInputStream."""
        from gettext import gettext as _

        # Clear timeout
        with self._dnd_lock:
            if self._dnd_timeout_id is not None and self._dnd_timeout_id > 0:
                GLib.source_remove(self._dnd_timeout_id)
                self._dnd_timeout_id = None

        try:
            # Get input stream from drop
            input_stream, _mime_type = drop.read_finish(result)
            if input_stream is None:
                logger.error("DnD: Failed to get input stream from drop")
                self._show_error_toast(_("Failed to read dropped file"))
                return

            # Use DataInputStream for safe reading (avoids SIGABRT from read_value_async in Python)
            data_stream = Gio.DataInputStream.new(input_stream)

            # Read stream content (read until null terminator or EOF)
            content_bytes, _ = data_stream.read_upto("\0", 1, None)

            if not content_bytes:
                logger.error("DnD: Empty content from drop stream")
                self._show_error_toast(_("Failed to read dropped file"))
                return

            # Decode URI list (RFC 2483 format)
            uri_string = content_bytes.decode('utf-8', errors='replace').strip()

            # Parse URI list manually (RFC 2483: CRLF separated, # comments)
            uris = []
            for line in uri_string.splitlines():
                line = line.strip()
                if line and not line.startswith('#'):
                    uris.append(line)

            if not uris:
                logger.error("DnD: No valid URIs found in drop")
                self._show_error_toast(_("No valid file found in drop"))
                return

            # Get first file URI
            file_uri = uris[0]
            if not file_uri.startswith("file://"):
                logger.error(f"DnD: Non-file URI: {file_uri}")
                self._show_error_toast(_("Only local files can be dropped"))
                return

            # Convert file:// URI to local path
            try:
                local_path, _hostname = GLib.filename_from_uri(file_uri)
            except GLib.Error as e:
                logger.error(f"DnD: Failed to convert URI to path: {e.message}")
                self._show_error_toast(_("Failed to process dropped file"))
                return

            # Check if file exists and is accessible (Flatpak permission check)
            if not os.path.exists(local_path):
                logger.error(f"DnD: File not accessible (Flatpak permission): {local_path}")
                self._show_error_toast(
                    _("File not accessible. Ensure Anura has permission to access this location.")
                )
                return

            # Validate MIME type
            (mimetype, _encoding) = guess_type(local_path)
            logger.debug(f"DnD: Dropped file ({mimetype}): {local_path}")

            if not mimetype or not mimetype.startswith("image"):
                self._show_error_toast(_("Only images can be processed that way."))
                return

            # Resolve window reference
            window = self.get_root()
            if not window:
                logger.error("DnD: Root window is None")
                self._show_error_toast(_("Failed to process dropped file"))
                return

            if not hasattr(window, "process_dnd_file_sync"):
                logger.error(f"DnD: Root window {window} missing process_dnd_file_sync method")
                self._show_error_toast(_("Failed to process dropped file"))
                return

            # Set processing state before starting OCR
            self._set_drop_area_processing_state(True)
            self.show_spinner()

            # Process file synchronously (path is already validated and accessible)
            window.process_dnd_file_sync(local_path)

        except GLib.Error as e:
            if e.matches(Gio.io_error_quark(), Gio.IOErrorEnum.CANCELLED):
                logger.debug("DnD: Operation cancelled")
                return
            logger.error(f"DnD: Error reading drop: {e.message}")
            self._show_error_toast(_("Failed to read dropped file"))
        except Exception as e:
            logger.error(f"DnD: Unexpected error in drop processing: {e}")
            self._show_error_toast(_("Failed to process dropped file"))
        finally:
            # Clean up cancellable
            with self._dnd_lock:
                self._dnd_cancellable = None

    def _on_dnd_timeout(self, cancellable: Gio.Cancellable) -> bool:
        """Handle DnD timeout (30s safety)."""
        logger.warning("DnD: Operation timed out after 30s")
        with self._dnd_lock:
            if self._dnd_cancellable is not None:
                self._dnd_cancellable.cancel()
            self._dnd_cancellable = None
            self._dnd_timeout_id = None
        self._set_drop_area_processing_state(False)
        self.hide_spinner()
        return False  # Don't repeat timeout

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
                from gettext import gettext as _
                self.drop_area_label.set_label(_("Processing..."))
        else:
            self.drop_area.remove_css_class("drag-processing")
            if self.drop_area_label:
                from gettext import gettext as _
                self.drop_area_label.set_label(_("Drop image file here"))

    def reset_drop_area_state(self) -> None:
        """Reset the drop area to its initial state (called after OCR completes)."""
        self._set_drop_area_processing_state(False)
        self.hide_spinner()
        self.drop_area.set_visible(False)
        self.drop_button.remove_css_class("suggested-action")

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
        # Clean up drop target controller
        if hasattr(self, "_drop_target") and self._drop_target:
            self.drop_area.remove_controller(self._drop_target)
            self._drop_target = None
        # Clean up DnD async resources
        with self._dnd_lock:
            if self._dnd_cancellable is not None:
                self._dnd_cancellable.cancel()
                self._dnd_cancellable = None
            if self._dnd_timeout_id is not None and self._dnd_timeout_id > 0:
                GLib.source_remove(self._dnd_timeout_id)
                self._dnd_timeout_id = None
        super().do_destroy()
