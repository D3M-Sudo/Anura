# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""Every task kind must use its own lane (#507).

The behavioural tests live in ``tests/test_gi_atomic_task_lanes.py`` (they need
PyGObject); this headless test keeps the call sites grouped by lane, which is
what prevents an OCR task from cancelling a TTS generation.
"""

from pathlib import Path


def _source(relative: str) -> str:
    return Path(relative).read_text(encoding="utf-8")


def test_ocr_tasks_use_the_ocr_lane():
    window = _source("anura/window.py")
    screenshot = _source("anura/services/screenshot_service.py")

    # Two synchronous decode paths in the window.
    assert window.count("lane=OCR_LANE") == 2
    # The portal follow-up and the isolated pipeline.
    assert screenshot.count("lane=OCR_LANE") == 2


def test_file_cleanup_uses_its_own_lane():
    assert "lane=CLEANUP_LANE" in _source("anura/services/screenshot_service.py")


def test_tts_uses_its_own_lane_and_reports_supersession():
    tts = _source("anura/controllers/tts_controller.py")

    assert "lane=TTS_LANE" in tts
    assert "on_superseded=" in tts
    assert "def _on_generation_superseded" in tts


def test_broken_pool_teardown_is_guarded_by_identity():
    manager = _source("anura/core/atomic_task_manager.py")

    assert "def _handle_broken_pool" in manager
    assert "if self._process_executor is not failed_executor:" in manager
    assert "self._handle_broken_pool(executor)" in manager


def test_manager_exposes_the_lane_api():
    manager = _source("anura/core/atomic_task_manager.py")

    assert "DEFAULT_LANE = " in manager
    assert "def _begin_lane_locked" in manager
    assert "on_superseded" in manager
