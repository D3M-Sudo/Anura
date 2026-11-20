# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

from pathlib import Path


class FakeSettings:
    def __init__(self, properties):
        self.properties = dict(properties)

    def find_property(self, name):
        return object() if name in self.properties else None

    def get_property(self, name):
        return self.properties[name]


class FakeWidget:
    def __init__(self):
        self.css_classes = set()

    def add_css_class(self, name):
        self.css_classes.add(name)

    def remove_css_class(self, name):
        self.css_classes.discard(name)


def test_reduced_motion_uses_interface_preference_when_available(headless_gi_mocks):
    from anura.utils.accessibility import is_reduced_motion_enabled

    settings = FakeSettings(
        {
            "gtk-interface-reduced-motion": True,
            "gtk-enable-animations": True,
        }
    )
    assert is_reduced_motion_enabled(settings) is True


def test_reduced_motion_falls_back_to_enable_animations(headless_gi_mocks):
    from anura.utils.accessibility import is_reduced_motion_enabled

    settings = FakeSettings({"gtk-enable-animations": False})
    assert is_reduced_motion_enabled(settings) is True
    settings.properties["gtk-enable-animations"] = True
    assert is_reduced_motion_enabled(settings) is False


def test_reduced_motion_class_tracks_setting_changes(headless_gi_mocks):
    from anura.utils.accessibility import sync_reduced_motion_class

    settings = FakeSettings({"gtk-enable-animations": False})
    widget = FakeWidget()

    sync_reduced_motion_class(widget, settings)
    assert "reduced-motion" in widget.css_classes

    settings.properties["gtk-enable-animations"] = True
    sync_reduced_motion_class(widget, settings)
    assert "reduced-motion" not in widget.css_classes


def test_reduced_motion_css_disables_custom_motion():
    css = Path("data/style.css").read_text(encoding="utf-8")
    assert ".reduced-motion *" in css
    assert "transition-duration: 0ms;" in css
    assert "animation-duration: 0ms;" in css
    assert "animation-iteration-count: 1;" in css
    assert ".reduced-motion .anura-button:hover" in css

def test_application_motion_consumers_are_covered_by_reduced_motion_policy():
    root = Path(__file__).resolve().parents[1]
    css = (root / "data/style.css").read_text(encoding="utf-8")
    shortcuts = (root / "anura/widgets/shortcuts_overlay.py").read_text(encoding="utf-8")
    welcome = (root / "anura/widgets/welcome_page.py").read_text(encoding="utf-8")
    welcome_blueprint = (root / "data/ui/welcome_page.blp").read_text(encoding="utf-8")

    reduced_rule = css.split(".reduced-motion *", maxsplit=1)[1].split("}", maxsplit=1)[0]
    assert "transition-duration: 0ms;" in reduced_rule
    assert "animation-duration: 0ms;" in reduced_rule
    assert "animation-iteration-count: 1;" in reduced_rule

    # These selectors are applied to descendants of the main window and inherit
    # its reduced-motion policy.
    descendant_motion_selectors = (
        ".anura-button",
        ".anura-slide-up",
        ".extracted-page textview",
        ".drag-hover",
        ".drag-processing",
    )
    for selector in descendant_motion_selectors:
        assert selector in css, f"missing motion selector: {selector}"

    assert 'styles ["pill", "suggested-action", "anura-button"]' in welcome_blueprint
    assert 'styles ["pill", "anura-button", "flat"]' in welcome_blueprint
    assert 'styles ["card", "anura-slide-up"]' in welcome_blueprint
    assert 'self.drop_area.add_css_class("drag-hover")' in welcome
    assert 'self.drop_area.add_css_class("drag-processing")' in welcome

    # ShortcutsOverlay applies motion classes to its own root. The descendant
    # selector cannot match that root, so the widget explicitly removes and
    # restores those classes as the GTK preference changes.
    for motion_class in ("anura-fade-in", "anura-card"):
        assert f'self.add_css_class("{motion_class}")' in shortcuts
        assert f'"{motion_class}"' in shortcuts
    assert "if reduced_motion:" in shortcuts
    assert "self.remove_css_class(css_class)" in shortcuts
    assert "self.add_css_class(css_class)" in shortcuts
