# welcome_page.py
#
# Copyright 2021-2025 Andrey Maksimov
# Copyright 2026 D3M-Sudo (Anura fork and modifications)

import contextlib
from mimetypes import guess_type
import os

from gi.repository import Adw, Gdk, Gio, Gtk
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

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)

        self.settings = settings

        self._language_changed_handler_id = self.language_popover.connect("language-changed", self._on_language_changed)

        current_lang_code = self.settings.get_string("active-language")
        self.lang_combo.set_label(
            language_manager.get_language(current_lang_code),
        )

        self.drop_button.connect("clicked", self._on_drop_button_clicked)
        self._setup_drop_target()

    def _setup_drop_target(self) -> None:
        """Configure the drop target using Gtk.DropTarget with Gdk.FileList.

        This uses the GTK4 high-level API which handles the X11 Xdnd protocol
        internally and delivers data only after complete transfer — preventing
        the blocking stream read freeze on non-GNOME desktops (XFCE, LXDE, etc).

        Gdk.FileList covers: text/uri-list, libfm/files, x-special/gnome-icon-list
        and other file list formats used by various file managers.
        """
        self._drop_target = Gtk.DropTarget.new(Gdk.FileList, Gdk.DragAction.COPY)
        self._drop_target.connect("drop", self._on_dnd_drop)
        self._drop_target.connect("enter", self._on_dnd_enter)
        self._drop_target.connect("leave", self._on_dnd_leave)
        self.drop_area.add_controller(self._drop_target)

    def _on_drop_button_clicked(self, _: Gtk.Button) -> None:
        """Toggle the visibility of the dedicated drop area."""
        is_visible = self.drop_area.get_visible()
        self.drop_area.set_visible(not is_visible)
        if not is_visible:
            self.drop_button.add_css_class("suggested-action")
        else:
            self.drop_button.remove_css_class("suggested-action")

    def _on_dnd_enter(self, target: Gtk.DropTarget, x: float, y: float) -> Gdk.DragAction:
        """Visual feedback when drag enters the drop area."""
        self.drop_area.add_css_class("drag-hover")
        return Gdk.DragAction.COPY

    def _on_dnd_leave(self, target: Gtk.DropTarget) -> None:
        """Remove visual feedback when drag leaves the drop area."""
        self.drop_area.remove_css_class("drag-hover")

    def _on_dnd_drop(self, target: Gtk.DropTarget, value: Gdk.FileList, x: float, y: float) -> bool:
        """Handle drop event. GTK has already fully transferred the data at this point.

        Called only after complete data transfer — no blocking I/O on main thread.
        value is a Gdk.FileList containing Gio.File objects.
        """
        from gettext import gettext as _

        self.drop_area.remove_css_class("drag-hover")

        files = value.get_files()
        if not files:
            logger.error("DnD: Empty file list received")
            self._show_error_toast(_("No valid file found in drop"))
            return False

        # Take the first file only (Anura processes one image at a time)
        gfile: Gio.File = files[0]
        local_path = gfile.get_path()

        if not local_path:
            logger.error("DnD: File has no local path (non-local URI?)")
            self._show_error_toast(_("Only local files can be dropped"))
            return False

        if not os.path.exists(local_path):
            logger.error(f"DnD: File not accessible (Flatpak permission): {local_path}")
            self._show_error_toast(_("File not accessible. Ensure Anura has permission to access this location."))
            return False

        # Validate MIME type
        (mimetype, _encoding) = guess_type(local_path)
        logger.debug(f"DnD: Dropped file ({mimetype}): {local_path}")

        if not mimetype or not mimetype.startswith("image"):
            self._show_error_toast(_("Only images can be processed that way."))
            return False

        # Resolve window reference
        window = self.get_root()
        if not window or not hasattr(window, "process_dnd_file_sync"):
            logger.error("DnD: Root window missing or missing process_dnd_file_sync")
            self._show_error_toast(_("Failed to process dropped file"))
            return False

        # Set processing state and start OCR
        self._set_drop_area_processing_state(True)
        self.show_spinner()
        window.process_dnd_file_sync(local_path)

        return True

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

        super().do_destroy()
