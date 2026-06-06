# This file is part of Anura.
# Copyright (C) 2022-2025 Andrey Maksimov (Frog)
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

from gettext import gettext as _

from gi.repository import GObject, Gtk

from anura.config import RESOURCE_PREFIX
from anura.models.language_item import LanguageItem


@Gtk.Template(resource_path=f"{RESOURCE_PREFIX}/language_popover_row.ui")
class LanguagePopoverRow(Gtk.ListBoxRow):
    __gtype_name__ = "LanguagePopoverRow"

    lang: LanguageItem

    # Widgets
    title: Gtk.Label = Gtk.Template.Child()
    selection: Gtk.Image = Gtk.Template.Child()

    def __init__(self, lang: LanguageItem) -> None:
        super().__init__()
        self.lang = lang
        self.title.set_label(self.lang.title)

        # Accessibility: set tooltip and label for screen readers
        tooltip = _("Select {language}").format(language=self.lang.title)
        self.set_tooltip_text(tooltip)
        self.update_property([Gtk.AccessibleProperty.LABEL], [tooltip])

        self.lang.bind_property(
            "selected",
            self.selection,
            "visible",
            GObject.BindingFlags.SYNC_CREATE,
        )
