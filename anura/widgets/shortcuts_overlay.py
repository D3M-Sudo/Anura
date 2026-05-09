# shortcuts_overlay.py
#
# Copyright 2026 D3M-Sudo (Anura fork and modifications)
"""
Keyboard shortcuts overlay widget for Anura OCR.
Provides an elegant cheat sheet with all available keyboard shortcuts.
"""

from gettext import gettext as _
from typing import ClassVar

import gi

gi.require_version("Adw", "1")
gi.require_version("Gdk", "4.0")
gi.require_version("GLib", "2.0")
gi.require_version("GObject", "2.0")
gi.require_version("Gtk", "4.0")
from gi.repository import Adw, Gdk, GObject, Gtk  # noqa: E402


class ShortcutsOverlay(Adw.Window):
    """Elegant keyboard shortcuts overlay window."""

    __gtype_name__ = "ShortcutsOverlay"

    __gsignals__: ClassVar[dict[str, tuple]] = {
        "closed": (GObject.SignalFlags.RUN_LAST, None, ()),
    }

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)

        # Configure window properties
        self.set_title(_("Keyboard Shortcuts"))
        self.set_modal(True)
        self.set_resizable(False)
        self.set_default_size(600, 500)

        # Create UI widgets programmatically
        self._create_ui()

        # Set up shortcuts data
        self._setup_shortcuts_data()
        self._populate_shortcuts_list()
        self._connect_signals()

        # Add fade-in animation
        self.add_css_class("anura-fade-in")
        self.add_css_class("anura-card")

    def _create_ui(self) -> None:
        """Create the UI layout programmatically."""
        # Main toolbar view
        toolbar_view = Adw.ToolbarView()

        # Header bar
        header_bar = Adw.HeaderBar()

        # Window title
        window_title = Adw.WindowTitle()
        window_title.set_title(_("Keyboard Shortcuts"))
        header_bar.set_title_widget(window_title)

        # Close button
        close_button = Gtk.Button()
        close_button.set_label(_("Close"))
        close_button.set_icon_name("window-close-symbolic")
        close_button.connect("clicked", lambda *_: self.close())
        header_bar.pack_end(close_button)

        toolbar_view.add_top_bar(header_bar)

        # Main content box
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        content_box.set_spacing(12)
        content_box.set_margin_top(12)
        content_box.set_margin_bottom(12)
        content_box.set_margin_start(12)
        content_box.set_margin_end(12)

        # Search entry
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text(_("Search shortcuts..."))
        content_box.append(self.search_entry)

        # Scrolled window for shortcuts list
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_vexpand(True)
        scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        # Shortcuts list
        self.shortcuts_list = Gtk.ListBox()
        self.shortcuts_list.set_selection_mode(Gtk.SelectionMode.NONE)
        scrolled_window.set_child(self.shortcuts_list)

        content_box.append(scrolled_window)
        toolbar_view.set_content(content_box)

        # Set as main content
        self.set_content(toolbar_view)

    def _setup_shortcuts_data(self) -> None:
        """Define all keyboard shortcuts with descriptions."""
        self.shortcuts_data = [
            # Screenshot & OCR
            {
                "category": _("Screenshot & OCR"),
                "shortcuts": [
                    {"key": "Ctrl + G", "description": _("Take screenshot")},
                    {"key": "Ctrl + Shift + G", "description": _("Take screenshot and copy to clipboard")},
                    {"key": "Ctrl + O", "description": _("Open image file")},
                    {"key": "Ctrl + V", "description": _("Paste image from clipboard")},
                ],
            },
            # Text Operations
            {
                "category": _("Text Operations"),
                "shortcuts": [
                    {"key": "Ctrl + C", "description": _("Copy text to clipboard")},
                    {"key": "Ctrl + L", "description": _("Listen to text (TTS)")},
                    {"key": "Ctrl + Shift + L", "description": _("Stop text-to-speech")},
                ],
            },
            # Application
            {
                "category": _("Application"),
                "shortcuts": [
                    {"key": "Ctrl + ,", "description": _("Open preferences")},
                    {"key": "Ctrl + ?", "description": _("Show keyboard shortcuts")},
                    {"key": "Ctrl + H", "description": _("Show keyboard shortcuts")},
                    {"key": "Ctrl + /", "description": _("Show keyboard shortcuts")},
                    {"key": "Ctrl + Q", "description": _("Quit application")},
                    {"key": "Ctrl + W", "description": _("Quit application")},
                ],
            },
            # Navigation
            {
                "category": _("Navigation"),
                "shortcuts": [
                    {"key": "Escape", "description": _("Close dialog/go back")},
                    {"key": "Tab", "description": _("Navigate between widgets")},
                    {"key": "Shift + Tab", "description": _("Navigate backwards")},
                ],
            },
            # Advanced
            {
                "category": _("Advanced"),
                "shortcuts": [
                    {"key": "Ctrl + Shift + O", "description": _("Open image file (advanced)")},
                    {"key": "F1", "description": _("Show help")},
                    {"key": "F10", "description": _("Open application menu")},
                ],
            },
        ]

    def _populate_shortcuts_list(self) -> None:
        """Populate the shortcuts list with categorized shortcuts."""
        for category_data in self.shortcuts_data:
            # Create category group
            group = Adw.PreferencesGroup()
            group.set_title(category_data["category"])

            # Add shortcuts to group
            for shortcut in category_data["shortcuts"]:
                row = Adw.ActionRow()
                row.set_title(shortcut["description"])

                # Create shortcut label
                shortcut_label = Gtk.ShortcutLabel()
                shortcut_label.set_accelerator(shortcut["key"])
                shortcut_label.set_valign(Gtk.Align.CENTER)

                row.add_suffix(shortcut_label)
                group.add(row)

            self.shortcuts_list.append(group)

    def _connect_signals(self) -> None:
        """Connect signals for search and window events."""
        # Search functionality
        self.search_entry.connect("search-changed", self._on_search_changed)

        # Window events
        self.connect("close-request", self._on_close_request)

    def _on_search_changed(self, entry: Gtk.SearchEntry) -> None:
        """Handle search entry changes."""
        query = entry.get_text().lower()

        # Filter each group based on search query
        for row in self.shortcuts_list:
            if isinstance(row, Adw.PreferencesGroup):
                visible_count = 0
                for child_row in row:
                    if isinstance(child_row, Adw.ActionRow):
                        title = child_row.get_title().lower()
                        if query in title:
                            child_row.set_visible(True)
                            visible_count += 1
                        else:
                            child_row.set_visible(False)

                # Hide empty groups
                row.set_visible(visible_count > 0)

    def _on_close_request(self, window: Gtk.Window) -> bool:
        """Handle window close request."""
        self.emit("closed")
        return False

    def _on_key_press(self, window: Gtk.Window, event: Gdk.Event) -> bool:
        """Handle key press events."""
        # Close on Escape
        if event.get_keyval() == Gdk.KEY_Escape:
            self.close()
            return True

        return False


def show_shortcuts_overlay(parent_window: Gtk.Window) -> None:
    """Show the keyboard shortcuts overlay."""
    try:
        overlay = ShortcutsOverlay(transient_for=parent_window)
        overlay.present()
    except Exception as e:
        from loguru import logger

        logger.error(f"Failed to show shortcuts overlay: {e}")
