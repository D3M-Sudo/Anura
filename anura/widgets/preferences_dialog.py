# preferences_dialog.py
#
# Copyright 2021-2025 Andrey Maksimov
# Copyright 2026 D3M-Sudo (Anura fork and modifications)

from gi.repository import Gtk, Adw

from anura.config import RESOURCE_PREFIX
from anura.widgets.preferences_general_page import PreferencesGeneralPage
from anura.widgets.preferences_languages_page import PreferencesLanguagesPage


@Gtk.Template(resource_path=f'{RESOURCE_PREFIX}/ui/preferences_dialog.ui')
class PreferencesDialog(Adw.PreferencesDialog):
    __gtype_name__ = 'PreferencesDialog'

    general_page: PreferencesGeneralPage = Gtk.Template.Child()
    languages_page: PreferencesLanguagesPage = Gtk.Template.Child()


    def __init__(self, **kwargs):
        super().__init__(**kwargs)

