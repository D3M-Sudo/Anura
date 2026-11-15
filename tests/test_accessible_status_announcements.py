# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

from unittest.mock import MagicMock


def test_ocr_status_announces_only_changed_messages(headless_gi_mocks):
    from anura.widgets.welcome_page import WelcomePage

    page = MagicMock()
    page.drop_area_label = MagicMock()
    page._last_announced_status = None

    WelcomePage.set_status(page, "Loading image")
    WelcomePage.set_status(page, "Loading image")
    WelcomePage.set_status(page, "Recognizing text")

    assert [call.args[0] for call in page.announce.call_args_list] == [
        "Loading image",
        "Recognizing text",
    ]


def test_tts_announces_state_transitions_without_idle_noise(headless_gi_mocks, monkeypatch):
    import anura.window as window_module

    window = MagicMock()
    window._last_announced_tts_state = "idle"
    window.navigation_view.get_visible_page.return_value = window.extracted_page
    announcements = MagicMock()
    monkeypatch.setattr(window_module, "announce_accessible", announcements)

    for state in ("generating", "generating", "playing", "paused", "idle"):
        window_module.AnuraWindow._on_tts_state_changed(window, MagicMock(), state)

    assert [call.args[1] for call in announcements.call_args_list] == [
        "Generating speech",
        "Reading text",
        "Reading paused",
    ]


def test_search_result_announcement_is_debounced(headless_gi_mocks, monkeypatch):
    import anura.widgets.extracted_page as extracted_page

    page = MagicMock()
    page.search_count_label = MagicMock()
    page.search_settings.get_search_text.return_value = "Anura"
    page.search_context.get_occurrences_count.return_value = 2
    page.search_entry = MagicMock()
    page._search_announce_timeout_id = None
    page._cancel_search_announcement = lambda: extracted_page.ExtractedPage._cancel_search_announcement(page)
    page._announce_search_results = lambda: extracted_page.ExtractedPage._announce_search_results(page)

    timeout_ids = iter((101, 102))
    timeout_add = MagicMock(side_effect=lambda _delay, _callback: next(timeout_ids))
    source_remove = MagicMock()
    announcements = MagicMock()
    monkeypatch.setattr(extracted_page.GLib, "timeout_add", timeout_add)
    monkeypatch.setattr(extracted_page.GLib, "source_remove", source_remove)
    monkeypatch.setattr(extracted_page, "announce_accessible", announcements)

    extracted_page.ExtractedPage._on_search_occurrences_changed(page, page.search_context, None)
    extracted_page.ExtractedPage._on_search_occurrences_changed(page, page.search_context, None)

    source_remove.assert_called_once_with(101)
    assert page._search_announce_timeout_id == 102

    extracted_page.ExtractedPage._announce_search_results(page)

    assert announcements.call_count == 1
    assert announcements.call_args.args[0] is page.search_entry
    assert announcements.call_args.args[1] == "2 matches"
    assert len(announcements.call_args.args) == 3
    assert page._search_announce_timeout_id is None
