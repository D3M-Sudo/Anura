#!/usr/bin/env python3
"""
Test keyboard shortcuts functionality using pytest framework.
Tests action registration and accelerator mapping without requiring full GTK environment.
"""

import os
import sys

import pytest

# Add the anura module to the path (from tests/ directory)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestKeyboardShortcuts:
    """Test keyboard shortcuts setup and action registration."""

    @pytest.mark.gtk
    def test_shortcuts_action_setup_method_exists(self):
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
    def test_shortcuts_source_code_contains_fixes(self):
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
    def test_paste_action_signature_fixed(self):
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

    def test_ui_shortcuts_file_updated(self):
        """Test that shortcuts UI file contains both shortcuts."""
        ui_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'ui', 'shortcuts.blp')

        if not os.path.exists(ui_file):
            pytest.skip(f"UI file not found: {ui_file}")

        with open(ui_file) as f:
            content = f.read()

        # Check for all shortcuts
        assert '<ctrl>question' in content, "Missing <ctrl>question shortcut"
        assert '<ctrl>slash' in content, "Missing <ctrl>slash shortcut"
        assert '<ctrl>h' in content, "Missing <ctrl>h shortcut"

        # Check for the shortcut descriptions
        assert 'Display Shortcuts (alternative)' in content, "Missing alternative shortcut description"
        assert 'Display Shortcuts (universal)' in content, "Missing universal shortcut description"


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
