# velis/widgets/history_page.py
try:
    import gi
    gi.require_version("Gtk", "4.0")
    gi.require_version("Adw", "1")
    from gi.repository import Adw, Gtk
    HAS_GTK = True
except (ImportError, ValueError):
    HAS_GTK = False
    class Gtk:
        class Box: pass
        def Template(*args, **kwargs): return lambda x: x

from velis.services.history_service import get_history_service


@Gtk.Template(resource_path="/io/github/d3msudo/velis/history_page.ui")
class HistoryPage(Gtk.Box):
    __gtype_name__ = "HistoryPage"

    if HAS_GTK:
        history_list = Gtk.Template.Child()

    def __init__(self, **kwargs):
        if HAS_GTK:
            super().__init__(**kwargs)
        self.history_service = get_history_service()

    def refresh(self):
        if not HAS_GTK:
            return

        # Clear list
        while child := self.history_list.get_first_child():
            self.history_list.remove(child)

        items = self.history_service.get_history()
        for item in items:
            row = Adw.ActionRow.new()
            row.set_title(item["text"][:100] + "..." if len(item["text"]) > 100 else item["text"])
            row.set_subtitle(item["timestamp"])
            self.history_list.append(row)

    if HAS_GTK:
        @Gtk.Template.Callback()
        def on_back_clicked(self, button):
            self.activate_action("win.show_welcome", None)
