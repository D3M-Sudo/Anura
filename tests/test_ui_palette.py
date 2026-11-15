# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""Regression tests for the GTK accent palette and button state styling."""

from pathlib import Path
import re

import pytest


ROOT = Path(__file__).resolve().parents[1]
STYLE_CSS = (ROOT / "data" / "style.css").read_text(encoding="utf-8")
WELCOME_BLP = (ROOT / "data" / "ui" / "welcome_page.blp").read_text(encoding="utf-8")


def _defined_color(name: str) -> str:
    match = re.search(rf"@define-color\s+{re.escape(name)}\s+(#[0-9a-fA-F]{{6}})\s*;", STYLE_CSS)
    assert match is not None, f"Missing GTK color token: {name}"
    return match.group(1).lower()


def _rule(selector: str) -> str:
    match = re.search(rf"(?ms)^{re.escape(selector)}\s*\{{([^{{}}]*)\}}", STYLE_CSS)
    assert match is not None, f"Missing GTK CSS rule: {selector}"
    return match.group(1)


def _property(rule: str, name: str) -> str:
    match = re.search(rf"(?m)^\s*{re.escape(name)}\s*:\s*([^;]+);", rule)
    assert match is not None, f"Missing CSS property: {name}"
    return match.group(1).strip().lower()


def _luminance(color: str) -> float:
    channels = [int(color[index : index + 2], 16) / 255 for index in (1, 3, 5)]
    linear = [channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4 for channel in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def _contrast_ratio(foreground: str, background: str) -> float:
    lighter, darker = sorted((_luminance(foreground), _luminance(background)), reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


def test_approved_palette_roles_meet_graphical_and_suggested_action_contrast():
    accent = _defined_color("accent_color")
    accent_background = _defined_color("accent_bg_color")
    accent_foreground = _defined_color("accent_fg_color")

    assert accent == "#16a36a"
    assert accent_background == "#0f7650"
    assert accent_foreground == "#ffffff"

    # Graphical accents require 3:1 against both light and dark UI surfaces.
    assert _contrast_ratio(accent, "#ffffff") >= 3.0
    assert _contrast_ratio(accent, "#242424") >= 3.0
    assert _contrast_ratio(accent, "#353535") >= 3.0

    # Suggested-action controls use white foreground text on the dark green.
    assert _contrast_ratio(accent_foreground, accent_background) >= 4.5


def test_downloaded_language_text_meets_wcag_aa_in_light_and_dark_schemes():
    light_text = _property(_rule(".downloaded label"), "color")
    dark_text = _property(_rule(".dark .downloaded label"), "color")

    assert light_text == "#0f7650"
    assert dark_text == "#21b77a"

    for surface in ("#ffffff", "#f6f5f4"):
        assert _contrast_ratio(light_text, surface) >= 4.5

    for surface in ("#242424", "#353535"):
        assert _contrast_ratio(dark_text, surface) >= 4.5



def test_anura_button_preserves_hover_active_focus_and_disabled_states():
    hover = _rule(".anura-button:hover")
    active = _rule(".anura-button:active")
    focus = _rule(".anura-button:focus")
    disabled = _rule(".anura-button:disabled")

    assert _property(hover, "transform") != "none"
    assert _property(hover, "box-shadow") != "none"
    assert _property(active, "transform") == "translatey(0)"
    assert _property(focus, "outline-color") == "@accent_color"
    assert _property(focus, "outline-style") == "solid"
    assert _property(focus, "outline-width") == "2px"
    assert _property(disabled, "transform") == "none"
    assert _property(disabled, "box-shadow") == "none"


def test_screenshot_remains_the_welcome_page_suggested_action():
    screenshot_button = WELCOME_BLP.split("Button screenshot_button {", maxsplit=1)[1].split("};", maxsplit=1)[0]
    assert 'styles ["pill", "suggested-action", "anura-button"]' in screenshot_button
