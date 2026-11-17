# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""Coalesced background persistence for the extraction history (#511).

``record()`` used to serialise the whole history (indent=2), write a temp file,
``fsync`` it and ``os.replace`` it on the GTK main thread after every
extraction, with each entry allowed to hold up to 1,000,000 characters. With a
high limit and long texts that was hundreds of MB of work per extraction, with
the UI blocked for the duration.
"""

import json
from pathlib import Path
import threading
import time

from anura.services.history_service import MAX_HISTORY_ENTRY_CHARS, HistoryService


def _stored(tmp_path: Path) -> list[dict]:
    path = tmp_path / "history.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else []


def test_record_does_not_wait_for_the_disk(tmp_path):
    service = HistoryService(base_dir=tmp_path)
    write_started = threading.Event()
    release_write = threading.Event()
    original_write = service._write_entries

    def slow_write(entries):
        write_started.set()
        release_write.wait(timeout=5)
        original_write(entries)

    service._write_entries = slow_write  # type: ignore[method-assign]

    service.record("first", "eng")
    assert write_started.wait(timeout=5), "the background writer never started"

    started = time.monotonic()
    service.record("second", "eng")
    elapsed = time.monotonic() - started

    assert elapsed < 0.5, f"record() blocked for {elapsed:.2f}s on a busy writer"
    assert [entry.text for entry in service.get_entries()] == ["second", "first"]

    release_write.set()
    service.close()


def test_rapid_records_are_coalesced(tmp_path):
    service = HistoryService(base_dir=tmp_path)
    writes: list[int] = []
    gate = threading.Event()
    original_write = service._write_entries

    def counting_write(entries):
        writes.append(len(entries))
        gate.wait(timeout=5)
        original_write(entries)

    service._write_entries = counting_write  # type: ignore[method-assign]

    for index in range(20):
        service.record(f"entry-{index}", "eng")

    gate.set()
    assert service.flush() is True

    assert len(writes) <= 3, f"expected coalesced writes, got {writes}"
    assert [entry["text"] for entry in _stored(tmp_path)][:2] == ["entry-19", "entry-18"]
    assert len(_stored(tmp_path)) == 20
    service.close()


def test_entry_text_is_capped(tmp_path):
    service = HistoryService(base_dir=tmp_path)
    service.record("x" * (MAX_HISTORY_ENTRY_CHARS + 1_000), "eng")

    entries = service.get_entries()

    assert len(entries) == 1
    assert len(entries[0].text) == MAX_HISTORY_ENTRY_CHARS
    service.close()


def test_close_flushes_pending_entries(tmp_path):
    service = HistoryService(base_dir=tmp_path)
    service.record("last", "eng")

    service.close()

    assert [entry["text"] for entry in _stored(tmp_path)] == ["last"]


def test_close_is_idempotent(tmp_path):
    service = HistoryService(base_dir=tmp_path)
    service.record("once", "eng")

    service.close()
    service.close()

    assert [entry["text"] for entry in _stored(tmp_path)] == ["once"]


def test_clear_discards_a_pending_record(tmp_path):
    service = HistoryService(base_dir=tmp_path)
    service.record("pending", "eng")

    service.clear()
    assert service.flush() is True

    assert service.get_entries() == []
    assert _stored(tmp_path) == []
    service.close()


def test_synchronous_mode_persists_immediately(tmp_path):
    service = HistoryService(base_dir=tmp_path, persist_async=False)
    service.record("sync", "eng")

    assert [entry["text"] for entry in _stored(tmp_path)] == ["sync"]
