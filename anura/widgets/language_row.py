# This file is part of Anura.
# Copyright (C) 2022-2025 Andrey Maksimov (Frog)
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import contextlib

from gi.repository import GLib, GObject, Gtk

from anura.config import RESOURCE_PREFIX
from anura.models.language_item import LanguageItem
from anura.services.language_manager import get_language_manager
from anura.utils.signal_manager import SignalManagerMixin


@Gtk.Template(resource_path=f"{RESOURCE_PREFIX}/language_row.ui")
class LanguageRow(Gtk.Overlay, SignalManagerMixin):
    __gtype_name__ = "LanguageRow"

    label: Gtk.Label = Gtk.Template.Child()
    install_btn: Gtk.Button = Gtk.Template.Child()
    remove_btn: Gtk.Button = Gtk.Template.Child()
    progress_bar: Gtk.ProgressBar = Gtk.Template.Child()
    revealer: Gtk.Revealer = Gtk.Template.Child()

    _item: LanguageItem | None = None

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)
        SignalManagerMixin.__init__(self)

        # Instance-level idle ID tracking to prevent cross-instance interference.
        # Uses a set so completed (auto-removed) source IDs can be pruned.
        self._idle_ids: set[int] = set()

        mgr = get_language_manager()
        self.connect_tracked(mgr, "downloading", self.update_progress)
        self.connect_tracked(mgr, "downloaded", self.on_downloaded)

        # Deferred UI update to ensure item is set
        idle_id = GLib.idle_add(self._idle_update_ui)
        self._idle_ids.add(idle_id)

    @GObject.Property(type=GObject.TYPE_PYOBJECT)
    def item(self) -> LanguageItem | None:
        """Get the language item."""
        return self._item

    @item.setter  # type: ignore[no-redef]
    def item(self, item: LanguageItem) -> None:
        self._item = item
        self.label.set_label(self._item.title)

    def _idle_update_ui(self) -> bool:
        """One-shot idle callback: runs update_ui and prunes itself from tracking."""
        # Check widget validity before accessing attributes to prevent crash if widget destroyed
        if not self.get_parent() or not self._item:
            return GLib.SOURCE_REMOVE
        self.update_ui()
        # Prune: this source has fired and auto-removed; discard the stale ID
        # (the ID was added in __init__ or on_downloaded)
        return GLib.SOURCE_REMOVE

    def update_ui(self) -> None:
        """
        Updates the visibility and sensitivity of control buttons
        based on the language installation status.
        """
        if not self._item:
            return

        if self._item.code == "eng":
            self.install_btn.set_visible(False)
            self.remove_btn.set_sensitive(False)
            return

        # Handle button states based on installation/download status
        is_installed = self._item.code in get_language_manager().get_downloaded_codes()
        is_loading = self._item.code in get_language_manager().loading_languages

        self.remove_btn.set_visible(is_installed)
        self.install_btn.set_visible(not is_installed)
        self.install_btn.set_sensitive(not is_loading)

        if not is_loading:
            self.revealer.set_reveal_child(False)

    def update_progress(self, sender: GObject.GObject, code: str, progress: float) -> None:
        """Signal handler for download progress."""
        if self._item and code == self._item.code:
            GLib.idle_add(self.late_update, code, progress)

    def late_update(self, code: str, progress: float) -> bool:
        """
        Updates the progress bar on the main thread.
        """
        if self._item and self._item.code == code:
            if not self.revealer.get_reveal_child():
                self.revealer.set_reveal_child(True)

            self.progress_bar.set_fraction(progress / 100)

            if progress >= 100:
                self.revealer.set_reveal_child(False)

        return GLib.SOURCE_REMOVE

    @Gtk.Template.Callback()
    def _on_download(self, _: Gtk.Button) -> None:
        """
        Triggered when the install button is clicked.
        """
        if not self._item or self._item.code in get_language_manager().loading_languages:
            return

        get_language_manager().download(self._item.code)
        self.update_ui()

    @Gtk.Template.Callback()
    def _on_remove(self, _: Gtk.Button) -> None:
        """
        Triggered when the remove button is clicked.
        """
        if not self._item or self._item.code in get_language_manager().loading_languages:
            return

        if self._item.code in get_language_manager().get_downloaded_codes():
            get_language_manager().remove_language(self._item.code)
            self.update_ui()

    def on_downloaded(self, sender: GObject.GObject, code: str) -> None:
        """
        Signal handler for completed downloads.
        """
        if self._item and self._item.code == code:
            idle_id = GLib.idle_add(self._idle_update_ui)
            self._idle_ids.add(idle_id)

    def do_destroy(self) -> None:
        """Clean up signal handlers and pending idle_add callbacks to prevent memory leaks."""
        for idle_id in self._idle_ids:
            with contextlib.suppress(TypeError, RuntimeError):
                GLib.source_remove(idle_id)
        self._idle_ids.clear()

        self.teardown_all()
        super().do_destroy()
