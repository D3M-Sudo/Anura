# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

from gettext import gettext as _
import html

from gi.repository import Adw, GLib, Gtk

from anura.config import APP_ID


class DialogManager:
    """Manager for application-level dialogs (About, Preferences)."""

    @staticmethod
    def show_about(parent_window, version, release_notes=None):
        """Show the About dialog."""
        # Adw.AboutDialog internally uses a GtkLabel with markup enabled
        _copyright = html.escape("© 2025-2026 D3M-Sudo & Anura Contributors\n© 2022-2025 Frog OCR Contributors")

        def _schedule_present():
            if parent_window:
                parent_window.set_focus(None)

            about_window = Adw.AboutDialog(
                application_name="Anura",
                application_icon=APP_ID,
                version=version,
                copyright=_copyright,
                website="https://github.com/D3M-Sudo/Anura",
                license_type=Gtk.License.MIT_X11,
                developers=["D3M-Sudo"],
                designers=["D3M-Sudo"],
            )

            about_window.add_legal_section(
                _("Acknowledgements"),
                "© 2022-2025 Andrey Maksimov (Frog OCR)",
                Gtk.License.UNKNOWN,
                _("Built with Tesseract OCR, GTK4, Libadwaita, and other open source components."),
            )
            about_window.add_link(_("Changelog"), "https://github.com/D3M-Sudo/Anura/blob/main/CHANGELOG.md")
            about_window.add_link(_("Report an Issue"), "https://github.com/D3M-Sudo/Anura/issues")

            about_window.present(parent_window)
            return GLib.SOURCE_REMOVE

        def _close_popovers():
            if parent_window and hasattr(parent_window, "close_popovers"):
                parent_window.set_focus(None)
                parent_window.close_popovers()
            GLib.idle_add(_schedule_present)
            return GLib.SOURCE_REMOVE

        if parent_window:
            parent_window.set_focus(None)
        GLib.idle_add(_close_popovers)

    @staticmethod
    def show_preferences(parent_window):
        """Show the preferences dialog."""
        if hasattr(parent_window, "show_preferences"):
            parent_window.show_preferences()
        else:
            from anura.widgets.preferences_dialog import PreferencesDialog

            dialog = PreferencesDialog()
            dialog.present(parent_window)

    @staticmethod
    def show_fatal_error(parent_window, title, body):
        """Show a fatal error message dialog."""
        dialog = Adw.MessageDialog(
            parent=parent_window,
            heading=title,
            body=body,
        )
        dialog.add_response("ok", _("OK"))
        dialog.set_default_response("ok")
        dialog.present()
