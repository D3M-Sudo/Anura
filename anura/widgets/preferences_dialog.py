# This file is part of Anura.
# Copyright (C) 2022-2025 Andrey Maksimov (Frog)
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

from gettext import gettext as _

from gi.repository import Adw, GLib, Gtk

from anura.config import RESOURCE_PREFIX
from anura.services.language_manager import get_language_manager
from anura.utils.signal_manager import SignalManagerMixin
from anura.widgets.preferences_general_page import PreferencesGeneralPage
from anura.widgets.preferences_languages_page import PreferencesLanguagesPage


@Gtk.Template(resource_path=f"{RESOURCE_PREFIX}/preferences_dialog.ui")
class PreferencesDialog(Adw.PreferencesDialog, SignalManagerMixin):
    __gtype_name__ = "PreferencesDialog"

    general_page: PreferencesGeneralPage = Gtk.Template.Child()
    languages_page: PreferencesLanguagesPage = Gtk.Template.Child()

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)
        SignalManagerMixin.__init__(self)

        mgr = get_language_manager()
        self.connect_tracked(
            mgr, "downloaded", lambda _, code: GLib.idle_add(self.on_language_downloaded, code)
        )
        self.connect_tracked(
            mgr, "download-failed", lambda _, code: GLib.idle_add(self.on_language_download_failed, code)
        )

    def on_language_downloaded(self, code: str) -> None:
        """Handle language download completion - refresh UI state."""
        # Force refresh of language lists to show newly downloaded language
        if hasattr(self.languages_page, "load_languages"):
            self.languages_page.load_languages()
        if hasattr(self.general_page, "_setup_extra_languages"):
            self.general_page._setup_extra_languages()

    def on_language_download_failed(self, code: str) -> None:
        """Handle language download failure - show user feedback."""
        mgr = get_language_manager()
        lang_name = mgr.get_language(code)
        msg = _("Failed to download {language} model. Please check your internet connection.").format(
            language=lang_name
        )

        # Try to show toast on the parent window
        parent = self.get_transient_for()
        if parent and hasattr(parent, "show_toast"):
            parent.show_toast(msg)

    def do_destroy(self) -> None:
        """Clean up child pages when dialog is destroyed."""
        # Ensure child pages clean up their signal connections
        if hasattr(self.general_page, "disconnect_all_signals"):
            self.general_page.disconnect_all_signals()
        if hasattr(self.languages_page, "disconnect_all_signals"):
            self.languages_page.disconnect_all_signals()

        self.teardown_all()
        super().do_destroy()
