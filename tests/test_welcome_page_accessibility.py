# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""Unit tests for WelcomePage OCR language accessibility synchronization."""

from unittest.mock import MagicMock

from anura.models.language_item import LanguageItem


def test_welcome_page_initializes_lang_combo_accessibility(headless_gi_mocks):
    from anura.widgets.welcome_page import WelcomePage

    page = WelcomePage()
    page.lang_combo = MagicMock()

    # Trigger accessibility update for initial language
    page._update_lang_combo_accessibility("English")

    page.lang_combo.set_tooltip_text.assert_called_with("OCR language: English (click to change)")
    page.lang_combo.update_property.assert_called_once()
    prop_args = page.lang_combo.update_property.call_args[0]
    assert prop_args[1] == ["OCR language: English (click to change)"]


def test_welcome_page_on_language_changed_updates_accessibility(headless_gi_mocks):
    from anura.widgets.welcome_page import WelcomePage

    page = WelcomePage()
    page.lang_combo = MagicMock()
    page.settings = MagicMock()

    item = LanguageItem(code="ita", title="Italian", selected=True)
    popover = MagicMock()

    page._on_language_changed(popover, item)

    page.lang_combo.set_label.assert_called_with("Italian")
    page.lang_combo.set_tooltip_text.assert_called_with("OCR language: Italian (click to change)")
    page.lang_combo.update_property.assert_called_once()
    prop_args = page.lang_combo.update_property.call_args[0]
    assert prop_args[1] == ["OCR language: Italian (click to change)"]
    page.settings.set_string.assert_called_with("active-language", "ita")
