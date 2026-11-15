# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""Regression tests for the GTK accent palette and button state styling."""


def _read_text(path: str) -> str:
    with open(path, encoding="utf-8") as source:
        return source.read()


STYLE_CSS = _read_text("data/style.css")
WELCOME_BLP = _read_text("data/ui/welcome_page.blp")


def _defined_color(name: str) -> str:
    prefix = f"@define-color {name} "
    line = next(line for line in STYLE_CSS.splitlines() if line.strip().startswith(prefix))
    return line.strip().removeprefix(prefix).removesuffix(";").lower()


def _rule(selector: str) -> str:
    start = STYLE_CSS.index(selector)
    opening = STYLE_CSS.index("{", start) + 1
    closing = STYLE_CSS.index("}", opening)
    return STYLE_CSS[opening:closing]


def _property(rule: str, name: str) -> str:
    prefix = f"{name}:"
    line = next(line for line in rule.splitlines() if line.strip().startswith(prefix))
    return line.strip().removeprefix(prefix).removesuffix(";").strip().lower()


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



def _blend(foreground: str, background: str, alpha: float) -> str:
    channels = []
    for index in (1, 3, 5):
        front = int(foreground[index : index + 2], 16)
        back = int(background[index : index + 2], 16)
        channels.append(round(front * alpha + back * (1 - alpha)))
    return "#" + "".join(f"{channel:02x}" for channel in channels)


def test_focus_indicator_meets_graphical_contrast_on_light_and_dark_surfaces():
    focus_color = _property(_rule(".anura-button:focus"), "outline-color")
    assert focus_color == "@accent_color"
    focus_color = _defined_color("accent_color")

    for surface in ("#ffffff", "#f6f5f4", "#242424", "#353535"):
        assert _contrast_ratio(focus_color, surface) >= 3.0


def test_history_empty_state_icon_meets_contrast_on_light_and_dark_surfaces():
    light_icon = _property(_rule(".history-empty-state image.icon"), "color")
    dark_icon = _property(_rule(".dark .history-empty-state image.icon"), "color")
    assert light_icon == "#0f7650"
    assert dark_icon == "#21b77a"

    for surface in ("#ffffff", "#f6f5f4"):
        tinted_surface = _blend("#16a36a", surface, 0.12)
        assert _contrast_ratio(light_icon, tinted_surface) >= 3.0

    for surface in ("#242424", "#353535"):
        tinted_surface = _blend("#16a36a", surface, 0.12)
        assert _contrast_ratio(dark_icon, tinted_surface) >= 3.0


def test_secondary_and_disabled_text_remain_theme_managed():
    disabled = _rule(".anura-button:disabled")
    assert "color:" not in disabled
    assert ".dim-label" not in STYLE_CSS


def test_processing_state_retains_semantic_warning_feedback():
    processing = _rule("#drop_area.drag-processing")
    assert "border-color: @warning_color" in processing
    assert "background: alpha(@warning_color, 0.15)" in processing
