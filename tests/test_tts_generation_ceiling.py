# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""Headless tests for the TTS generation UX ceiling (VM bug #1).

Network hangs must never wedge the UI on a mute spinner: a one-shot
'still-waiting' toast appears after _TTS_STILL_WAITING_DELAY_S, and a hard
timeout settles the request to idle after _TTS_GENERATION_TIMEOUT_S even if
the worker thread is still blocked. Both timers are superseded by real
completion (monotonic request id); stale callbacks are ignored.
"""

import sys
import types
from unittest.mock import MagicMock


def _install_stubs(monkeypatch):
    """Stub gi/loguru/atomic/settings/tts-service so the controller imports headless."""
    import anura.controllers.tts_controller as ctl_module

    scheduled: list[tuple] = []

    fake_glib = types.SimpleNamespace(
        Error=type("GError", (Exception,), {}),
        timeout_add_seconds=lambda delay, cb, *args: scheduled.append((delay, cb, args)) or len(scheduled),
        source_remove=lambda _source: scheduled.clear() or True,
    )
    fake_gobject = types.SimpleNamespace(
        GObject=type("GObject", (), {"__init__": lambda self, *a, **k: None}),
        SignalFlags=types.SimpleNamespace(RUN_LAST=0),
    )
    fake_loguru = types.SimpleNamespace(logger=MagicMock())
    fake_atomic = types.SimpleNamespace(get_atomic_manager=lambda: MagicMock())
    fake_settings = types.SimpleNamespace(get_string=lambda _key: "eng")
    fake_tts_mod = types.SimpleNamespace(
        get_tts_service=lambda: MagicMock(is_paused=lambda: False),
    )

    monkeypatch.setitem(sys.modules, "gi", types.SimpleNamespace())
    monkeypatch.setitem(sys.modules, "gi.repository", types.SimpleNamespace(GLib=fake_glib, GObject=fake_gobject))
    monkeypatch.setitem(sys.modules, "loguru", fake_loguru)
    monkeypatch.setitem(
        sys.modules, "anura.core.atomic_task_manager", types.SimpleNamespace(get_atomic_manager=fake_atomic.get_atomic_manager)
    )
    monkeypatch.setitem(sys.modules, "anura.services.settings", types.SimpleNamespace(settings=fake_settings))
    monkeypatch.setitem(sys.modules, "anura.services.tts", fake_tts_mod)
    monkeypatch.setitem(
        sys.modules,
        "anura.utils.signal_manager",
        types.SimpleNamespace(SignalManagerMixin=object),
    )
    return ctl_module, scheduled, fake_glib


def _make_controller(monkeypatch):
    ctl_module, scheduled, _fake_glib = _install_stubs(monkeypatch)
    import importlib

    importlib.reload(ctl_module)
    window = MagicMock()
    controller = ctl_module.TtsController.__new__(ctl_module.TtsController)
    controller._window = window
    controller._tts_service = MagicMock()
    controller._tts_service.is_paused.return_value = False
    controller._tts_service.get_effective_language.return_value = "en"
    controller._current_text = None
    controller._generation_seq = 0
    controller._active_generation_seq = None
    controller._waiting_source = None
    controller._timeout_source = None
    emitted: list[tuple] = []
    controller.emit = lambda *args: emitted.append(args)  # type: ignore[method-assign]
    monkeypatch.setattr(ctl_module, "get_atomic_manager", lambda: MagicMock())
    monkeypatch.setattr(ctl_module.settings, "get_string", lambda _key: "eng")
    return ctl_module, controller, emitted, scheduled


def test_still_waiting_emits_one_shot_before_timeout(monkeypatch):
    ctl_module, controller, emitted, scheduled = _make_controller(monkeypatch)
    controller.request_listen("hello world")

    assert ("state-changed", "generating") in emitted
    assert len(scheduled) == 2
    waiting_delay, waiting_cb, (waiting_seq,) = scheduled[0]
    timeout_delay, timeout_cb, (timeout_seq,) = scheduled[1]
    assert waiting_delay == ctl_module._TTS_STILL_WAITING_DELAY_S
    assert timeout_delay == ctl_module._TTS_GENERATION_TIMEOUT_S
    assert controller._active_generation_seq == waiting_seq == timeout_seq

    assert waiting_cb(waiting_seq) is False  # one-shot GLib source
    assert ("still-waiting",) in emitted
    # Timeout timer still armed: completing later via timeout goes idle.
    assert timeout_cb(timeout_seq) is False
    kinds = [e[0] for e in emitted]
    assert "error-occurred" in kinds
    assert emitted[-1] == ("state-changed", "idle")
    assert controller._active_generation_seq is None


def test_real_completion_supersedes_timers(monkeypatch):
    _ctl, controller, emitted, scheduled = _make_controller(monkeypatch)
    controller.request_listen("hello world")

    _delay, waiting_cb, (seq,) = scheduled[0]
    controller._on_generated("/tmp/fake.mp3")

    # Success path: playback is queued and state becomes 'playing'.
    assert controller._tts_service.play.call_count == 1
    controller._tts_service.play.assert_called_once_with("/tmp/fake.mp3")
    assert ("state-changed", "playing") in emitted
    # Stale timer callbacks are now no-ops driving no UI change.
    n_before = len(emitted)
    assert waiting_cb(seq) is False
    assert len(emitted) == n_before
    assert controller._active_generation_seq is None


def test_second_request_supersedes_first_timers(monkeypatch):
    _ctl, controller, emitted, scheduled = _make_controller(monkeypatch)
    controller.request_listen("first text")

    _d, waiting_cb, (first_seq,) = scheduled[0]
    controller.request_listen("second text")

    n_before = len(emitted)
    assert waiting_cb(first_seq) is False
    # Stale first-request timer must not emit 'still-waiting'.
    assert all(e != ("still-waiting",) for e in emitted[n_before:])


if __name__ == "__main__":
    import pytest

    pytest.main([__file__])
