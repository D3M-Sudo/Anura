# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""Regression tests for the GTK palette and shared UI design conventions."""

SPACING_SCALE = {4, 8, 12, 16, 24}
RADIUS_SCALE = {6, 12, 9999}
BLUEPRINT_FILES = (
    "data/ui/extracted_page.blp",
    "data/ui/history_page.blp",
    "data/ui/language_popover.blp",
    "data/ui/language_popover_row.blp",
    "data/ui/language_row.blp",
    "data/ui/preferences_dialog.blp",
    "data/ui/preferences_editor.blp",
    "data/ui/preferences_general.blp",
    "data/ui/preferences_languages.blp",
    "data/ui/preferences_voice.blp",
    "data/ui/share_row.blp",
    "data/ui/shortcuts_overlay.blp",
    "data/ui/welcome_page.blp",
    "data/ui/window.blp",
)


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
    assert _property(focus, "outline-color") == "@accent_bg_color"
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
    light_focus_color = _property(_rule(".anura-button:focus"), "outline-color")
    dark_focus_color = _property(_rule(".dark .anura-button:focus"), "outline-color")
    assert light_focus_color == "@accent_bg_color"
    assert dark_focus_color == "#21b77a"

    light_focus_color = _defined_color("accent_bg_color")
    dark_focus_color = "#21b77a"
    for surface in ("#ffffff", "#f6f5f4"):
        assert _contrast_ratio(light_focus_color, surface) >= 3.0
    for surface in ("#242424", "#353535"):
        assert _contrast_ratio(dark_focus_color, surface) >= 3.0


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




def test_blueprint_spacing_uses_the_shared_scale():
    for path in BLUEPRINT_FILES:
        for line_number, line in enumerate(_read_text(path).splitlines(), start=1):
            for property_name in ("spacing:", "margin-top:", "margin-bottom:", "margin-start:", "margin-end:"):
                if property_name in line:
                    value = line.split(property_name, maxsplit=1)[1].split(";", maxsplit=1)[0].strip()
                    if value.isdigit():
                        assert int(value) in SPACING_SCALE, f"{path}:{line_number}: unsupported spacing {value}px"


def test_stylesheet_spacing_uses_the_shared_scale():
    properties = ("padding:", "padding-top:", "padding-bottom:", "padding-left:", "padding-right:",
                  "margin:", "margin-top:", "margin-bottom:", "margin-left:", "margin-right:")
    for line in STYLE_CSS.splitlines():
        stripped = line.strip()
        for property_name in properties:
            if stripped.startswith(property_name):
                value = stripped.split(":", maxsplit=1)[1].split(";", maxsplit=1)[0]
                for token in value.split():
                    numeric = token.removesuffix("px")
                    if numeric.isdigit():
                        assert int(numeric) == 0 or int(numeric) in SPACING_SCALE, (
                            f"unsupported stylesheet spacing {numeric}px"
                        )


def test_custom_corner_radii_follow_the_shared_scale():
    radii = set()
    for line in STYLE_CSS.splitlines():
        if "border-radius:" in line:
            value = line.split("border-radius:", maxsplit=1)[1].split(";", maxsplit=1)[0].strip()
            if value.endswith("px") and value[:-2].isdigit():
                radii.add(int(value[:-2]))
    assert radii
    assert radii <= RADIUS_SCALE


def test_custom_typography_keeps_libadwaita_semantic_hierarchy():
    assert STYLE_CSS.count("font-size:") == 1
    assert ".welcome-hero label.title-1 {" in STYLE_CSS
    assert "font-size: 1.15em;" in STYLE_CSS
