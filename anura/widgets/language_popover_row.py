# language_popover_row.py
#
# Copyright 2021-2025 Andrey Maksimov
# Copyright 2026 D3M-Sudo (Anura fork and modifications)
#
# MIT License

from gi.repository import Gtk, GObject

from anura.config import RESOURCE_PREFIX
from anura.types.language_item import LanguageItem


@Gtk.Template(resource_path=f"{RESOURCE_PREFIX}/ui/language_popover_row.ui")
class LanguagePopoverRow(Gtk.ListBoxRow):
    __gtype_name__ = 'LanguagePopoverRow'

    lang: LanguageItem

    # Widgets
    title: Gtk.Label = Gtk.Template.Child()
    selection: Gtk.Image = Gtk.Template.Child()

    def __init__(self, lang: LanguageItem):
        super().__init__()
        self.lang = lang
        self.title.set_label(self.lang.title)

        self.lang.bind_property(
            'selected',
            self.selection,
            'visible',
            GObject.BindingFlags.SYNC_CREATE
        )
