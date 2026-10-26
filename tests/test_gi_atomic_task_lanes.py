# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""Per-lane task slots (#507).

The manager used to have a single current-task slot, so any new task cancelled
the previous one regardless of its kind: a screenshot invalidated a TTS
generation, and the post-OCR `unlink` invalidated the OCR itself. Results of the
"losing" task were dropped silently, leaving the TTS controller to wait for its
watchdog and show a misleading timeout message.
"""

import threading
from unittest.mock import MagicMock

import pytest

pytest.importorskip("gi")

from gi.repository import GLib

from anura.core.atomic_task_manager import (
    CLEANUP_LANE,
    DEFAULT_LANE,
    OCR_LANE,
    TTS_LANE,
    AtomicTaskManager,
    AtomicTaskResult,
)


@pytest.fixture
def manager():
    manager = AtomicTaskManager()
    yield manager
    manager.shutdown()


def test_lanes_do_not_invalidate_each_other(manager):
    release = threading.Event()

    def blocking():
        release.wait(timeout=5)

    tts_id = manager.execute(blocking, lane=TTS_LANE)
    ocr_id = manager.execute(blocking, lane=OCR_LANE)

    assert manager.is_cancelled(tts_id) is False
    assert manager.is_cancelled(ocr_id) is False
    assert manager._current_lane_task_id(TTS_LANE) == tts_id
    assert manager._current_lane_task_id(OCR_LANE) == ocr_id

    release.set()


def test_cleanup_does_not_cancel_an_ocr_task(manager):
    release = threading.Event()

    def blocking():
        release.wait(timeout=5)

    ocr_id = manager.execute(blocking, lane=OCR_LANE)
    manager.execute(lambda: None, lane=CLEANUP_LANE)

    assert manager.is_cancelled(ocr_id) is False

    release.set()


def test_same_lane_supersedes_only_the_previous_task(manager):
    first = manager.execute(lambda: None, lane=OCR_LANE)
    second = manager.execute(lambda: None, lane=OCR_LANE)

    assert manager.is_cancelled(first) is True
    assert manager.is_cancelled(second) is False


def test_unknown_task_id_is_cancelled(manager):
    assert manager.is_cancelled("not-a-task") is True


def test_default_lane_keeps_the_historical_behaviour(manager):
    first = manager.execute(lambda: None)
    assert manager._current_task_id == first

    second = manager.execute(lambda: None)
    assert manager._current_task_id == second
    assert manager.is_cancelled(first) is True


def test_superseded_success_reports_instead_of_dropping(manager):
    manager.execute(lambda: None, lane=OCR_LANE)
    stale = AtomicTaskResult(task_id="stale-id", lane=OCR_LANE, data="dropped")
    callback = MagicMock()
    on_superseded = MagicMock()

    assert manager._handle_success(stale, callback, on_superseded) == GLib.SOURCE_REMOVE

    callback.assert_not_called()
    on_superseded.assert_called_once_with("stale-id")


def test_current_success_reaches_the_callback(manager):
    task_id = manager.execute(lambda: None, lane=DEFAULT_LANE)
    result = AtomicTaskResult(task_id=task_id, lane=DEFAULT_LANE, data="ok")
    callback = MagicMock()

    manager._handle_success(result, callback)

    callback.assert_called_once_with("ok")


def test_superseded_error_does_not_reach_the_errorback(manager):
    manager.execute(lambda: None, lane=OCR_LANE)
    stale = AtomicTaskResult(task_id="stale-id", lane=OCR_LANE, error=RuntimeError("boom"))
    errorback = MagicMock()
    on_superseded = MagicMock()

    manager._handle_error(stale, errorback, on_superseded)

    errorback.assert_not_called()
    on_superseded.assert_called_once_with("stale-id")


def test_cancel_lane_discards_a_late_result(manager):
    """#508: cancelling a lane (watchdog) must drop the in-flight result."""
    release = threading.Event()

    def blocking():
        release.wait(timeout=5)

    task_id = manager.execute(blocking, lane=TTS_LANE)
    manager.cancel_lane(TTS_LANE)

    assert manager.is_cancelled(task_id) is True

    late = AtomicTaskResult(task_id=task_id, lane=TTS_LANE, data="late")
    callback, on_superseded = MagicMock(), MagicMock()
    manager._handle_success(late, callback, on_superseded)

    callback.assert_not_called()
    on_superseded.assert_called_once_with(task_id)

    release.set()


def test_current_error_reaches_the_errorback(manager):
    task_id = manager.execute(lambda: None, lane=DEFAULT_LANE)
    result = AtomicTaskResult(task_id=task_id, lane=DEFAULT_LANE, error=RuntimeError("boom"))
    errorback = MagicMock()

    manager._handle_error(result, errorback)

    errorback.assert_called_once()
