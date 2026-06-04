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

import inspect
import os
import sys
from unittest.mock import MagicMock

import pytest

# Add the anura module to the path (from tests/ directory)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# Try to import gi (GTK). Tests that need GTK will skip if unavailable.
try:
    import gi

    gi.require_version("Gtk", "4.0")
    gi.require_version("Gio", "2.0")
    from gi.repository import Gio, GLib

    HAS_GI = True
except (ImportError, ValueError):
    HAS_GI = False
    Gio = MagicMock()
    GLib = MagicMock()


# Skip all tests in this module if GTK environment is not available
pytestmark = pytest.mark.skipif(not HAS_GI, reason="GTK environment (gi) not available")


@pytest.fixture
def setup_gtk_environment():
    """Setup GTK environment with GResource for GTK tests."""
    if not HAS_GI:
        pytest.skip("GTK environment not available")

    # Load GResource as documented in testing.md
    gresource_path = os.path.join(
        os.path.dirname(__file__), "..", "builddir", "data", "io.github.d3msudo.anura.gresource"
    )
    if os.path.exists(gresource_path):
        try:
            with open(gresource_path, "rb") as f:
                data = f.read()
                resource = Gio.Resource.new_from_data(GLib.Bytes.new(data))
                resource._register()
        except (AttributeError, OSError, RuntimeError) as e:
            pytest.skip(f"Cannot load GResource: {e}")


class TestKeyboardShortcuts:
    """Test keyboard shortcuts setup and action registration."""

    @pytest.mark.gtk
    def test_shortcuts_action_setup_method_exists(self, setup_gtk_environment):
        """Test that _setup_options method exists for keyboard shortcuts."""
        try:
            # Import without executing GTK-dependent code
            from anura.main import AnuraApplication

            # Check method exists (renamed from _setup_actions to _setup_options in refactor)
            assert hasattr(AnuraApplication, "_setup_options")
            assert callable(AnuraApplication._setup_options)

        except ImportError as e:
            pytest.skip(f"Cannot import main module: {e}")

    @pytest.mark.gtk
    def test_action_registry_class_exists(self, setup_gtk_environment):
        """Test that the ActionRegistry class exists and has setup_actions method."""
        try:
            from anura.core.action_registry import ActionRegistry

            # Check class exists and has required method
            assert ActionRegistry is not None
            assert hasattr(ActionRegistry, "setup_actions")
            assert callable(ActionRegistry.setup_actions)

        except ImportError as e:
            pytest.skip(f"Cannot import ActionRegistry: {e}")

    @pytest.mark.gtk
    def test_action_registry_registers_all_main_actions(self, setup_gtk_environment):
        """Test that ActionRegistry registers all expected main actions."""
        try:
            import gi

            gi.require_version("Gio", "2.0")

            from anura.core.action_registry import ActionRegistry

            # Mock app that tracks add_action calls
            actions_added = []
            accels_set = []

            mock_app = MagicMock()
            mock_app.add_action.side_effect = lambda action: actions_added.append(action.get_name())
            mock_app.set_accels_for_action.side_effect = (
                lambda action_name, accels: accels_set.append((action_name, accels))
            )

            registry = ActionRegistry(mock_app)
            registry.setup_actions()

            # Verify the main actions are registered
            expected_actions = {
                "get_screenshot",
                "get_screenshot_and_copy",
                "copy_to_clipboard",
                "open_image",
                "paste_from_clipboard",
                "listen",
                "listen_pause",
                "listen_cancel",
                "shortcuts",
                "quit",
                "preferences",
                "about",
                "github_star",
                "report_issue",
            }
            assert expected_actions.issubset(set(actions_added)), (
                f"Missing actions: {expected_actions - set(actions_added)}"
            )

        except ImportError as e:
            pytest.skip(f"Cannot import required modules: {e}")

    @pytest.mark.gtk
    def test_paste_action_signature_uses_varargs(self, setup_gtk_environment):
        """Test that on_paste_from_clipboard has varargs signature.

        BUG-FIX-2026-06-03: The signature was changed from (self, _variant) to
        (self, *_) to accept any positional args from GAction activation
        callbacks. The test was previously broken because it expected
        exactly 2 parameters.
        """
        try:
            from anura.main import AnuraApplication

            # Get the method
            method = AnuraApplication.on_paste_from_clipboard

            # Check signature — should be (self, *_) or (self, *_args, **_kwargs)
            sig = inspect.signature(method)
            params = list(sig.parameters.keys())

            # First param must be 'self'
            assert len(params) >= 1, f"Expected at least 1 param (self), got {len(params)}: {params}"
            assert params[0] == "self", f"First param must be 'self', got {params[0]}"

            # Must have VAR_POSITIONAL (*args) to accept any GAction callback args
            var_positional = [
                p for p in sig.parameters.values()
                if p.kind == inspect.Parameter.VAR_POSITIONAL
            ]
            assert len(var_positional) >= 1, (
                f"on_paste_from_clipboard must accept *args to handle GAction callbacks. "
                f"Current parameters: {params}"
            )

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
        ui_file = os.path.join(os.path.dirname(__file__), "..", "data", "ui", "shortcuts_overlay.blp")

        if not os.path.exists(ui_file):
            pytest.skip(f"UI file not found: {ui_file}")

        with open(ui_file) as f:
            content = f.read()

        # Check for UI structure
        assert "ShortcutsOverlay" in content, "Missing ShortcutsOverlay template"
        assert "search_entry" in content, "Missing search_entry widget"
        assert "shortcuts_list" in content, "Missing shortcuts_list widget"


@pytest.mark.gtk
class TestShortcutsIntegration:
    """Integration tests for keyboard shortcuts (require full environment)."""

    def test_full_shortcuts_registration(self):
        """Test full shortcuts registration (requires GTK environment)."""
        # This would require full GTK environment with display and GResources.
        # Marked as GTK-only — only run in environments with display server.
        pytest.skip("Full GTK test requires display and GResources")

