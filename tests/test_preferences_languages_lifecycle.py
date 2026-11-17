# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""Regression coverage for Preferences language-page and LanguageRow lifecycles."""

from types import SimpleNamespace
from unittest.mock import MagicMock
from urllib.parse import urlsplit


def _make_languages_page(monkeypatch, headless_gi_mocks):
    import anura.widgets.preferences_languages_page as module

    manager = MagicMock()
    manager.get_available_codes.return_value = []
    manager.get_downloaded_codes.return_value = []
    manager.get_language_item.return_value = None
    monkeypatch.setattr(module, "get_language_manager", lambda: manager)
    monkeypatch.setattr(module, "settings", MagicMock())

    monitor = MagicMock()
    address = SimpleNamespace(hostname=None, port=None)

    def make_address(hostname, port):
        address.hostname = hostname
        address.port = port
        return address

    monkeypatch.setattr(module.Gio.NetworkMonitor, "get_default", lambda: monitor)
    monkeypatch.setattr(module.Gio.NetworkAddress, "new", make_address)

    page = module.PreferencesLanguagesPage()
    return module, page, monitor, address


def test_network_probe_targets_the_configured_ocr_model_host(monkeypatch, headless_gi_mocks):
    """The reachability warning must probe the host that serves tessdata."""
    from anura.config import TESSDATA_URL

    _module, _page, monitor, address = _make_languages_page(monkeypatch, headless_gi_mocks)

    assert address.hostname == urlsplit(TESSDATA_URL).hostname
    assert address.port == 443
    assert monitor.can_reach_async.call_args.args[0] is address


def test_disposing_languages_page_cancels_probe_and_ignores_late_result(monkeypatch, headless_gi_mocks):
    """A late network result must not update a destroyed Preferences page."""
    _module, page, monitor, _address = _make_languages_page(monkeypatch, headless_gi_mocks)
    cancellable = page._network_cancellable
    callback = monitor.can_reach_async.call_args.args[2]
    result = MagicMock()

    page.do_destroy()

    cancellable.cancel.assert_called_once_with()
    callback(monitor, result)

    monitor.can_reach_finish.assert_not_called()
    page.banner.set_title.assert_not_called()
    page.banner.set_revealed.assert_not_called()


def test_language_row_prunes_idle_id_when_refresh_callback_finishes(monkeypatch, headless_gi_mocks):
    """Completed one-shot refreshes must not remain queued for destruction."""
    import anura.widgets.language_row as module

    callbacks = []

    def idle_add(callback, *args):
        callbacks.append((callback, args))
        return len(callbacks)

    monkeypatch.setattr(module.GLib, "idle_add", idle_add)
    row = module.LanguageRow()
    row._item = SimpleNamespace(code="ita", title="Italian")
    row.get_parent = MagicMock(return_value=object())
    row.update_ui = MagicMock()

    assert row._idle_ids == {1}

    callback, args = callbacks.pop(0)
    callback(*args)

    assert row._idle_ids == set()
    row.update_ui.assert_called_once_with()


def test_preferences_language_list_has_an_explicit_accessible_name(monkeypatch, headless_gi_mocks):
    """Assistive technology must receive a contextual name for the model list."""
    module, page, _monitor, _address = _make_languages_page(monkeypatch, headless_gi_mocks)

    page.list_view.update_property.assert_any_call([module.Gtk.AccessibleProperty.LABEL], ["Available OCR models"])
