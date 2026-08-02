# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

from gettext import gettext as _
import time
from typing import ClassVar

from gi.repository import Adw, Gio, GLib, GObject, Gtk

from anura.config import RESOURCE_PREFIX
from anura.models.history import CaptureSession
from anura.services.history_service import get_history_service
from anura.utils.signal_manager import SignalManagerMixin


@Gtk.Template(resource_path=f"{RESOURCE_PREFIX}/history_page.ui")
class HistoryPage(Adw.NavigationPage, SignalManagerMixin):
    __gtype_name__ = "HistoryPage"

    __gsignals__: ClassVar[dict[str, tuple]] = {
        "session-selected": (GObject.SignalFlags.RUN_LAST, None, (str, str)),  # text, lang
        "go-back": (GObject.SignalFlags.RUN_LAST, None, (int,)),
    }

    status_stack: Gtk.Stack = Gtk.Template.Child()
    history_list: Gtk.ListBox = Gtk.Template.Child()
    clear_button: Gtk.Button = Gtk.Template.Child()

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)
        SignalManagerMixin.__init__(self)

        self._history_service = get_history_service()
        self.connect_tracked(self._history_service, "history-changed", self._on_history_changed)
        self.connect_tracked(self.history_list, "row-activated", self._on_row_activated)

        # Register history actions
        action_group = Gio.SimpleActionGroup()
        clear_action = Gio.SimpleAction.new("clear", None)
        self.connect_tracked(clear_action, "activate", self._on_clear_clicked)
        action_group.add_action(clear_action)
        self.insert_action_group("history", action_group)

        self._update_ui()

    def _on_clear_clicked(self, _action, _param) -> None:
        """Confirm and clear all history."""
        dialog = Adw.MessageDialog(
            transient_for=self.get_root(),
            heading=_("Clear History?"),
            body=_("This will permanently delete all capture history. This action cannot be undone."),
        )
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("clear", _("Clear"))
        dialog.set_response_appearance("clear", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_default_response("cancel")
        dialog.set_close_response("cancel")

        def _on_response(_dialog, response_id):
            if response_id == "clear":
                self._history_service.clear_history()
            _dialog.destroy()

        self.connect_tracked(dialog, "response", _on_response)
        dialog.present()

    def _update_ui(self) -> None:
        """Clear and rebuild the history list UI."""
        # Clear existing rows
        while True:
            row = self.history_list.get_first_child()
            if not row:
                break
            self.history_list.remove(row)

        sessions = self._history_service.get_sessions()
        if not sessions:
            self.status_stack.set_visible_child_name("empty_state")
            self.clear_button.set_sensitive(False)
            return

        self.status_stack.set_visible_child_name("history_list")
        self.clear_button.set_sensitive(True)

        for session in sessions:
            row_widget = self._create_row_widget(session)
            self.history_list.append(row_widget)

    def _create_row_widget(self, session: CaptureSession) -> Gtk.ListBoxRow:
        """Create a custom row widget for a capture session."""
        row = Gtk.ListBoxRow()
        row.set_data("session_id", session.id)
        row.set_data("session_text", session.text)
        row.set_data("session_lang", session.lang)

        main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        main_box.set_margin_start(12)
        main_box.set_margin_end(12)
        main_box.set_margin_top(8)
        main_box.set_margin_bottom(8)

        # Content Box (Text preview, time, and language)
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        content_box.set_hexpand(True)

        # Text Preview: Truncate long lines, strip spaces
        preview_text = session.text.strip().replace("\n", " ")
        if len(preview_text) > 80:
            preview_text = preview_text[:80] + "…"

        preview_label = Gtk.Label(label=preview_text)
        preview_label.set_halign(Gtk.Align.START)
        preview_label.set_ellipsize(3)  # PANGO_ELLIPSIZE_END
        preview_label.add_css_class("body")
        content_box.append(preview_label)

        # Meta Box: Time and Language Badge
        meta_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

        # Time string
        formatted_time = time.strftime("%Y-%m-%d %H:%M", time.localtime(session.timestamp))
        time_label = Gtk.Label(label=formatted_time)
        time_label.add_css_class("dim-label")
        time_label.add_css_class("caption")
        meta_box.append(time_label)

        # Language Badge
        lang_label = Gtk.Label(label=session.lang.upper())
        lang_label.add_css_class("dim-label")
        lang_label.add_css_class("caption")
        lang_label.add_css_class("card")
        meta_box.append(lang_label)

        content_box.append(meta_box)
        main_box.append(content_box)

        # Individual Delete Button
        delete_btn = Gtk.Button()
        delete_btn.set_icon_name("user-trash-symbolic")
        delete_btn.add_css_class("flat")
        delete_btn.set_valign(Gtk.Align.CENTER)
        delete_btn.set_tooltip_text(_("Delete this item"))

        # Row-specific deletion callback
        self.connect_tracked(delete_btn, "clicked", lambda _: self._on_delete_clicked(session.id))
        main_box.append(delete_btn)

        row.set_child(main_box)
        return row

    def _on_history_changed(self, _service: object) -> None:
        """Update UI when history changes."""
        GLib.idle_add(self._update_ui)

    def _on_row_activated(self, _listbox: Gtk.ListBox, row: Gtk.ListBoxRow) -> None:
        """Handle row selection to open extracted page."""
        text = row.get_data("session_text")
        lang = row.get_data("session_lang")
        if text:
            self.emit("session-selected", text, lang)

    def _on_delete_clicked(self, session_id: str) -> None:
        """Delete a single session."""
        self._history_service.delete_session(session_id)

    def do_hiding(self) -> None:
        self.emit("go-back", 1)

    def do_destroy(self) -> None:
        self.teardown_all()
        super().do_destroy()
