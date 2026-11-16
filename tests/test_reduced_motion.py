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
