# Copyright 2023-2025 Andrey Maksimov
# Copyright 2026 D3M-Sudo (Anura fork and modifications)
#
# MIT License

from gettext import gettext as _

from gi.repository import GLib, Gtk

from anura.config import RESOURCE_PREFIX


@Gtk.Template(resource_path=f"{RESOURCE_PREFIX}/share_row.ui")
class ShareRow(Gtk.ListBoxRow):
    __gtype_name__ = "ShareRow"

    box: Gtk.Box = Gtk.Template.Child()
    image: Gtk.Image = Gtk.Template.Child()
    label: Gtk.Label = Gtk.Template.Child()

    provider_name: str = 'email'

    def __init__(self, provider_name: str):
        super().__init__()

        self.provider_name = provider_name or 'email'
        self.box.set_tooltip_text(_("Share via {name}").format(name=provider_name.capitalize()))
        self.label.set_label(provider_name.capitalize())
        self.image.set_from_icon_name(f"share-{self.provider_name.lower()}-symbolic")

    @Gtk.Template.Callback()
    def _on_released(self, *args):
        self.activate_action(
            "window.share", GLib.Variant.new_string(self.provider_name)
        )

