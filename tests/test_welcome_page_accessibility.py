# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""Unit tests for WelcomePage OCR language accessibility synchronization."""

from unittest.mock import MagicMock

from anura.models.language_item import LanguageItem


def test_welcome_page_initializes_lang_combo_accessibility(headless_gi_mocks):
    """The constructor must configure the combo it actually builds (#544).

    The previous version replaced ``page.lang_combo`` with a MagicMock and
    called the helper manually, so it proved the helper works but not that
    initialisation runs.
    """
    from anura.widgets.welcome_page import WelcomePage

    page = WelcomePage()

    page.lang_combo.set_tooltip_text.assert_called_once()
    tooltip = page.lang_combo.set_tooltip_text.call_args[0][0]

    # The label and the accessibility text describe the same language.
    label = page.lang_combo.set_label.call_args[0][0]
    assert tooltip == f"OCR language: {label} (click to change)"

    page.lang_combo.update_property.assert_called_once()
    prop_args = page.lang_combo.update_property.call_args[0]
    assert prop_args[1] == [tooltip]


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


def test_more_options_action_closes_the_popover(headless_gi_mocks):
    from anura.widgets.welcome_page import WelcomePage

    page = WelcomePage()
    page.more_options_popover = MagicMock()

    page._on_more_options_action_clicked(MagicMock())

    page.more_options_popover.popdown.assert_called_once()


def test_drop_action_closes_popover_and_reveals_drop_area(headless_gi_mocks):
    from anura.widgets.welcome_page import WelcomePage

    page = WelcomePage()
    page.more_options_popover = MagicMock()
    page.drop_revealer = MagicMock()
    page.drop_revealer.get_reveal_child.return_value = False
    page.drop_button = MagicMock()
    page.drop_area = MagicMock()
    page.more_options_button = MagicMock()

    page._on_drop_button_clicked(MagicMock())

    page.more_options_popover.popdown.assert_called_once()
    page.drop_revealer.set_reveal_child.assert_called_once_with(True)
    page.drop_button.add_css_class.assert_called_once_with("suggested-action")
