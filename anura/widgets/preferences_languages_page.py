# preferences_languages_page.py
#
# Copyright 2021-2025 Andrey Maksimov
# Copyright 2026 D3M-Sudo (Anura fork and modifications)

from gettext import gettext as _

from gi.repository import Adw, Gio, Gtk

from anura.config import RESOURCE_PREFIX
from anura.language_manager import language_manager
from anura.services.settings import settings
from anura.types.language_item import LanguageItem
from anura.utils.signal_manager import SignalManagerMixin
from anura.widgets.language_row import LanguageRow


@Gtk.Template(resource_path=f"{RESOURCE_PREFIX}/preferences_languages.ui")
class PreferencesLanguagesPage(Adw.PreferencesPage, SignalManagerMixin):
    __gtype_name__ = 'PreferencesLanguagesPage'

    banner: Adw.Banner = Gtk.Template.Child()
    views: Gtk.Stack = Gtk.Template.Child()
    search_bar: Gtk.SearchBar = Gtk.Template.Child()
    language_search_entry: Gtk.SearchEntry = Gtk.Template.Child()
    list_view: Gtk.ListView = Gtk.Template.Child()
    model: Gtk.FilterListModel = Gtk.Template.Child()
    list_store: Gio.ListStore = Gtk.Template.Child()
    revealer: Gtk.Revealer = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        SignalManagerMixin.__init__(self)

        self.settings = settings

        # Dynamic language store initialization - use centralized get_language_item pattern
        for lang_code in language_manager.get_available_codes():
            item = language_manager.get_language_item(lang_code)
            if item is not None:
                self.list_store.append(item)

        # Signals for dynamic model updates (tracked for automatic cleanup)
        self.connect_tracked(language_manager, 'added', self.on_language_added)
        self.connect_tracked(language_manager, 'downloaded', self.on_language_added)
        self.connect_tracked(language_manager, 'removed', self.on_language_removed)

        # UI signal connections (tracked for automatic cleanup)
        self.connect_tracked(self.language_search_entry, 'search-changed', self.on_language_search)
        self.connect_tracked(self.language_search_entry, 'stop-search', self.on_language_search_stop)
        self.connect_tracked(self.search_bar, 'notify::search-mode-enabled', self.on_search_mode_enabled)

        self.load_languages()
        self.activate_filter()
        self.check_connection()

    def check_connection(self) -> None:
        """Asynchronously checks network reachability for OCR model downloads."""
        monitor = Gio.NetworkMonitor.get_default()
        address = Gio.NetworkAddress.new("google.com", 443)
        monitor.can_reach_async(address, None, self._on_connection_checked)

    def _on_connection_checked(self, monitor, result) -> None:
        try:
            reachable = monitor.can_reach_finish(result)
        except Exception:
            reachable = False

        if not reachable:
            self.banner.set_title(_("OCR models unreachable. Please check your internet connection."))
            self.banner.set_revealed(True)
            return

        if monitor.get_network_metered():
            self.banner.set_title(_("Metered connection detected. Model downloads may incur data costs."))
            self.banner.set_revealed(True)
            return

        self.banner.set_revealed(False)

    @Gtk.Template.Callback()
    def _on_banner_clicked(self, _):
        self.check_connection()

    @Gtk.Template.Callback()
    def _on_item_setup(self, factory: Gtk.SignalListItemFactory, item: Gtk.ListItem):
        item.set_child(LanguageRow())

    @Gtk.Template.Callback()
    def _on_item_bind(self, factory: Gtk.SignalListItemFactory, list_item: Gtk.ListItem):
        row: LanguageRow = list_item.get_child()
        item: LanguageItem = list_item.get_item()
        row.item = item

    @Gtk.Template.Callback()
    def _on_add_language(self, sender: Gtk.Widget):
        if not self.is_search_mode:
            self.deactivate_filter()
            self.search_bar.set_search_mode(True)
            self.language_search_entry.grab_focus()
        else:
            self.activate_filter()
            self.search_bar.set_search_mode(False)

    def load_languages(self):
        self.list_store.remove_all()
        existing_codes = set()
        for lang_code in language_manager.get_available_codes():
            item = language_manager.get_language_item(lang_code)
            if item is not None and item.code not in existing_codes:
                self.list_store.append(item)
                existing_codes.add(item.code)

    @property
    def is_search_mode(self):
        return self.search_bar.get_search_mode()

    def activate_filter(self, search_text: str | None = None) -> None:
        _filter = Gtk.CustomFilter.new(PreferencesLanguagesPage.filter_func, search_text)
        self.model.set_filter(_filter)
        self.toggle_empty_state(not self.model.get_n_items())

    def deactivate_filter(self):
        self.model.set_filter(None)

    def on_language_search(self, entry: Gtk.SearchEntry, _user_data=None) -> None:
        self.activate_filter(entry.get_text())

    def on_language_search_stop(self, entry: Gtk.SearchEntry) -> None:
        entry.set_text('')
        self.search_bar.set_search_mode(False)
        self.revealer.set_reveal_child(True)
        self.activate_filter()

    def on_search_mode_enabled(self, _searchbar, _enabled: bool) -> None:
        if not self.search_bar.get_search_mode():
            self.activate_filter()

    @staticmethod
    def filter_func(item, user_data: str) -> bool:
        if user_data:
            return user_data.lower() in item.title.lower()
        return item.code in language_manager.get_downloaded_codes()

    def on_language_added(self, _sender, code: str | None = None) -> None:
        # Idempotent: only add if not already in the list
        if code is not None:
            existing_codes = {item.code for item in self.list_store}
            if code not in existing_codes:
                item = language_manager.get_language_item(code)
                if item is not None:
                    self.list_store.append(item)
        if not self.search_bar.get_search_mode():
            self.activate_filter()

    def on_language_removed(self, _sender, _code) -> None:
        if not self.search_bar.get_search_mode():
            self.activate_filter()

    def toggle_empty_state(self, is_empty: bool = False) -> None:
        state = 'empty_state' if is_empty else 'languages_state'
        self.views.set_visible_child_name(state)

    def do_destroy(self):
        """Clean up all tracked signal handlers to prevent memory leaks."""
        self.disconnect_all_signals()
        super().do_destroy()
