# welcome_page.py
#
# Copyright 2021-2025 Andrey Maksimov
# Copyright 2026 D3M-Sudo (Anura fork and modifications)

import contextlib

from gi.repository import Adw, Gdk, GLib, Gtk

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
        drop_target = Gtk.DropTarget.new(type=Gdk.FileList, actions=Gdk.DragAction.COPY)
        drop_target.connect("enter", self._on_dnd_enter)
        drop_target.connect("leave", self._on_dnd_leave)
        drop_target.connect("drop", self._on_dnd_drop)
        self.drop_area.add_controller(drop_target)

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

    def _on_dnd_drop(self, _target: Gtk.DropTarget, value: Gdk.FileList, _x: float, _y: float) -> bool:
        self.drop_area.remove_css_class("drag-hover")
        if not value or not isinstance(value, Gdk.FileList):
            return False

        files = value.get_files()
        if not files:
            return False

        # Resolve window reference before scheduling async work
        window = self.get_root()
        if not (window and hasattr(window, "process_gfile")):
            return False

        # Defer processing to next iteration of the main loop to avoid
        # Gtk-CRITICAL deadlock in the drag-and-drop signal handler.
        from gi.repository import GLib

        GLib.idle_add(window.process_gfile, files[0])
        return True

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
