# This file is part of Anura.
# Copyright (C) 2022-2025 Andrey Maksimov (Frog)
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

from gi.repository import Adw, Gio, Gtk

from anura.config import RESOURCE_PREFIX
from anura.services.settings import settings
from anura.utils.signal_manager import SignalManagerMixin


@Gtk.Template(resource_path=f"{RESOURCE_PREFIX}/preferences_editor.ui")
class PreferencesEditorPage(Adw.PreferencesPage, SignalManagerMixin):
    __gtype_name__ = "PreferencesEditorPage"

    editor_line_numbers_switch: Adw.SwitchRow = Gtk.Template.Child()
    editor_highlight_line_switch: Adw.SwitchRow = Gtk.Template.Child()
    editor_wrap_mode_combo: Adw.ComboRow = Gtk.Template.Child()

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)
        SignalManagerMixin.__init__(self)

        self.settings = settings

        self.settings.bind(
            "editor-show-line-numbers", self.editor_line_numbers_switch, "active", Gio.SettingsBindFlags.DEFAULT
        )
        self.settings.bind(
            "editor-highlight-current-line",
            self.editor_highlight_line_switch,
            "active",
            Gio.SettingsBindFlags.DEFAULT,
        )

        self._setup_editor_wrap_mode()

    def _setup_editor_wrap_mode(self) -> None:
        from gettext import pgettext

        modes = [
            pgettext("wrap-mode", "Words"),
            pgettext("wrap-mode", "Characters"),
            pgettext("wrap-mode", "Disabled"),
        ]
        self.editor_wrap_mode_combo.set_model(Gtk.StringList.new(modes))
        mode = self.settings.get_string("editor-wrap-mode")
        mapping = {"word": 0, "char": 1, "none": 2}
        idx = mapping.get(mode, 0)
        self.editor_wrap_mode_combo.set_selected(idx)
        self.connect_tracked(self.editor_wrap_mode_combo, "notify::selected", self._on_editor_wrap_mode_changed)

    def _on_editor_wrap_mode_changed(self, combo: Adw.ComboRow, _param: object) -> None:
        idx = combo.get_selected()
        mapping = {0: "word", 1: "char", 2: "none"}
        mode = mapping.get(idx, "word")
        self.settings.set_string("editor-wrap-mode", mode)

    def do_destroy(self) -> None:
        """Clean up all tracked signal handlers to prevent memory leaks."""
        self.teardown_all()
        super().do_destroy()
