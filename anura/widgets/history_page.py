# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import contextlib
from datetime import datetime
from gettext import gettext as _
from typing import TYPE_CHECKING
import weakref

import gi

# Set GTK version requirements before imports
gi.require_version("Adw", "1")
gi.require_version("GLib", "2.0")
gi.require_version("GObject", "2.0")
gi.require_version("Gtk", "4.0")

from gi.repository import Adw, GLib, Gtk  # noqa: E402
from loguru import logger  # noqa: E402

from anura.config import RESOURCE_PREFIX  # noqa: E402
from anura.services.settings import settings  # noqa: E402
from anura.utils.signal_manager import SignalManagerMixin  # noqa: E402

if TYPE_CHECKING:
    from anura.controllers.history_controller import HistoryController
    from anura.models.history import HistoryEntry
    from anura.services.history_service import HistoryService


_COPY_ICON = "edit-copy-symbolic"
_COPIED_ICON = "emblem-ok-symbolic"
_COPY_FEEDBACK_SECONDS = 2


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
    """Dedicated History page: list of persisted extractions with a per-row copy action.

    The page is a UI shell: copying is delegated to ``HistoryController`` and
    only the visual feedback (icon, tooltip, accessible label) lives here.
    """

    __gtype_name__ = "HistoryPage"

    history_stack: Gtk.Stack = Gtk.Template.Child()
    history_list: Gtk.ListBox = Gtk.Template.Child()
    clear_button: Gtk.Button = Gtk.Template.Child()

    def __init__(self, **kwargs: object) -> None:
        self._history_service = None  # type: "HistoryService | None"  # TYPE_CHECKING-only import
        # Weak reference: the window owns the controller, the page must not keep it alive.
        self._history_controller: weakref.ReferenceType[HistoryController] | None = None
        self._rows: list[Gtk.Widget] = []
        # Per-row handlers are NOT tracked by SignalManagerMixin (it would keep
        # every discarded row alive until teardown); they are disconnected in
        # _clear_rows() instead.
        self._row_handlers: list[tuple[Gtk.Widget, int]] = []
        # Copy-button feedback timers, keyed by button so they can be cancelled.
        self._feedback_timers: dict[Gtk.Button, int] = {}

        super().__init__(**kwargs)
        SignalManagerMixin.__init__(self)
        self.settings = settings

        self.connect_tracked(self.clear_button, "clicked", self._on_clear_clicked)
        # SignalManagerMixin.teardown_all() calls teardown() on registered controllers.
        self.register_controller(self)

    def setup(self, history_service: "HistoryService", history_controller: "HistoryController | None" = None) -> None:
        """Wire the shared HistoryService and HistoryController (injected by AnuraWindow)."""
        self._history_service = history_service
        self._history_controller = weakref.ref(history_controller) if history_controller is not None else None
        self.refresh()

    def teardown(self) -> None:
        """Unified teardown called by SignalManagerMixin."""
        self.cleanup()

    def cleanup(self) -> None:
        """Release row handlers, feedback timers and the controller reference."""
        self._clear_rows()
        self._history_controller = None

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
            self._append_row(entry)

    def _append_row(self, entry: "HistoryEntry") -> None:
        """Build one history row with its copy button and register it."""
        row = Adw.ActionRow(
            title=format_entry_title(entry.text),
            subtitle=format_entry_subtitle(entry),
        )
        copy_label = _("Copy text to clipboard")
        copy_btn = Gtk.Button(
            icon_name=_COPY_ICON,
            valign=Gtk.Align.CENTER,
            tooltip_text=copy_label,
        )
        copy_btn.add_css_class("flat")
        copy_btn.update_property([Gtk.AccessibleProperty.LABEL], [copy_label])
        handler_id = copy_btn.connect("clicked", self._on_copy_clicked, entry.text)
        self._row_handlers.append((copy_btn, handler_id))
        row.add_suffix(copy_btn)
        self.history_list.append(row)
        self._rows.append(row)

    def _on_copy_clicked(self, button: Gtk.Button, text: str) -> None:
        """Delegate the copy to the controller; show feedback only on success."""
        controller = self._history_controller() if self._history_controller is not None else None
        if controller is None:
            logger.warning("HistoryPage: Copy requested but no HistoryController is wired")
            return
        if controller.copy_entry_text(text):
            self._show_row_copy_feedback(button)

    def _show_row_copy_feedback(self, button: Gtk.Button) -> None:
        if button in self._feedback_timers:
            return  # Feedback already showing; the pending timer will restore the button.
        copied_text = _("Text copied to clipboard")
        button.set_icon_name(_COPIED_ICON)
        button.set_tooltip_text(copied_text)
        button.update_property([Gtk.AccessibleProperty.LABEL], [copied_text])
        self._feedback_timers[button] = GLib.timeout_add_seconds(
            _COPY_FEEDBACK_SECONDS, self._reset_row_copy_button, button
        )

    def _reset_row_copy_button(self, button: Gtk.Button) -> bool:
        self._feedback_timers.pop(button, None)
        copy_label = _("Copy text to clipboard")
        button.set_icon_name(_COPY_ICON)
        button.set_tooltip_text(copy_label)
        button.update_property([Gtk.AccessibleProperty.LABEL], [copy_label])
        return GLib.SOURCE_REMOVE

    def _cancel_feedback_timers(self) -> None:
        for source_id in self._feedback_timers.values():
            GLib.source_remove(source_id)
        self._feedback_timers.clear()

    def _clear_rows(self) -> None:
        """Remove previously displayed rows (tracked in Python, mock-safe).

        Also cancels pending feedback timers and disconnects the per-row
        handlers so discarded rows and buttons can be finalised.
        """
        self._cancel_feedback_timers()
        for widget, handler_id in self._row_handlers:
            with contextlib.suppress(TypeError, RuntimeError):
                widget.disconnect(handler_id)
        self._row_handlers.clear()
        for row in self._rows:
            with contextlib.suppress(RuntimeError):
                self.history_list.remove(row)
        self._rows.clear()

    def _on_clear_clicked(self, _button: Gtk.Button) -> None:
        """Ask for confirmation, then clear the history via the service."""
        if self._history_service is None:
            return

        parent = self.get_ancestor(Gtk.Window)
        # Adw.AlertDialog's .present(parent) accepts an optional parent window;
        # the deprecated message-dialog class inherits present() from Gtk.Window
        # (no arguments), so calling it with one used to raise a TypeError.
        dialog = Adw.AlertDialog(
            heading=_("Clear History?"),
            body=_("All stored extraction history will be removed. This cannot be undone."),
        )
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("clear", _("Clear"))
        dialog.set_response_appearance("clear", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_default_response("cancel")
        dialog.set_close_response("cancel")
        dialog.connect("response", self._on_clear_response)
        dialog.present(parent)

    def _on_clear_response(self, dialog: Adw.AlertDialog, response: str) -> None:
        dialog.force_close()
        if response != "clear":
            return
        try:
            self._history_service.clear()
        except OSError:
            logger.exception("HistoryPage: Failed to clear history")
        # Always refresh, even on failure, to reflect the actual stored state.
        self.refresh()
