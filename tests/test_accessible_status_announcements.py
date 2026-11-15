# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

from unittest.mock import MagicMock


def test_ocr_status_announces_only_changed_messages(headless_gi_mocks):
    from anura.widgets.welcome_page import WelcomePage

    page = WelcomePage()
    page.announce = MagicMock()

    page.set_status("Loading image")
    page.set_status("Loading image")
    page.set_status("Recognizing text")

    assert [call.args[0] for call in page.announce.call_args_list] == [
        "Loading image",
        "Recognizing text",
    ]


def test_tts_announces_state_transitions_without_idle_noise(headless_gi_mocks, monkeypatch):
    import anura.widgets.extracted_page as extracted_page

    page = MagicMock()
    page._last_announced_tts_state = None
    announcements = MagicMock()
    monkeypatch.setattr(extracted_page, "announce_accessible", announcements)

    for state in ("generating", "generating", "playing", "paused", "idle"):
        extracted_page.ExtractedPage.update_tts_state(page, state)

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

    announcements.assert_called_once_with(
        page.search_entry,
        "2 matches",
        priority=extracted_page.Gtk.AccessibleAnnouncementPriority.LOW,
    )
    assert page._search_announce_timeout_id is None
