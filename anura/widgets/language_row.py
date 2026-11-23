# This file is part of Anura.
# Copyright (C) 2022-2025 Andrey Maksimov (Frog)
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import contextlib
from gettext import gettext as _

from gi.repository import GLib, GObject, Gtk

from anura.config import RESOURCE_PREFIX
from anura.models.language_item import LanguageItem
from anura.services.language_manager import get_language_manager
from anura.utils.accessibility import announce_accessible
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
    _downloading_handler_id: int | None = None
    _downloaded_handler_id: int | None = None
    _progress_idle_id: int = 0

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)
        SignalManagerMixin.__init__(self)

        # Instance-level idle ID tracking to prevent cross-instance interference.
        # Uses a set so completed (auto-removed) source IDs can be pruned.
        self._idle_ids: set[int] = set()
        self._download_announced = False

        language_manager = get_language_manager()
        self.connect_tracked(language_manager, "downloading", self.update_progress)
        self.connect_tracked(language_manager, "downloaded", self.on_downloaded)
        self.connect_tracked(language_manager, "download-failed", self.on_download_failed)

        # Deferred UI update to ensure item is set.
        self._schedule_idle_update()

    @GObject.Property(type=GObject.TYPE_PYOBJECT)
    def item(self) -> LanguageItem | None:
        """Get the language item."""
        return self._item

    @item.setter  # type: ignore[no-redef]
    def item(self, item: LanguageItem) -> None:
        self._item = item
        self.label.set_label(self._item.title)

        # Context-aware accessibility enhancement (WCAG 2.4 compliant)
        install_tooltip = _("Install {language}").format(language=self._item.title)
        remove_tooltip = _("Remove {language}").format(language=self._item.title)

        self.install_btn.set_tooltip_text(install_tooltip)
        self.install_btn.update_property([Gtk.AccessibleProperty.LABEL], [install_tooltip])

        self.remove_btn.set_tooltip_text(remove_tooltip)
        self.remove_btn.update_property([Gtk.AccessibleProperty.LABEL], [remove_tooltip])

        progress_label = _("Download {language}").format(language=self._item.title)
        self.progress_bar.update_property([Gtk.AccessibleProperty.LABEL], [progress_label])

    def _schedule_idle_update(self) -> None:
        """Queue a one-shot UI refresh and prune its ID when it runs."""
        source_id: list[int] = []

        def _run() -> bool:
            if source_id:
                self._idle_ids.discard(source_id[0])
            return self._idle_update_ui()

        source_id.append(GLib.idle_add(_run))
        self._idle_ids.add(source_id[0])

    def _idle_update_ui(self) -> bool:
        """One-shot idle callback that refreshes the row when it is still attached."""
        if not self.get_parent() or not self._item:
            return GLib.SOURCE_REMOVE
        self.update_ui()
        return GLib.SOURCE_REMOVE

    def update_ui(self) -> None:
        """
        Updates the visibility and sensitivity of control buttons
        based on the language installation status.
        """
        if not self._item:
            return

        if self._item.code == "eng":
            self.remove_css_class("downloaded")
            self.install_btn.set_visible(False)
            self.remove_btn.set_sensitive(False)
            return

        # Handle button states based on installation/download status
        is_installed = self._item.code in get_language_manager().get_downloaded_codes()
        is_loading = self._item.code in get_language_manager().loading_languages

        if is_installed:
            self.add_css_class("downloaded")
        else:
            self.remove_css_class("downloaded")

        self.remove_btn.set_visible(is_installed)
        self.install_btn.set_visible(not is_installed)
        self.install_btn.set_sensitive(not is_loading)

        if not is_loading:
            self.revealer.set_reveal_child(False)

    def update_progress(self, _sender: GObject.GObject, code: str, progress: float) -> None:
        """Signal handler for download progress."""
        if self._item and code == self._item.code:
            # NEW-006: Use a single tracked idle ID to throttle UI updates.
            # This prevents flooding the main loop with redundant progress callbacks
            # if the download happens faster than the UI can repaint.
            if hasattr(self, "_progress_idle_id") and self._progress_idle_id:
                # NEW-010: Safe pruning from tracking set when removing the source.
                self._idle_ids.discard(self._progress_idle_id)
                GLib.source_remove(self._progress_idle_id)

            self._progress_idle_id = GLib.idle_add(self.late_update, code, progress)
            self._idle_ids.add(self._progress_idle_id)

    def late_update(self, code: str, progress: float) -> bool:
        """
        Updates the progress bar on the main thread.
        """
        # NEW-010: Cleanup tracking set for naturally completed sources.
        if hasattr(self, "_progress_idle_id") and self._progress_idle_id:
            self._idle_ids.discard(self._progress_idle_id)
            self._progress_idle_id = 0

        if self._item and self._item.code == code:
            if not self.revealer.get_reveal_child():
                self.revealer.set_reveal_child(True)

            self.progress_bar.set_fraction(progress / 100)
            if progress > 0 and not self._download_announced:
                message = _("Downloading {language}").format(language=self._item.title)
                self._download_announced = announce_accessible(self, message)

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

    def on_downloaded(self, _sender: GObject.GObject, code: str) -> None:
        """Announce completion and refresh the language row."""
        if self._item and self._item.code == code:
            message = _("Download of {language} completed").format(language=self._item.title)
            announce_accessible(self, message)
            self._download_announced = False
            self._schedule_idle_update()

    def on_download_failed(self, _sender: GObject.GObject, code: str) -> None:
        """Announce a failed download and restore the row controls."""
        if self._item and self._item.code == code:
            message = _("Download of {language} failed").format(language=self._item.title)
            announce_accessible(self, message)
            self._download_announced = False
            self._schedule_idle_update()

    def do_destroy(self) -> None:
        """Clean up signal handlers and pending idle_add callbacks to prevent memory leaks."""
        if hasattr(self, "_progress_idle_id") and self._progress_idle_id:
            with contextlib.suppress(TypeError, RuntimeError):
                GLib.source_remove(self._progress_idle_id)
            self._progress_idle_id = 0

        for idle_id in self._idle_ids:
            with contextlib.suppress(TypeError, RuntimeError):
                GLib.source_remove(idle_id)
        self._idle_ids.clear()

        self.teardown_all()
        super().do_destroy()
