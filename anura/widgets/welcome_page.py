# welcome_page.py
#
# Copyright 2021-2025 Andrey Maksimov
# Copyright 2026 D3M-Sudo (Anura fork and modifications)

import contextlib
from mimetypes import guess_type

from gi.repository import Adw, Gdk, Gtk
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
        """Configure the drop target for the dedicated drop area."""
        # Use a persistent controller to avoid Gtk-CRITICAL assertions on X11/Lubuntu
        self._drop_target = Gtk.DropTarget.new(type=Gdk.FileList, actions=Gdk.DragAction.COPY)
        self._drop_target.connect("enter", self._on_dnd_enter)
        self._drop_target.connect("leave", self._on_dnd_leave)
        self._drop_target.connect("drop", self._on_dnd_drop)
        self.drop_area.add_controller(self._drop_target)

    def _on_drop_button_clicked(self, _: Gtk.Button) -> None:
        """Toggle the visibility of the dedicated drop area."""
        is_visible = self.drop_area.get_visible()
        self.drop_area.set_visible(not is_visible)
        if not is_visible:
            self.drop_button.add_css_class("suggested-action")
        else:
            self.drop_button.remove_css_class("suggested-action")

    def _on_dnd_enter(self, _target: Gtk.DropTarget, _x: float, _y: float) -> Gdk.DragAction:
        self.drop_area.add_css_class("drag-hover")
        return Gdk.DragAction.COPY

    def _on_dnd_leave(self, _target: Gtk.DropTarget) -> None:
        self.drop_area.remove_css_class("drag-hover")

    def _on_dnd_drop(self, target: Gtk.DropTarget, value: Gdk.FileList, _x: float, _y: float, drop: Gdk.Drop) -> bool:
        """Handle drop event following Frog's simple sync pattern."""
        from gettext import gettext as _

        self.drop_area.remove_css_class("drag-hover")

        try:
            files = value.get_files()
            if not files:
                logger.debug("DnD: Drop file list is empty")
                return False

            item = files[0]
            file_path = item.get_path()
            (mimetype, _encoding) = guess_type(file_path)
            logger.debug(f"Dropped item ({mimetype}): {file_path}")

            if not mimetype or not mimetype.startswith("image"):
                window = self.get_root()
                if window and hasattr(window, "show_toast"):
                    window.show_toast(_("Only images can be processed that way."))
                return False

            # Resolve window reference
            window = self.get_root()
            if not window:
                logger.error("DnD: Root window is None")
                return False

            if not hasattr(window, "process_dnd_file_sync"):
                logger.error(f"DnD: Root window {window} missing process_dnd_file_sync method")
                return False

            # Set processing state before starting OCR
            self._set_drop_area_processing_state(True)
            self.spinner.set_visible(True)

            # Process synchronously following Frog's pattern
            window.process_dnd_file_sync(file_path)

        except Exception as e:
            logger.error(f"DnD: Error during drop processing: {e}")
            self._set_drop_area_processing_state(False)
            self.spinner.set_visible(False)
            return False

        return True

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
        self.drop_area.set_visible(False)
        self.drop_button.remove_css_class("suggested-action")

    def _on_language_changed(self, _: LanguagePopover, language: LanguageItem) -> None:
        self.lang_combo.set_label(language.title)
        self.settings.set_string("active-language", language.code)

    def do_destroy(self) -> None:
        """Clean up signal handlers to prevent memory leaks."""
        if self._language_changed_handler_id is not None:
            with contextlib.suppress(Exception):
                self.language_popover.disconnect(self._language_changed_handler_id)
            self._language_changed_handler_id = None
        super().do_destroy()
