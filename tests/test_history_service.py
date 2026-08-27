# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

from unittest.mock import MagicMock

import pytest

from anura.services.history_service import HistoryService


@pytest.fixture(autouse=True)
def isolate_state_env(monkeypatch, tmp_path):
    """Isolate history tests from real user state home."""
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))


def test_history_service_initial_empty(isolate_env, headless_gi_mocks):
    """Verify that history starts empty if no file exists."""
    service = HistoryService()
    assert len(service.get_sessions()) == 0


def test_history_service_add_session(isolate_env, headless_gi_mocks):
    """Verify that add_session correctly appends a session to history."""
    service = HistoryService()
    # Mock settings to enable history
    service.settings = MagicMock()
    service.settings.get_boolean.return_value = True
    service.settings.get_int.return_value = 50

    service.add_session(
        text="Hello world!",
        language="eng",
        transformer_name="Paragraph",
        thumbnail_base64="fake-b64-png"
    )

    sessions = service.get_sessions()
    assert len(sessions) == 1
    assert sessions[0].text == "Hello world!"
    assert sessions[0].language == "eng"
    assert sessions[0].transformer_name == "Paragraph"
    assert sessions[0].thumbnail_base64 == "fake-b64-png"


def test_history_service_limit_and_disable(isolate_env, headless_gi_mocks):
    """Verify that history-limit truncates old sessions, and history-enabled=false disables additions."""
    service = HistoryService()
    service.settings = MagicMock()
    service.settings.get_boolean.return_value = True
    service.settings.get_int.return_value = 2  # limit of 2

    # Add 3 sessions
    service.add_session("text1")
    service.add_session("text2")
    service.add_session("text3")

    sessions = service.get_sessions()
    assert len(sessions) == 2
    # Most recent first: text3 should be at 0, text2 at 1
    assert sessions[0].text == "text3"
    assert sessions[1].text == "text2"

    # Disable history and try to add
    service.settings.get_boolean.return_value = False
    service.add_session("text4")

    # Length should still be 2 (text4 ignored)
    assert len(service.get_sessions()) == 2


def test_history_service_delete_and_clear(isolate_env, headless_gi_mocks):
    """Verify that we can delete a session by ID and clear all history."""
    service = HistoryService()
    service.settings = MagicMock()
    service.settings.get_boolean.return_value = True
    service.settings.get_int.return_value = 50

    service.add_session("text1")
    service.add_session("text2")

    sessions = service.get_sessions()
    assert len(sessions) == 2
    id_to_delete = sessions[0].id

    service.delete_session(id_to_delete)
    sessions = service.get_sessions()
    assert len(sessions) == 1
    assert sessions[0].id != id_to_delete

    # Clear all
    service.clear_history()
    assert len(service.get_sessions()) == 0


def test_history_service_corruption_recovery(isolate_env, headless_gi_mocks):
    """Verify that history gracefully recovers from corrupted JSON files."""
    service = HistoryService()
    service._history_dir.mkdir(parents=True, exist_ok=True)

    # Write malformed JSON
    with open(service._history_file, "w") as f:
        f.write("invalid json string {")

    # Reload history
    service.load_history()
    assert len(service.get_sessions()) == 0

    # Verify that a backup file was created
    corrupt_files = list(service._history_dir.glob("history.corrupt.*.json"))
    assert len(corrupt_files) == 1
