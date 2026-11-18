# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

from unittest.mock import MagicMock

from anura.models.language_item import LanguageItem


def _make_language_row(headless_gi_mocks, monkeypatch):
    import anura.widgets.language_row as language_row

    manager = MagicMock()
    monkeypatch.setattr(language_row, "get_language_manager", lambda: manager)

    row = language_row.LanguageRow()
    row.label = MagicMock()
    row.install_btn = MagicMock()
    row.remove_btn = MagicMock()
    row.progress_bar = MagicMock()
    row.revealer = MagicMock()
    row.announce = MagicMock()
    row.item = LanguageItem(code="ita", title="Italian")
    return language_row, row, manager


def test_progress_bar_accessible_name_includes_language(headless_gi_mocks, monkeypatch):
    _language_row, row, _manager = _make_language_row(headless_gi_mocks, monkeypatch)

    row.progress_bar.update_property.assert_called_once()
    properties, values = row.progress_bar.update_property.call_args.args
    assert len(properties) == 1
    assert values == ["Download Italian"]



def test_download_progress_reveals_updates_and_hides_progress_bar(headless_gi_mocks, monkeypatch):
    _language_row, row, _manager = _make_language_row(headless_gi_mocks, monkeypatch)
    row.revealer.get_reveal_child.side_effect = [False, True]

    row.late_update("ita", 35)
    row.late_update("ita", 100)

    assert [call.args[0] for call in row.progress_bar.set_fraction.call_args_list] == [0.35, 1.0]
    assert [call.args[0] for call in row.revealer.set_reveal_child.call_args_list] == [True, False]

def test_download_announcements_skip_percentage_updates(headless_gi_mocks, monkeypatch):
    _language_row, row, _manager = _make_language_row(headless_gi_mocks, monkeypatch)

    row.late_update("ita", 5)
    row.late_update("ita", 50)
    row.late_update("ita", 95)

    assert [call.args[0] for call in row.announce.call_args_list] == ["Downloading Italian"]


def test_download_completion_and_failure_are_announced(headless_gi_mocks, monkeypatch):
    _language_row, row, manager = _make_language_row(headless_gi_mocks, monkeypatch)

    row.late_update("ita", 10)
    row.on_downloaded(manager, "ita")
    row.on_download_failed(manager, "ita")

    assert [call.args[0] for call in row.announce.call_args_list] == [
        "Downloading Italian",
        "Download of Italian completed",
        "Download of Italian failed",
    ]


def test_installed_language_state_toggles_downloaded_style_class(headless_gi_mocks, monkeypatch):
    _language_row, row, manager = _make_language_row(headless_gi_mocks, monkeypatch)
    row.add_css_class = MagicMock()
    row.remove_css_class = MagicMock()
    manager.get_downloaded_codes.return_value = ["ita"]
    manager.loading_languages = set()

    row.update_ui()

    row.add_css_class.assert_called_once_with("downloaded")
    row.remove_css_class.assert_not_called()
    row.remove_btn.set_visible.assert_called_with(True)
    row.install_btn.set_visible.assert_called_with(False)
    row.install_btn.set_sensitive.assert_called_with(True)

    manager.get_downloaded_codes.return_value = []
    row.update_ui()

    row.remove_css_class.assert_called_once_with("downloaded")
    row.remove_btn.set_visible.assert_called_with(False)
    row.install_btn.set_visible.assert_called_with(True)
    row.install_btn.set_sensitive.assert_called_with(True)
