# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""History durability and the live entry limit (#540, #510).

#540: ``clear()`` emptied the in-memory cache before persisting, so a failed
write left the UI showing an empty history while ``history.json`` still held
every entry (they reappeared after a restart).

#510: ``history-limit`` was read once when the window was built, so changing the
preference had no effect until the application restarted.
"""

import json
from pathlib import Path

import pytest

from anura.services.history_service import HistoryService


def _service(tmp_path: Path, limit: int = 50) -> HistoryService:
    return HistoryService(base_dir=tmp_path / "history", limit=limit)


def _stored(tmp_path: Path) -> list[dict]:
    path = tmp_path / "history" / "history.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else []


def _failing_persist(*_args: object) -> None:
    raise OSError("read-only filesystem")


def test_failed_clear_restores_in_memory_entries(tmp_path, monkeypatch):
    service = _service(tmp_path)
    service.record("first", "eng")
    service.record("second", "ita")
    service.flush()

    monkeypatch.setattr(service, "_write_entries", _failing_persist)

    with pytest.raises(OSError):
        service.clear()

    assert [entry.text for entry in service.get_entries()] == ["second", "first"]
    # Nothing was deleted on disk either.
    assert [entry["text"] for entry in _stored(tmp_path)] == ["second", "first"]


def test_failed_clear_does_not_resurrect_after_reload(tmp_path, monkeypatch):
    service = _service(tmp_path)
    service.record("keep-me", "eng")
    service.flush()

    monkeypatch.setattr(service, "_write_entries", _failing_persist)
    with pytest.raises(OSError):
        service.clear()
    monkeypatch.undo()

    reopened = HistoryService(base_dir=tmp_path / "history")
    assert [entry.text for entry in reopened.get_entries()] == ["keep-me"]


def test_successful_clear_persists_an_empty_history(tmp_path):
    service = _service(tmp_path)
    service.record("gone", "eng")

    service.clear()

    assert service.get_entries() == []
    assert _stored(tmp_path) == []


def test_set_limit_trims_and_persists_immediately(tmp_path):
    service = _service(tmp_path, limit=10)
    for index in range(5):
        service.record(f"entry-{index}", "eng")

    service.set_limit(2)

    assert [entry.text for entry in service.get_entries()] == ["entry-4", "entry-3"]
    assert len(_stored(tmp_path)) == 2


def test_raising_the_limit_applies_without_a_restart(tmp_path):
    service = _service(tmp_path, limit=2)
    for index in range(4):
        service.record(f"e{index}", "eng")
    assert len(service.get_entries()) == 2

    service.set_limit(4)
    service.record("new", "eng")

    assert len(service.get_entries()) == 3


@pytest.mark.parametrize("value", [0, -3])
def test_set_limit_is_clamped_to_one(tmp_path, value):
    service = _service(tmp_path)

    service.set_limit(value)
    service.record("a", "eng")
    service.record("b", "eng")

    assert len(service.get_entries()) == 1


def test_clear_failure_is_reported_to_the_user():
    page = Path("anura/widgets/history_page.py").read_text(encoding="utf-8")

    assert "self._report_clear_failure()" in page
    assert 'controller.emit("error-occurred"' in page


def test_window_applies_the_limit_from_settings():
    window = Path("anura/window.py").read_text(encoding="utf-8")

    assert '"changed::history-limit"' in window
    assert "self.history_service.set_limit(limit)" in window
