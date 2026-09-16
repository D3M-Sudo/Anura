# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

from collections.abc import Callable
import contextlib
from datetime import datetime
from gettext import gettext as _
from typing import TYPE_CHECKING

import gi

# Set GTK version requirements before imports
gi.require_version("Adw", "1")
gi.require_version("GLib", "2.0")
gi.require_version("GObject", "2.0")
gi.require_version("Gtk", "4.0")

from gi.repository import Adw, GLib, Gtk  # noqa: E402
from loguru import logger  # noqa: E402

from anura.config import RESOURCE_PREFIX  # noqa: E402
from anura.services.clipboard_service import get_clipboard_service  # noqa: E402
from anura.services.settings import settings  # noqa: E402
from anura.utils.signal_manager import SignalManagerMixin  # noqa: E402

if TYPE_CHECKING:
    from anura.models.history import HistoryEntry
    from anura.services.history_service import HistoryService


def format_entry_timestamp(iso_timestamp: str) -> str:
    """Render an ISO-8601 UTC timestamp as a short human-readable string.

    Falls back to the raw string when the timestamp cannot be parsed, so a
    malformed entry never breaks the page.
    """
    try:
        return datetime.fromisoformat(iso_timestamp).strftime("%Y-%m-%d %H:%M")
    except (ValueError, TypeError):
        return iso_timestamp


def format_entry_subtitle(entry: "HistoryEntry") -> str:
    """Compose the row subtitle: timestamp · language · applied_name · confidence.

    Empty/unavailable fields are skipped; a fully empty entry still yields a
    non-crashing (possibly empty) string.
    """
    parts = [format_entry_timestamp(entry.timestamp)]
    if entry.language:
        parts.append(entry.language)
    if entry.applied_name:
        parts.append(entry.applied_name)
    if entry.conf > 0:
        parts.append(f"{entry.conf:.0f}%")
    return " · ".join(parts)


def format_entry_title(text: str, max_chars: int = 200) -> str:
    """First line of the extracted text, capped to avoid pathological labels."""
    first_line = text.splitlines()[0] if text else ""
    if len(first_line) > max_chars:
        first_line = first_line[: max_chars - 1] + "…"
    return first_line


@Gtk.Template(resource_path=f"{RESOURCE_PREFIX}/history_page.ui")
class HistoryPage(Adw.NavigationPage, SignalManagerMixin):
    """Dedicated History V1 page: read-only list of persisted extractions."""

    __gtype_name__ = "HistoryPage"

    history_stack: Gtk.Stack = Gtk.Template.Child()
    history_list: Gtk.ListBox = Gtk.Template.Child()
    clear_button: Gtk.Button = Gtk.Template.Child()

    def __init__(self, **kwargs: object) -> None:
        self._history_service = None  # type: "HistoryService | None"  # TYPE_CHECKING-only import
        self._rows: list[Gtk.Widget] = []

        super().__init__(**kwargs)
        SignalManagerMixin.__init__(self)
        self.settings = settings

        self.connect_tracked(self.clear_button, "clicked", self._on_clear_clicked)

    def setup(self, history_service: "HistoryService") -> None:
        """Wire the shared HistoryService instance (injected by AnuraWindow)."""
        self._history_service = history_service
        self.refresh()

    def refresh(self) -> None:
        """Reload entries from the service and repopulate the list."""
        self._clear_rows()

        history_enabled = False
        with contextlib.suppress(AttributeError, RuntimeError):
            history_enabled = self.settings.get_boolean("history-enabled")

        entries = []
        if self._history_service is not None:
            try:
                entries = self._history_service.get_entries()
            except OSError:
                logger.exception("HistoryPage: Failed to read history for display")
                entries = []

        if not entries:
            # Disabled recording shows the dedicated state; existing stored
            # history is still displayed even when recording is off.
            self.history_stack.set_visible_child_name("disabled" if not history_enabled else "empty")
            return

        self.history_stack.set_visible_child_name("entries")
        for entry in entries:
            row = Adw.ActionRow(
                title=format_entry_title(entry.text),
                subtitle=format_entry_subtitle(entry),
                activatable=True,
            )
            copy_btn = Gtk.Button(
                icon_name="edit-copy-symbolic",
                valign=Gtk.Align.CENTER,
                tooltip_text=_("Copy text to clipboard"),
            )
            copy_btn.add_css_class("flat")
            copy_btn.update_property([Gtk.AccessibleProperty.LABEL], [_("Copy text to clipboard")])
            copy_cb = self._make_copy_callback(entry.text, copy_btn)
            self.connect_tracked(copy_btn, "clicked", copy_cb)
            self.connect_tracked(row, "activated", copy_cb)
            row.add_suffix(copy_btn)
            self.history_list.append(row)
            self._rows.append(row)

    def _make_copy_callback(self, text: str, button: Gtk.Button) -> Callable[[object], None]:
        def _on_copy_clicked(*_args: object) -> None:
            try:
                get_clipboard_service().set(text)
                self._show_row_copy_feedback(button)
            except Exception as e:
                logger.exception(f"HistoryPage: Failed to copy entry to clipboard: {e}")

        return _on_copy_clicked

    def _show_row_copy_feedback(self, button: Gtk.Button) -> None:
        if button.get_icon_name() == "emblem-ok-symbolic":
            return
        original_icon = button.get_icon_name()
        button.set_icon_name("emblem-ok-symbolic")
        copied_text = _("Copied to clipboard!")
        button.set_tooltip_text(copied_text)
        button.update_property([Gtk.AccessibleProperty.LABEL], [copied_text])

        GLib.timeout_add_seconds(2, self._reset_row_copy_button, button, original_icon)

    def _reset_row_copy_button(self, button: Gtk.Button, original_icon: str) -> bool:
        try:
            if button and button.get_icon_name() == "emblem-ok-symbolic":
                button.set_icon_name(original_icon)
                copy_text = _("Copy text to clipboard")
                button.set_tooltip_text(copy_text)
                button.update_property([Gtk.AccessibleProperty.LABEL], [copy_text])
        except (AttributeError, RuntimeError, TypeError) as e:
            logger.exception(f"HistoryPage: Failed to reset row copy button: {e}")
        return GLib.SOURCE_REMOVE

    def _clear_rows(self) -> None:
        """Remove previously displayed rows (tracked in Python, mock-safe)."""
        for row in self._rows:
            with contextlib.suppress(RuntimeError):
                self.history_list.remove(row)
        self._rows.clear()

    def _on_clear_clicked(self, _button: Gtk.Button) -> None:
        """Ask for confirmation, then clear the history via the service."""
        if self._history_service is None:
            return

        parent = self.get_ancestor(Gtk.Window)
        dialog = Adw.MessageDialog(
            heading=_("Clear History?"),
            body=_("All stored extraction history will be removed. This cannot be undone."),
        )
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("clear", _("Clear"))
        dialog.set_response_appearance("clear", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_default_response("cancel")
        dialog.set_close_response("cancel")
        dialog.connect("response", self._on_clear_response)
        if parent is not None:
            dialog.present(parent)
        else:
            dialog.present()

    def _on_clear_response(self, dialog: Adw.MessageDialog, response: str) -> None:
        dialog.force_close()
        if response != "clear":
            return
        try:
            self._history_service.clear()
        except OSError:
            logger.exception("HistoryPage: Failed to clear history")
        # Always refresh, even on failure, to reflect the actual stored state.
        self.refresh()
