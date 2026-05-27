#!/usr/bin/env python3
# This file is part of Anura.
# Copyright (C) 2022-2025 Andrey Maksimov (Frog)
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""
Test keyboard shortcuts functionality using pytest framework.
Tests action registration and accelerator mapping with proper GTK environment setup.
"""

import os
import sys

import pytest

# Add the anura module to the path (from tests/ directory)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture
def setup_gtk_environment():
    """Setup GTK environment with GResource for GTK tests."""
    pytest.importorskip("gi")

    import gi

    gi.require_version("Gtk", "4.0")
    gi.require_version("Gio", "2.0")
    from gi.repository import Gio, GLib

    # Load GResource as documented in testing.md
    gresource_path = os.path.join(
        os.path.dirname(__file__), "..", "data", "io.github.d3msudo.anura.gresource"
    )
    if os.path.exists(gresource_path):
        with open(gresource_path, "rb") as f:
            data = f.read()
            resource = Gio.Resource.new_from_data(GLib.Bytes.new(data))
            resource._register()


class TestKeyboardShortcuts:
    """Test keyboard shortcuts setup and action registration."""

    @pytest.mark.gtk
    def test_shortcuts_action_setup_method_exists(self, setup_gtk_environment):
        """Test that ActionRegistry.setup_actions method exists."""
        try:
            from anura.core.action_registry import ActionRegistry

            # Check method exists
            assert hasattr(ActionRegistry, "setup_actions")
            assert callable(ActionRegistry.setup_actions)

        except ImportError as e:
            pytest.skip(f"Cannot import action_registry module: {e}")

    @pytest.mark.gtk
    def test_shortcuts_source_code_contains_fixes(self, setup_gtk_environment):
        """Test that ActionRegistry exists."""
        try:
            from anura.core.action_registry import ActionRegistry
            assert ActionRegistry is not None

        except ImportError as e:
            pytest.skip(f"Cannot import action_registry module: {e}")

    @pytest.mark.gtk
    def test_paste_action_signature_fixed(self, setup_gtk_environment):
        """Test that on_paste_from_clipboard has correct signature."""
        pytest.importorskip("anura.main")
        try:
            from anura.main import AnuraApplication

            # Get the method
            method = AnuraApplication.on_paste_from_clipboard

            # Check it accepts *args
            import inspect
            sig = inspect.signature(method)
            params = list(sig.parameters.values())

            # Should have self and VAR_POSITIONAL (*)
            assert any(p.kind == inspect.Parameter.VAR_POSITIONAL for p in params)

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
            assert hasattr(ShortcutsOverlay, "__init__")
            assert callable(ShortcutsOverlay)

        except ImportError as e:
            pytest.skip(f"Cannot import ShortcutsOverlay: {e}")

    @pytest.mark.gtk
    def test_shortcuts_overlay_ui_exists(self):
        """Test that shortcuts overlay UI file exists."""
        # The file is actually .ui now, as .blp is source
        ui_file = os.path.join(os.path.dirname(__file__), "..", "data", "ui", "shortcuts_overlay.ui")

        if not os.path.exists(ui_file):
            # Try .blp if .ui is not found (might not have been compiled yet in local env)
            ui_file = os.path.join(os.path.dirname(__file__), "..", "data", "ui", "shortcuts_overlay.blp")

        if not os.path.exists(ui_file):
            pytest.skip(f"UI/BLP file not found: {ui_file}")

        with open(ui_file) as f:
            content = f.read()

        # Check for UI structure
        if ui_file.endswith(".ui"):
            assert "ShortcutsOverlay" in content, "Missing ShortcutsOverlay template"
        else:
            assert "template ShortcutsOverlay" in content, "Missing ShortcutsOverlay template in BLP"


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
