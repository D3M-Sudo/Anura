# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import html
import time

import gi

# Set GTK version requirements before imports
gi.require_version("Adw", "1")
gi.require_version("Gio", "2.0")
gi.require_version("GLib", "2.0")
gi.require_version("GObject", "2.0")
gi.require_version("Gtk", "4.0")
gi.require_version("Pango", "1.0")

from gi.repository import Adw, Gio, GLib, Gtk, Pango  # noqa: E402
from loguru import logger  # noqa: E402

from anura.config import RESOURCE_PREFIX  # noqa: E402
from anura.models.capture_session import CaptureSession  # noqa: E402
from anura.services.history_service import get_history_service  # noqa: E402
from anura.services.settings import settings  # noqa: E402
from anura.utils.signal_manager import SignalManagerMixin  # noqa: E402


class HistoryRow(Gtk.Box):
    """Custom horizontal row widget for rendering historic captures in the virtualized Gtk.ListView."""

    def __init__(self) -> None:
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        self.set_margin_start(12)
        self.set_margin_end(12)
        self.set_margin_top(8)
        self.set_margin_bottom(8)

        # Gtk.Picture preserves rectangular aspect ratios beautifully (unlike Adw.Avatar)
        self.picture = Gtk.Picture()
        self.picture.set_size_request(80, 50)
        self.picture.set_content_fit(Gtk.ContentFit.CONTAIN)
        self.picture.add_css_class("card")
        self.append(self.picture)

        # Labels container
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        vbox.set_hexpand(True)

        self.title_label = Gtk.Label(halign=Gtk.Align.START)
        self.title_label.set_ellipsize(Pango.EllipsizeMode.END)
        self.title_label.set_use_markup(True)
        vbox.append(self.title_label)

        self.subtitle_label = Gtk.Label(halign=Gtk.Align.START)
        self.subtitle_label.set_ellipsize(Pango.EllipsizeMode.END)
        self.subtitle_label.add_css_class("dim-label")
        vbox.append(self.subtitle_label)

        self.append(vbox)

        # Language badge/tag
        self.lang_badge = Gtk.Label()
        self.lang_badge.add_css_class("dim-label")
        self.lang_badge.set_valign(Gtk.Align.CENTER)
        self.append(self.lang_badge)

    def bind(self, session: CaptureSession) -> None:
        """Bind session data fields directly to widgets."""
        raw_text = session.text or ""
        first_line = raw_text.splitlines()[0] if raw_text.splitlines() else ""
        if len(first_line) > 60:
            first_line = first_line[:60] + "…"

        self.title_label.set_markup(f"<b>{html.escape(first_line)}</b>")

        t = session.timestamp
        date_str = time.strftime("%Y-%m-%d %H:%M", time.localtime(t)) if t > 0 else ""
        transformer = session.transformer_name
        if transformer:
            subtitle = f"{date_str} • {transformer}"
        else:
            subtitle = date_str
        self.subtitle_label.set_text(subtitle)

        self.lang_badge.set_text((session.language or "").upper())

        base64_str = session.thumbnail_base64
        if base64_str:
            try:
                import base64

                from gi.repository import Gdk
                img_bytes = base64.b64decode(base64_str)
                gbytes = GLib.Bytes.new(img_bytes)
                texture = Gdk.Texture.new_from_bytes(gbytes)
                self.picture.set_paintable(texture)
                self.picture.set_visible(True)
            except Exception as e:
                logger.error(f"HistoryRow: Failed to load thumbnail texture: {e}")
                self.picture.set_paintable(None)
                self.picture.set_visible(False)
        else:
            self.picture.set_paintable(None)
            self.picture.set_visible(False)


@Gtk.Template(resource_path=f"{RESOURCE_PREFIX}/history_page.ui")
class HistoryPage(Adw.NavigationPage, SignalManagerMixin):
    __gtype_name__ = "HistoryPage"

    views_stack: Gtk.Stack = Gtk.Template.Child()
    warning_banner: Adw.Banner = Gtk.Template.Child()
    list_view: Gtk.ListView = Gtk.Template.Child()
    list_store: Gio.ListStore = Gtk.Template.Child()

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)
        SignalManagerMixin.__init__(self)

        self.settings = settings
        self._history_service = get_history_service()

        # Connect to HistoryService mutations
        self.connect_tracked(self._history_service, "changed", self._on_history_changed)
        # Connect to settings toggle changes
        self.connect_tracked(self.settings, "changed::history-enabled", self._on_settings_changed)

        # Wire up row activation
        self.connect_tracked(self.list_view, "activate", self._on_item_activated)

        # Initial refresh
        self.refresh_list()

    @Gtk.Template.Callback()
    def _on_item_setup(self, factory: Gtk.SignalListItemFactory, item: Gtk.ListItem) -> None:
        item.set_child(HistoryRow())

    @Gtk.Template.Callback()
    def _on_item_bind(self, factory: Gtk.SignalListItemFactory, list_item: Gtk.ListItem) -> None:
        row: HistoryRow = list_item.get_child()
        item: CaptureSession = list_item.get_item()
        row.bind(item)

    @Gtk.Template.Callback()
    def _on_clear_clicked(self, *_) -> None:
        """Present a beautiful Libadwaita confirmation dialog before clearing history."""
        window = self.get_root()
        dialog = Adw.MessageDialog(
            parent=window,
            heading=_("Clear History?"),
            body=_("Are you sure you want to permanently clear your capture history?"),
        )
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("clear", _("Clear"))
        dialog.set_response_appearance("clear", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_default_response("cancel")

        def _on_dialog_response(diag, response):
            if response == "clear":
                self._history_service.clear_history()
            diag.close()

        dialog.connect("response", _on_dialog_response)
        dialog.present()

    def _on_item_activated(self, list_view: Gtk.ListView, position: int) -> None:
        """Populates ExtractedPage with selection and navigates there."""
        try:
            session: CaptureSession = self.list_store.get_item(position)
            if not session:
                return

            window = self.get_root()
            if window and hasattr(window, "extracted_page"):
                # Stop any active TTS
                if hasattr(window, "tts_controller"):
                    window.tts_controller.stop()

                # Pop back to clear path if welcome or somewhere else
                if hasattr(window, "navigation_view"):
                    window.navigation_view.push_by_tag("extracted")

                # Restore text and transformer details
                window.extracted_page.set_extracted_text(
                    session.text, session.transformer_name
                )
                window.extracted_page.text_view.grab_focus()
        except Exception as e:
            logger.error(f"HistoryPage: Error activating historic capture: {e}")

    def refresh_list(self) -> None:
        """Reloads and synchronized internal Gio.ListStore model from HistoryService."""
        self.list_store.remove_all()
        sessions = self._history_service.get_sessions()

        for s in sessions:
            self.list_store.append(s)

        # Toggle Empty State vs List State
        if not sessions:
            self.views_stack.set_visible_child_name("empty_state")
        else:
            self.views_stack.set_visible_child_name("list_state")

        # Set GSettings warning banner visibility
        enabled = self.settings.get_boolean("history-enabled")
        self.warning_banner.set_revealed(not enabled)

    def _on_history_changed(self, *_) -> None:
        self.refresh_list()

    def _on_settings_changed(self, *_) -> None:
        self.refresh_list()

    def do_destroy(self) -> None:
        """Clean up signal handlers to avoid memory leaks."""
        self.teardown_all()
        super().do_destroy()
