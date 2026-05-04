# list_menu_row.py
#
# Copyright 2021-2025 Andrey Maksimov
# Copyright 2026 D3M-Sudo (Anura fork and modifications)
#
# MIT License

from gi.repository import GObject, Gtk

from anura.types.language_item import LanguageItem


class ListMenuRow(Gtk.Label):
    __gtype_name__ = 'ListMenuRow'

    _item: LanguageItem | None

    def __init__(self, item: LanguageItem):
        super().__init__()

        self.item = item

    @GObject.Property(type=GObject.TYPE_PYOBJECT)
    def item(self) -> LanguageItem:
        return self._item

    @item.setter
    def item(self, item: LanguageItem):
        self._item = item

        self.set_label(item.title)
        self.set_halign(Gtk.Align.START)

