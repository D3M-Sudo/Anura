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
    cancellable = MagicMock()

    def make_address(hostname, port):
        address.hostname = hostname
        address.port = port
        return address

    monkeypatch.setattr(
        module.Gio,
        "NetworkMonitor",
        SimpleNamespace(get_default=lambda: monitor),
    )
    monkeypatch.setattr(
        module.Gio,
        "NetworkAddress",
        SimpleNamespace(new=make_address),
    )
    monkeypatch.setattr(module.Gio, "Cancellable", lambda: cancellable)

    page = module.PreferencesLanguagesPage()
    return module, page, monitor, address, cancellable


def test_network_probe_targets_the_configured_ocr_model_host(monkeypatch, headless_gi_mocks):
    """The reachability warning must probe the host that serves tessdata."""
    from anura.config import TESSDATA_URL

    _module, _page, monitor, address, _cancellable = _make_languages_page(monkeypatch, headless_gi_mocks)

    assert address.hostname == urlsplit(TESSDATA_URL).hostname
    assert address.port == 443
    assert monitor.can_reach_async.call_args.args[0] is address


def test_disposing_languages_page_cancels_probe_and_ignores_late_result(monkeypatch, headless_gi_mocks):
    """A late network result must not update a destroyed Preferences page."""
    _module, page, monitor, _address, cancellable = _make_languages_page(monkeypatch, headless_gi_mocks)
    callback = monitor.can_reach_async.call_args.args[2]
    result = MagicMock()
    base_class = _module.PreferencesLanguagesPage.__mro__[1]
    monkeypatch.setattr(base_class, "do_destroy", lambda _self: None, raising=False)

    page.do_destroy()

    cancellable.cancel.assert_called_once_with()
    callback(monitor, result)

    monitor.can_reach_finish.assert_not_called()
    page.banner.set_title.assert_not_called()
    page.banner.set_revealed.assert_not_called()


def test_network_banner_retry_hides_warning_after_recovery(monkeypatch, headless_gi_mocks):
    """Retrying the source probe clears the unreachable banner after recovery."""
    _module, page, monitor, _address, _cancellable = _make_languages_page(monkeypatch, headless_gi_mocks)

    monitor.can_reach_finish.return_value = False
    failed_callback = monitor.can_reach_async.call_args.args[2]
    failed_callback(monitor, MagicMock())

    assert page.banner.set_revealed.call_args.args == (True,)
    assert "unreachable" in page.banner.set_title.call_args.args[0].lower()

    page._on_banner_clicked(MagicMock())

    retry_callback = monitor.can_reach_async.call_args.args[2]
    monitor.can_reach_finish.return_value = True
    monitor.get_network_metered.return_value = False
    retry_callback(monitor, MagicMock())

    assert page.banner.set_revealed.call_args.args == (False,)


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
    _module, page, _monitor, _address, _cancellable = _make_languages_page(monkeypatch, headless_gi_mocks)

    assert any(call.args[1] == ["Available OCR models"] for call in page.list_view.update_property.call_args_list)


def test_language_search_matches_titles_case_insensitively(monkeypatch, headless_gi_mocks):
    """Search matches a language title without depending on input casing."""
    module, _page, _monitor, _address, _cancellable = _make_languages_page(monkeypatch, headless_gi_mocks)
    item = SimpleNamespace(code="eng", title="English")

    assert module.PreferencesLanguagesPage.filter_func(item, "GLiSh")
    assert not module.PreferencesLanguagesPage.filter_func(item, "italian")


def test_default_language_filter_shows_only_downloaded_codes(monkeypatch, headless_gi_mocks):
    """An empty search query limits the visible list to downloaded models."""
    module, _page, _monitor, _address, _cancellable = _make_languages_page(monkeypatch, headless_gi_mocks)
    manager = module.get_language_manager()
    manager.get_downloaded_codes.return_value = ["ita"]
    english = SimpleNamespace(code="eng", title="English")
    italian = SimpleNamespace(code="ita", title="Italian")

    assert not module.PreferencesLanguagesPage.filter_func(english, "")
    assert module.PreferencesLanguagesPage.filter_func(italian, "")


def test_activate_filter_selects_empty_or_languages_stack_child(monkeypatch, headless_gi_mocks):
    """The visible stack page reflects whether the filtered model has results."""
    _module, page, _monitor, _address, _cancellable = _make_languages_page(monkeypatch, headless_gi_mocks)

    page.model.get_n_items.return_value = 0
    page.activate_filter()
    page.views.set_visible_child_name.assert_called_with("empty_state")

    page.model.get_n_items.return_value = 2
    page.activate_filter("English")
    page.views.set_visible_child_name.assert_called_with("languages_state")


def test_stop_search_clears_query_and_restores_downloaded_filter(monkeypatch, headless_gi_mocks):
    """Stopping search clears the entry and restores the default filter."""
    _module, page, _monitor, _address, _cancellable = _make_languages_page(monkeypatch, headless_gi_mocks)
    entry = page.language_search_entry
    page.model.get_n_items.return_value = 1
    page.model.set_filter.reset_mock()

    page.on_language_search_stop(entry)

    entry.set_text.assert_called_with("")
    page.search_bar.set_search_mode.assert_called_with(False)
    page.revealer.set_reveal_child.assert_called_with(True)
    page.model.set_filter.assert_called_once()
    page.views.set_visible_child_name.assert_called_with("languages_state")


def test_language_added_event_is_idempotent(monkeypatch, headless_gi_mocks):
    """Repeated added events do not append duplicate language rows."""
    _module, page, _monitor, _address, _cancellable = _make_languages_page(monkeypatch, headless_gi_mocks)
    item = SimpleNamespace(code="ita", title="Italian")

    class ListStore:
        def __init__(self):
            self.items = []

        def __iter__(self):
            return iter(self.items)

        def append(self, value):
            self.items.append(value)

    store = ListStore()
    page.list_store = store
    import anura.widgets.preferences_languages_page as language_module

    language_manager = language_module.get_language_manager()
    language_manager.get_language_item.return_value = item
    page.search_bar.get_search_mode.return_value = False

    page.on_language_added(language_manager, "ita")
    page.on_language_added(language_manager, "ita")

    assert store.items == [item]


def test_language_removal_refreshes_default_filter(monkeypatch, headless_gi_mocks):
    """Removing a downloaded model rebuilds the visible default filter."""
    module, page, _monitor, _address, _cancellable = _make_languages_page(monkeypatch, headless_gi_mocks)
    manager = module.get_language_manager()
    manager.get_downloaded_codes.return_value = ["eng", "ita"]
    page.search_bar.get_search_mode.return_value = False
    page.model.get_n_items.return_value = 1
    page.model.set_filter.reset_mock()

    manager.get_downloaded_codes.return_value = ["eng"]
    page.on_language_removed(manager, "ita")

    page.model.set_filter.assert_called_once()
    assert not module.PreferencesLanguagesPage.filter_func(SimpleNamespace(code="ita", title="Italian"), "")
    page.views.set_visible_child_name.assert_called_with("languages_state")


def test_language_row_prunes_failed_download_refresh_idle_id(monkeypatch, headless_gi_mocks):
    """A completed failure refresh must be removed from the row's tracked sources."""
    import anura.widgets.language_row as module

    callbacks = []

    def idle_add(callback, *args):
        callbacks.append((callback, args))
        return len(callbacks)

    monkeypatch.setattr(module.GLib, "idle_add", idle_add)
    monkeypatch.setattr(module, "announce_accessible", MagicMock())

    row = module.LanguageRow()
    row._item = SimpleNamespace(code="ita", title="Italian")
    row.get_parent = MagicMock(return_value=object())
    row.update_ui = MagicMock()

    initial_callback, initial_args = callbacks.pop(0)
    initial_callback(*initial_args)
    assert row._idle_ids == set()

    row.on_download_failed(MagicMock(), "ita")

    assert len(row._idle_ids) == 1

    failure_callback, failure_args = callbacks.pop(0)
    failure_callback(*failure_args)

    assert row._idle_ids == set()
    row.update_ui.assert_called_with()
