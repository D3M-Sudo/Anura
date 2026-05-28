# preferences_dialog.py
#
# Copyright 2021-2025 Andrey Maksimov
# Copyright 2026 D3M-Sudo (Anura fork and modifications)

from gi.repository import Adw, Gtk

from anura.config import RESOURCE_PREFIX
from anura.widgets.preferences_general_page import PreferencesGeneralPage
from anura.widgets.preferences_languages_page import PreferencesLanguagesPage


@Gtk.Template(resource_path=f"{RESOURCE_PREFIX}/preferences_dialog.ui")
class PreferencesDialog(Adw.PreferencesDialog):
    __gtype_name__ = "PreferencesDialog"

    general_page: PreferencesGeneralPage = Gtk.Template.Child()
    languages_page: PreferencesLanguagesPage = Gtk.Template.Child()

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)

    def on_language_downloaded(self, code: str) -> None:
        """Handle language download completion - refresh UI state."""
        # Force refresh of language lists to show newly downloaded language
        if hasattr(self.languages_page, "load_languages"):
            self.languages_page.load_languages()
        if hasattr(self.general_page, "_setup_extra_languages"):
            self.general_page._setup_extra_languages()

    def on_language_download_failed(self, code: str) -> None:
        """Handle language download failure - show user feedback."""
        # Could show error notification or update UI state
        # For now, just ensure UI remains responsive
        pass

    def do_destroy(self) -> None:
        """Clean up child pages when dialog is destroyed."""
        # Ensure child pages clean up their signal connections
        if hasattr(self.general_page, "disconnect_all_signals"):
            self.general_page.disconnect_all_signals()
        if hasattr(self.languages_page, "disconnect_all_signals"):
            self.languages_page.disconnect_all_signals()

        super().do_destroy()
