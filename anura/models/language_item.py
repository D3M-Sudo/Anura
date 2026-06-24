# This file is part of Anura.
# Copyright (C) 2022-2025 Andrey Maksimov (Frog)
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

from gi.repository import GObject


class LanguageItem(GObject.GObject):
    """
    Represent a language item in the OCR language list.
    Designed for use with Gio.ListStore and Gtk.ListView/ListBox.
    """

    __gtype_name__ = "LanguageItem"

    # Properties definition for GTK/GObject Data Binding
    title = GObject.Property(type=str)
    code = GObject.Property(type=str)
    selected = GObject.Property(type=bool, default=False)

    def __init__(self, code: str, title: str, selected: bool = False) -> None:
        """
        Initialize a new LanguageItem.

        Args:
            code (str): ISO 639-2/T language code (e.g., 'eng', 'ita').
            title (str): Human-readable language name.
            selected (bool): Whether this language is currently active.
        """
        super().__init__()
        self.title = title
        self.code = code
        self.selected = selected

    def __repr__(self) -> str:
        return f"<LanguageItem: {self.title} ({self.code}), selected={self.selected}>"
