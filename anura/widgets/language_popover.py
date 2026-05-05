# language_popover.py
#
# Copyright 2021-2025 Andrey Maksimov
# Copyright 2026 D3M-Sudo (Anura fork and modifications)

from typing import ClassVar

from gi.repository import Gio, GObject, Gtk
from loguru import logger

from anura.config import RESOURCE_PREFIX
from anura.language_manager import language_manager
from anura.services.settings import settings
from anura.types.language_item import LanguageItem
from anura.utils.signal_manager import SignalManagerMixin
from anura.widgets.language_popover_row import LanguagePopoverRow


@Gtk.Template(resource_path=f"{RESOURCE_PREFIX}/language_popover.ui")
class LanguagePopover(Gtk.Popover, SignalManagerMixin):
    __gtype_name__ = "LanguagePopover"

    __gsignals__: ClassVar[dict[str, tuple]] = {
        'language-changed': (GObject.SIGNAL_RUN_LAST, None, (LanguageItem,)),
    }

    views: Gtk.Stack = Gtk.Template.Child()
    search_box: Gtk.Box = Gtk.Template.Child()
    entry: Gtk.SearchEntry = Gtk.Template.Child()
    list_view: Gtk.ListBox = Gtk.Template.Child()

    lang_list: Gio.ListStore = Gio.ListStore(item_type=LanguageItem)
    filter_list: Gtk.FilterListModel
    filter: Gtk.CustomFilter

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        SignalManagerMixin.__init__(self)

        self.settings = settings

        self.connect_tracked(language_manager, "downloaded", self._on_language_downloaded)
        self.connect_tracked(language_manager, "removed", self._on_language_removed)

        self._active_language = self.settings.get_string('active-language')

        self.bind_model()

    def bind_model(self):
        self.filter = Gtk.CustomFilter()
        self.filter.set_filter_func(self._on_language_filter)
        self.filter_list = Gtk.FilterListModel.new(self.lang_list, self.filter)
        self.list_view.bind_model(self.filter_list, LanguagePopoverRow)

    @GObject.Property(type=str)
    def active_language(self):
        return self._active_language

    @active_language.setter
    def active_language(self, lang_code: str):
        self._active_language = lang_code

    def _on_language_filter(self, proposal: LanguageItem, text: str | None = None) -> bool:
        if not text:
            return True
        return text.lower() in proposal.title.lower()

    def _on_language_downloaded(self, _sender: GObject.GObject, _lang_code: str) -> None:
        self.populate_model()

    def _on_language_removed(self, _sender: GObject.GObject, _lang_code: str) -> None:
        self.populate_model()

    @Gtk.Template.Callback()
    def _on_search_activate(self, entry: Gtk.SearchEntry):
        if self.filter_list.get_n_items() > 0:
            first_row = self.list_view.get_row_at_index(0)
            if first_row:
                self._on_language_activate(self.list_view, first_row)

    @Gtk.Template.Callback()
    def _on_language_activate(self, _: Gtk.ListBox, row: LanguagePopoverRow):
        item: LanguageItem = row.lang
        self.emit('language-changed', item)
        self.active_language = item.code
        language_manager.active_language = item


        self.settings.set_string('active-language', item.code)
        logger.debug(f"Anura: OCR language changed to '{item.code}'")
        self.popdown()

    @Gtk.Template.Callback()
    def _on_search_changed(self, entry: Gtk.SearchEntry):
        query = entry.get_text().strip()
        self.filter.set_filter_func(self._on_language_filter, query)
        self.toggle_empty_state(not self.filter_list.get_n_items())

    @Gtk.Template.Callback()
    def _on_stop_search(self, _entry: Gtk.SearchEntry):
        self.popdown()

    @Gtk.Template.Callback()
    def _on_popover_show(self, _):
        self.populate_model()

    @Gtk.Template.Callback()
    def _on_popover_closed(self, *_):
        self.entry.set_text('')

    @Gtk.Template.Callback()
    def _on_add_clicked(self, _: Gtk.Widget):
        self.activate_action('app.preferences')
        self.popdown()

    def populate_model(self) -> None:
        self.lang_list.remove_all()

        downloaded_languages = language_manager.get_downloaded_languages(force=True)
        for lang in downloaded_languages:
            code = language_manager.get_language_code(lang)
            selected = (self.active_language == code)
            self.lang_list.append(LanguageItem(code=code, title=lang, selected=selected))

        # Fallback to English if current language was removed, emitting only on actual change
        current_code = self.active_language
        if current_code not in language_manager.get_downloaded_codes():
            new_item = language_manager.get_language_item("eng")
            if new_item and self.active_language != "eng":  # emit only if language actually changed
                self.active_language = "eng"
                self.settings.set_string('active-language', 'eng')
                self.emit("language-changed", new_item)

    def toggle_empty_state(self, is_empty: bool = False) -> None:
        if is_empty:
            self.views.set_visible_child_name('empty_page')
        else:
            self.views.set_visible_child_name('languages_page')

    def do_destroy(self):
        """Clean up all tracked signal handlers to prevent memory leaks."""
        self.disconnect_all_signals()
        super().do_destroy()
