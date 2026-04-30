# language_row.py
#
# Copyright 2021-2025 Andrey Maksimov
# Copyright 2026 D3M-Sudo (Anura fork and modifications)

from gi.repository import GLib, GObject, Gtk

from anura.config import RESOURCE_PREFIX
from anura.language_manager import language_manager
from anura.types.language_item import LanguageItem


@Gtk.Template(resource_path=f"{RESOURCE_PREFIX}/language_row.ui")
class LanguageRow(Gtk.Overlay):
    __gtype_name__ = "LanguageRow"

    label: Gtk.Label = Gtk.Template.Child()
    install_btn: Gtk.Button = Gtk.Template.Child()
    remove_btn: Gtk.Button = Gtk.Template.Child()
    progress_bar: Gtk.ProgressBar = Gtk.Template.Child()
    revealer: Gtk.Revealer = Gtk.Template.Child()

    _item: LanguageItem | None = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Connect language manager signals for download updates
        language_manager.connect("downloading", self.update_progress)
        language_manager.connect("downloaded", self.on_downloaded)

        # Deferred UI update to ensure item is set
        GLib.idle_add(self.update_ui)

    @GObject.Property(type=GObject.TYPE_PYOBJECT)
    def item(self) -> LanguageItem | None:
        return self._item

    @item.setter
    def item(self, item: LanguageItem):
        self._item = item
        self.label.set_label(self._item.title)

    def update_ui(self):
        """
        Updates the visibility and sensitivity of control buttons
        based on the language installation status.
        """
        if not self._item:
            return

        # English is the core language and cannot be removed
        if self._item.code == "eng":
            self.install_btn.set_visible(False)
            self.remove_btn.set_sensitive(False)
            return

        # Handle button states based on installation/download status
        is_installed = self._item.code in language_manager.get_downloaded_codes()
        is_loading = self._item.code in language_manager.loading_languages

        self.remove_btn.set_visible(is_installed)
        self.install_btn.set_visible(not is_installed)
        self.install_btn.set_sensitive(not is_loading)

        if not is_loading:
            self.revealer.set_reveal_child(False)

    def update_progress(self, sender, code: str, progress: float) -> None:
        """
        Signal handler for download progress.
        """
        if self._item and code == self._item.code:
            GLib.idle_add(self.late_update, code, progress)

    def late_update(self, code, progress):
        """
        Updates the progress bar on the main thread.
        """
        if self._item and self._item.code == code:
            if not self.revealer.get_reveal_child():
                self.revealer.set_reveal_child(True)

            self.progress_bar.set_fraction(progress / 100)

            if progress >= 100:
                self.revealer.set_reveal_child(False)

    @Gtk.Template.Callback()
    def _on_download(self, _: Gtk.Button):
        """
        Triggered when the install button is clicked.
        """
        if self._item.code in language_manager.loading_languages:
            return

        language_manager.download(self._item.code)
        self.update_ui()

    @Gtk.Template.Callback()
    def _on_remove(self, _: Gtk.Button):
        """
        Triggered when the remove button is clicked.
        """
        if self._item.code in language_manager.loading_languages:
            return

        if self._item.code in language_manager.get_downloaded_codes():
            language_manager.remove_language(self._item.code)
            self.update_ui()

    def on_downloaded(self, sender, code):
        """
        Signal handler for completed downloads.
        """
        if self._item and self._item.code == code:
            GLib.idle_add(self.update_ui)
