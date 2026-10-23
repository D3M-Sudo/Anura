# This file is part of Anura.
# Copyright (C) 2022-2025 Andrey Maksimov (Frog)
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

from collections.abc import Callable

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

        # #539: idle callbacks scheduled by language-download signals must be
        # cancellable. Disconnecting the signals in do_destroy() does not
        # cancel an idle source that was already queued, which then ran
        # against destroyed child pages.
        self._pending_idle_sources: set[int] = set()
        self._disposed = False

        mgr = get_language_manager()
        self.connect_tracked(
            mgr,
            "downloaded",
            lambda _, code: self._schedule_idle(self.on_language_downloaded, code),
        )
        self.connect_tracked(
            mgr,
            "download-failed",
            lambda _, code: self._schedule_idle(self.on_language_download_failed, code),
        )

    def _schedule_idle(self, callback: Callable[[str], None], code: str) -> None:
        """Queue *callback* on the next main-loop idle and track its source.

        The source id is kept so ``do_destroy()`` can remove it; the wrapper
        also re-checks ``_disposed`` in case the dialog is closing between the
        idle being scheduled and it running.
        """
        if self._disposed:
            return

        source: list[int] = []

        def _run() -> bool:
            if source:
                self._pending_idle_sources.discard(source[0])
            if not self._disposed:
                callback(code)
            return GLib.SOURCE_REMOVE

        source.append(GLib.idle_add(_run))
        self._pending_idle_sources.add(source[0])

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
        # #539: drop any queued language-refresh idle before the pages go away,
        # and make sure a callback that already started bails out.
        self._disposed = True
        for source_id in list(self._pending_idle_sources):
            GLib.source_remove(source_id)
        self._pending_idle_sources.clear()

        # Ensure child pages clean up their signal connections
        if hasattr(self.general_page, "disconnect_all_signals"):
            self.general_page.disconnect_all_signals()
        if hasattr(self.languages_page, "disconnect_all_signals"):
            self.languages_page.disconnect_all_signals()

        self.teardown_all()
        super().do_destroy()
