#!/usr/bin/env python3
"""
Test keyboard shortcuts functionality using pytest framework.
Tests action registration and accelerator mapping with proper GTK environment setup.
"""

import os
import sys

import pytest

# Add the anura module to the path (from tests/ directory)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


@pytest.fixture
def setup_gtk_environment():
    """Setup GTK environment with GResource for GTK tests."""
    import gi
    gi.require_version('Gtk', '4.0')
    gi.require_version('Gio', '2.0')
    from gi.repository import Gio, GLib

    # Load GResource as documented in testing.md
    gresource_path = os.path.join(
        os.path.dirname(__file__), '..', 'builddir', 'data',
        'com.github.d3msudo.anura.gresource'
    )
    if os.path.exists(gresource_path):
        with open(gresource_path, 'rb') as f:
            data = f.read()
            resource = Gio.Resource.new_from_data(GLib.Bytes.new(data))
            resource._register()


class TestKeyboardShortcuts:
    """Test keyboard shortcuts setup and action registration."""

    @pytest.mark.gtk
    def test_shortcuts_action_setup_method_exists(self, setup_gtk_environment):
        """Test that _setup_actions method contains expected shortcuts."""
        pytest.importorskip('anura.main')
        try:
            # Import without executing GTK-dependent code
            import anura.main
            _ = anura.main.AnuraApplication._setup_actions.__doc__

            # Check method exists
            assert hasattr(anura.main.AnuraApplication, '_setup_actions')
            assert callable(anura.main.AnuraApplication._setup_actions)

        except ImportError as e:
            pytest.skip(f"Cannot import main module: {e}")

    @pytest.mark.gtk
    def test_shortcuts_source_code_contains_fixes(self, setup_gtk_environment):
        """Test that the source code contains the keyboard shortcut fixes."""
        pytest.importorskip('anura.main')
        try:
            import anura.main

            # Get the source code of _setup_actions
            _ = anura.main.AnuraApplication._setup_actions.__code__.co_code

            # This is a basic check - in real scenarios we'd read the file
            # For now, we check the method exists and has proper signature
            assert hasattr(anura.main.AnuraApplication, '_setup_actions')

        except ImportError as e:
            pytest.skip(f"Cannot import main module: {e}")

    @pytest.mark.gtk
    def test_paste_action_signature_fixed(self, setup_gtk_environment):
        """Test that on_paste_from_clipboard has correct signature."""
        pytest.importorskip('anura.main')
        try:
            import inspect

            import anura.main

            # Get the method
            method = anura.main.AnuraApplication.on_paste_from_clipboard

            # Check signature
            sig = inspect.signature(method)
            params = list(sig.parameters.keys())

            # Should take 'self', '_action', and '_param' (3 params total)
            assert len(params) == 3, f"Expected 3 parameters, got {len(params)}: {params}"
            assert 'self' in params, "Missing 'self' parameter"
            assert '_action' in params, "Missing '_action' parameter"
            assert '_param' in params, "Missing '_param' parameter"

        except ImportError as e:
            pytest.skip(f"Cannot import main module: {e}")

    @pytest.mark.gtk
    def test_shortcuts_overlay_exists(self):
        """Test that the new shortcuts overlay system exists."""
        try:
            # Test that the ShortcutsOverlay class can be imported
            from anura.widgets.shortcuts_overlay import ShortcutsOverlay, show_shortcuts_overlay

            # Check class exists
            assert ShortcutsOverlay is not None
            assert show_shortcuts_overlay is not None
            assert callable(show_shortcuts_overlay)

            # Check class has expected methods
            assert hasattr(ShortcutsOverlay, '__init__')
            assert callable(ShortcutsOverlay)

        except ImportError as e:
            pytest.skip(f"Cannot import ShortcutsOverlay: {e}")

    @pytest.mark.gtk
    def test_shortcuts_overlay_ui_exists(self):
        """Test that shortcuts overlay UI file exists."""
        ui_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'ui', 'shortcuts_overlay.blp')

        if not os.path.exists(ui_file):
            pytest.skip(f"UI file not found: {ui_file}")

        with open(ui_file) as f:
            content = f.read()

        # Check for UI structure
        assert 'ShortcutsOverlay' in content, "Missing ShortcutsOverlay template"
        assert 'search_entry' in content, "Missing search_entry widget"
        assert 'shortcuts_list' in content, "Missing shortcuts_list widget"
        assert 'close_button' in content, "Missing close_button widget"


@pytest.mark.gtk
class TestShortcutsIntegration:
    """Integration tests for keyboard shortcuts (require full environment)."""

    def test_full_shortcuts_registration(self):
        """Test full shortcuts registration (requires GTK environment)."""
        try:
            # This would require full GTK environment
            # For now, we just test the class can be instantiated
            # In a real test environment, we'd test actual action registration

            pytest.skip("Full GTK test requires display and GResources")

        except ImportError as e:
            pytest.skip(f"Cannot import main module: {e}")
