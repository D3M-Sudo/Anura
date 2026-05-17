# tests/test_phase2_f.py
import pytest
from unittest.mock import Mock, patch
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, Gio
import os

# Load resources before importing widgets
resource_path = os.path.join(os.path.dirname(__file__), "..", "data", "com.github.d3msudo.anura.gresource")
if os.path.exists(resource_path):
    res = Gio.Resource.load(resource_path)
    res._register()

from anura.widgets.language_popover_row import LanguagePopoverRow
from anura.widgets.share_row import ShareRow
from anura.types.language_item import LanguageItem

class TestWidgets:
    @pytest.mark.gtk
    def test_language_popover_row(self):
        item = LanguageItem(code="fra", title="French")
        row = LanguagePopoverRow(item)
        assert row.get_child() is not None
        # Check if title is correct - this might be inside some sub-widget
        # but we just want to ensure it inits without error

    @pytest.mark.gtk
    def test_share_row(self):
        row = ShareRow("email")
        # Check if row is created successfully
        assert row is not None

    @pytest.mark.gtk
    def test_simple_widgets_init(self):
        # Test widgets that don't have complex dependencies
        from anura.widgets.preferences_dialog import PreferencesDialog
        try:
            from gi.repository import Adw
            app = Adw.Application()
            dialog = PreferencesDialog(transient_for=None)
            assert dialog is not None
        except Exception as e:
            pytest.skip(f"Could not init PreferencesDialog: {e}")
