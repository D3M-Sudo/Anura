# This file is part of Anura.
# Copyright (C) 2022-2025 Andrey Maksimov (Frog)
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

from gettext import gettext as _
from gettext import ngettext
from gettext import pgettext as C_
from typing import ClassVar

import gi

# Set GTK version requirements before imports
gi.require_version("Adw", "1")
gi.require_version("GLib", "2.0")
gi.require_version("GObject", "2.0")
gi.require_version("Gtk", "4.0")

from gi.repository import Adw, GLib, GObject, Gtk  # noqa: E402
from loguru import logger  # noqa: E402

from anura.config import RESOURCE_PREFIX  # noqa: E402
from anura.services.settings import settings  # noqa: E402
from anura.services.share_service import get_share_service  # noqa: E402
from anura.utils.signal_manager import SignalManagerMixin  # noqa: E402
from anura.widgets.share_row import ShareRow  # noqa: E402


@Gtk.Template(resource_path=f"{RESOURCE_PREFIX}/extracted_page.ui")
class ExtractedPage(Adw.NavigationPage, SignalManagerMixin):
    __gtype_name__ = "ExtractedPage"

    __gsignals__: ClassVar[dict[str, tuple]] = {
        "go-back": (GObject.SignalFlags.RUN_LAST, None, (int,)),
        "on-listen-start": (GObject.SignalFlags.RUN_LAST, None, ()),
        "on-listen-stop": (GObject.SignalFlags.RUN_LAST, None, ()),
    }

    stats_label: Gtk.Label = Gtk.Template.Child()
    transformer_label: Gtk.Label = Gtk.Template.Child()
    share_list_box: Gtk.ListBox = Gtk.Template.Child()
    grab_btn: Gtk.Button = Gtk.Template.Child()
    text_copy_btn: Gtk.Button = Gtk.Template.Child()
    listen_stack: Gtk.Stack = Gtk.Template.Child()
    listen_btn: Gtk.Button = Gtk.Template.Child()
    listen_pause_btn: Gtk.Button = Gtk.Template.Child()
    listen_spinner: Gtk.Spinner = Gtk.Template.Child()
    share_button: Gtk.MenuButton = Gtk.Template.Child()
    text_view: Gtk.TextView = Gtk.Template.Child()
    buffer: Gtk.TextBuffer = Gtk.Template.Child()

    def __init__(self, **kwargs: object) -> None:
        # Pre-initialize attributes to avoid AttributeError during failed template init
        self.settings = settings
        self._share_service = None

        super().__init__(**kwargs)
        SignalManagerMixin.__init__(self)

        # Defensive check: ensure critical template components are loaded
        if not self.share_list_box:
            logger.error("ExtractedPage: share_list_box not found in template")
        else:
            self._share_service = get_share_service()
            for provider in self._share_service.providers():
                self.share_list_box.append(ShareRow(provider))
            # Connect to share signal to automatically popdown the menu
            self.connect_tracked(self._share_service, "share", self._on_share_finished)

        self.connect_tracked(self.buffer, "changed", self._on_buffer_changed)
        self.connect_tracked(self.buffer, "mark-set", self._on_mark_set)

        # Accessibility: set tooltip for the stats label
        self.stats_label.set_tooltip_text(
            _("Shows character and word count. If text is selected, shows selection stats.")
        )


    def _on_buffer_changed(self, buffer: Gtk.TextBuffer) -> None:
        """Update action sensitivities when buffer changes."""
        text = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), False)
        has_text = bool(text.strip()) if text else False

        # Update action sensitivity based on text presence
        if self.text_copy_btn:
            self.text_copy_btn.set_sensitive(has_text)
        if self.share_button:
            self.share_button.set_sensitive(has_text)
        if self.listen_btn:
            self.listen_btn.set_sensitive(has_text)

        self._update_stats_label()

    def _on_mark_set(self, _buffer: Gtk.TextBuffer, _location: Gtk.TextIter, mark: Gtk.TextMark) -> None:
        """Update stats label when selection changes."""
        # We only care about the selection bound or the insert mark which define the selection
        if mark.get_name() in ["selection_bound", "insert"]:
            self._update_stats_label()

    def _update_stats_label(self) -> None:
        """Update character and word count in the status bar label, considering selection."""
        selection = self.buffer.get_selection_bounds()
        if selection:
            start, end = selection
            text = self.buffer.get_text(start, end, False)
            # Use a prefix to indicate these are selection stats
            prefix = _("Selection: ")
        else:
            text = self.extracted_text
            prefix = ""

        char_count = len(text) if text else 0
        word_count = len(text.split()) if text else 0

        words_text = ngettext("{n} word", "{n} words", word_count).format(n=word_count)
        chars_text = ngettext("{n} character", "{n} characters", char_count).format(n=char_count)

        # Construct the stats label using a single translatable string
        stats = _("{words} | {chars}").format(words=words_text, chars=chars_text)
        self.stats_label.set_text(f"{prefix}{stats}")

        self._update_action_tooltips(bool(selection))

    def _update_action_tooltips(self, has_selection: bool) -> None:
        """Update tooltips and accessibility labels based on whether text is selected."""
        if has_selection:
            copy_tooltip = C_("Extracted screen", "Copy Selected Text to Clipboard (Ctrl+C)")
            listen_tooltip = C_("Extracted screen", "Listen to Selected Text (Ctrl+L)")
            share_tooltip = C_("Extracted screen", "Share Selection To")
        else:
            copy_tooltip = C_("Extracted screen", "Copy Extracted Text to Clipboard (Ctrl+C)")
            listen_tooltip = C_("Extracted screen", "Listen to Text (Ctrl+L)")
            share_tooltip = C_("Extracted screen", "Share To")

        if self.text_copy_btn:
            self.text_copy_btn.set_tooltip_text(copy_tooltip)
            self.text_copy_btn.update_property([Gtk.AccessibleProperty.LABEL], [copy_tooltip])

        if self.listen_btn:
            self.listen_btn.set_tooltip_text(listen_tooltip)
            self.listen_btn.update_property([Gtk.AccessibleProperty.LABEL], [listen_tooltip])

        if self.share_button:
            self.share_button.set_tooltip_text(share_tooltip)
            self.share_button.update_property([Gtk.AccessibleProperty.LABEL], [share_tooltip])

    def show_copy_feedback(self) -> None:
        """Temporarily change the copy button icon to a checkmark for UX feedback."""
        if not self.text_copy_btn:
            return

        # Defensive: if already showing feedback, don't nested-capture the checkmark
        if self.text_copy_btn.get_icon_name() == "emblem-ok-symbolic":
            return

        # Store original icon and switch to checkmark
        original_icon = self.text_copy_btn.get_icon_name()
        self.text_copy_btn.set_icon_name("emblem-ok-symbolic")

        GLib.timeout_add_seconds(2, self._reset_copy_icon, original_icon)

    def _reset_copy_icon(self, icon_name: str) -> bool:
        """Helper to reset copy button icon."""
        try:
            if self.text_copy_btn and self.text_copy_btn.get_icon_name() == "emblem-ok-symbolic":
                # Only reset if it's still showing the checkmark (don't overwrite newer state)
                self.text_copy_btn.set_icon_name(icon_name)
        except (AttributeError, RuntimeError, TypeError) as e:
            logger.exception(f"Anura: Failed to reset copy icon: {e}")
        return GLib.SOURCE_REMOVE

    def do_hiding(self) -> None:
        """Handle widget hiding event."""
        self.buffer.set_text("")
        self.emit("go-back", 1)

    def do_unmap(self) -> None:
        """Handle widget unmapping."""
        Gtk.Widget.do_unmap(self)

    def do_dispose(self) -> None:
        """Handle widget disposal."""
        # SignalManagerMixin handles all disconnects via do_destroy or explicit teardown_all
        super().do_dispose()

    @GObject.Property(type=str)
    def extracted_text(self) -> str:
        """Get the extracted text from the buffer."""
        return self.buffer.get_text(
            start=self.buffer.get_start_iter(),
            end=self.buffer.get_end_iter(),
            include_hidden_chars=False,
        )

    @extracted_text.setter  # type: ignore[no-redef]
    def extracted_text(self, text: str) -> None:
        self.set_extracted_text(text)

    def set_extracted_text(self, text: str, transformer_name: str = "") -> None:
        """Set the extracted text and optionally show the applied transformer."""
        GLib.idle_add(self._set_text_internal, text, transformer_name)

    def _set_text_internal(self, text: str, transformer_name: str) -> bool:
        """Atomic UI update for extracted text."""
        try:
            self.buffer.set_text(text)
            if transformer_name:
                self.transformer_label.set_text(_("Smart Parse: {name}").format(name=transformer_name))
                self.transformer_label.set_visible(True)
            else:
                self.transformer_label.set_visible(False)
        except (GLib.Error, ValueError) as e:
            logger.error(f"Error setting extracted text: {e}")
        return GLib.SOURCE_REMOVE

    def get_active_text(self) -> str:
        """Get selected text if available, otherwise the full text."""
        selection = self.buffer.get_selection_bounds()
        if selection:
            start, end = selection
            return self.buffer.get_text(start, end, False)
        return self.extracted_text

    def _on_share_finished(self, _service: object, _success: bool) -> None:
        """Handle share completion - close the popover."""
        popover = self.share_button.get_popover()
        if popover:
            popover.popdown()

    def update_tts_state(self, state: str) -> None:
        """Update the TTS UI state (called from TtsController via AnuraWindow)."""
        if state == "generating":
            self.swap_controls(True)
            if self.listen_stack:
                self.listen_stack.set_visible_child_name("spinner")
            if self.listen_spinner:
                self.listen_spinner.start()
        elif state == "playing":
            self.swap_controls(True)
            if self.listen_stack:
                self.listen_stack.set_visible_child_name("pause")
            if self.listen_spinner:
                self.listen_spinner.stop()
            if self.listen_pause_btn:
                self.listen_pause_btn.set_icon_name("media-playback-pause-symbolic")
        elif state == "paused":
            self.swap_controls(True)
            if self.listen_stack:
                self.listen_stack.set_visible_child_name("pause")
            if self.listen_pause_btn:
                self.listen_pause_btn.set_icon_name("media-playback-start-symbolic")
        else:  # idle
            self.swap_controls(False)
            if self.listen_stack:
                self.listen_stack.set_visible_child_name("button")
            if self.listen_spinner:
                self.listen_spinner.stop()

    def swap_controls(self, locked: bool) -> None:
        """Enable or disable interactive controls during TTS playback."""
        if self.grab_btn:
            self.grab_btn.set_sensitive(not locked)
        if self.text_copy_btn:
            self.text_copy_btn.set_sensitive(not locked)

    def do_destroy(self) -> None:
        """Clean up signal handlers to prevent memory leaks."""
        # do_dispose() already handles TTS and share service cleanup
        super().do_destroy()
