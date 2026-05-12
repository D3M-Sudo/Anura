# welcome_page.py
#
# Copyright 2021-2025 Andrey Maksimov
# Copyright 2026 D3M-Sudo (Anura fork and modifications)

import contextlib

from gi.repository import Adw, Gdk, Gtk

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
        from loguru import logger

        self.drop_area.remove_css_class("drag-hover")

        # X11 Constraint: Always finish the drop transaction immediately to prevent cursor hang
        drop_success = False

        try:
            if not value:
                logger.debug("DnD: Drop value is None")
                drop.finish(0, False)
                return False

            if not isinstance(value, Gdk.FileList):
                logger.debug(f"DnD: Drop value has unexpected type: {type(value)}")
                drop.finish(0, False)
                return False

            files = value.get_files()
            if not files:
                logger.debug("DnD: Drop file list is empty")
                drop.finish(0, False)
                return False

            # Resolve window reference before scheduling async work
            window = self.get_root()
            if not (window and hasattr(window, "process_gfile")):
                logger.debug(f"DnD: Root window not found or missing process_gfile (root={window})")
                drop.finish(0, False)
                return False

            # Defer processing to next iteration of the main loop to avoid
            # Gtk-CRITICAL deadlock in the drag-and-drop signal handler.
            from gi.repository import GLib

            logger.debug(f"DnD: Scheduling process_gfile for {files[0].get_path()}")
            # Schedule the file processing
            GLib.idle_add(window.process_gfile, files[0])
            GLib.idle_add(self._reset_drop_target, target)
            drop_success = True

        except Exception as e:
            logger.error(f"DnD: Error during drop processing: {e}")
            drop_success = False
        finally:
            # X11 Constraint: Always finish the drop transaction immediately
            drop.finish(Gdk.DragAction.COPY if drop_success else 0, drop_success)

        return drop_success

    def _reset_drop_target(self, target: Gtk.DropTarget) -> bool:
        """Reset the drop target to clear its state."""
        from gi.repository import GLib

        self.drop_area.remove_controller(target)
        self._setup_drop_target()
        return GLib.SOURCE_REMOVE

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
