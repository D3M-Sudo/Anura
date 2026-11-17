# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

from types import SimpleNamespace
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


def test_ocr_status_reannounces_after_status_clear(headless_gi_mocks):
    from anura.widgets.welcome_page import WelcomePage

    page = MagicMock()
    page.drop_area_label = MagicMock()
    page._last_announced_status = None

    WelcomePage.set_status(page, "Loading image")
    WelcomePage.set_status(page, "")
    WelcomePage.set_status(page, "Loading image")

    assert [call.args[0] for call in page.announce.call_args_list] == [
        "Loading image",
        "Loading image",
    ]


def _make_extracted_search_page(extracted_page, *, count: int, search_text: str = "Anura"):
    page = MagicMock()
    page.search_count_label = MagicMock()
    page.search_settings.get_search_text.return_value = search_text
    page.search_context.get_occurrences_count.return_value = count
    page.search_entry = MagicMock()
    page._search_announce_timeout_id = None
    page._cancel_search_announcement = lambda: extracted_page.ExtractedPage._cancel_search_announcement(page)
    page._announce_search_results = lambda: extracted_page.ExtractedPage._announce_search_results(page)
    return page


def test_search_in_progress_updates_visible_and_accessible_labels(headless_gi_mocks, monkeypatch):
    import anura.widgets.extracted_page as extracted_page

    page = _make_extracted_search_page(extracted_page, count=-1)
    timeout_add = MagicMock()
    monkeypatch.setattr(extracted_page.GLib, "timeout_add", timeout_add)

    extracted_page.ExtractedPage._on_search_occurrences_changed(page, page.search_context, None)

    page.search_count_label.set_text.assert_called_once_with("Searching…")
    assert page.search_entry.update_property.call_args.args[1] == ["Search extracted text (Searching…)"]
    timeout_add.assert_not_called()


def test_single_search_result_is_announced_after_400ms_with_low_priority(headless_gi_mocks, monkeypatch):
    import anura.widgets.extracted_page as extracted_page

    page = _make_extracted_search_page(extracted_page, count=1)
    timeout_add = MagicMock(return_value=303)
    announcements = MagicMock()
    low_priority = object()
    monkeypatch.setattr(extracted_page.Gtk, "AccessibleAnnouncementPriority", SimpleNamespace(LOW=low_priority))
    monkeypatch.setattr(extracted_page.GLib, "timeout_add", timeout_add)
    monkeypatch.setattr(extracted_page, "announce_accessible", announcements)

    extracted_page.ExtractedPage._on_search_occurrences_changed(page, page.search_context, None)

    page.search_count_label.set_text.assert_called_once_with("1 match")
    assert page.search_entry.update_property.call_args.args[1] == ["Search extracted text (1 match)"]
    timeout_add.assert_called_once_with(400, page._announce_search_results)

    extracted_page.ExtractedPage._announce_search_results(page)

    assert announcements.call_args.args == (page.search_entry, "1 match", low_priority)


def test_zero_search_results_are_announced_as_no_matches(headless_gi_mocks, monkeypatch):
    import anura.widgets.extracted_page as extracted_page

    page = _make_extracted_search_page(extracted_page, count=0)
    low_priority = object()
    monkeypatch.setattr(extracted_page.Gtk, "AccessibleAnnouncementPriority", SimpleNamespace(LOW=low_priority))
    monkeypatch.setattr(extracted_page.GLib, "timeout_add", MagicMock(return_value=404))
    announcements = MagicMock()
    monkeypatch.setattr(extracted_page, "announce_accessible", announcements)

    extracted_page.ExtractedPage._on_search_occurrences_changed(page, page.search_context, None)

    page.search_count_label.set_text.assert_called_once_with("No matches")
    assert page.search_entry.update_property.call_args.args[1] == ["Search extracted text (No matches)"]

    extracted_page.ExtractedPage._announce_search_results(page)

    assert announcements.call_args.args == (page.search_entry, "No matches", low_priority)


def test_clearing_search_restores_accessible_label_and_cancels_pending_announcement(headless_gi_mocks, monkeypatch):
    import anura.widgets.extracted_page as extracted_page

    page = _make_extracted_search_page(extracted_page, count=2)
    page._search_announce_timeout_id = 505
    entry = page.search_entry
    entry.get_text.return_value = ""
    source_remove = MagicMock()
    monkeypatch.setattr(extracted_page.GLib, "source_remove", source_remove)

    extracted_page.ExtractedPage._on_search_text_changed(page, entry)

    source_remove.assert_called_once_with(505)
    assert page._search_announce_timeout_id is None
    page.search_settings.set_search_text.assert_called_once_with(None)
    page.search_context.set_highlight.assert_called_once_with(False)
    page.search_count_label.set_text.assert_called_once_with("")
    assert entry.update_property.call_args.args[1] == ["Search extracted text"]
