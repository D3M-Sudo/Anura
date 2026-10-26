# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""Shutdown must not wait for a blocking generation (#506).

``do_shutdown()`` called ``ThreadPoolExecutor.shutdown(wait=True)``, so it
blocked until the TTS generation finished its sequential gTTS requests (up to
~100 requests of 30 s timeout each). Even with ``wait=False`` CPython joins the
pool workers at interpreter exit, so the process could outlive the window.
"""

from pathlib import Path


def _manager_source() -> str:
    return Path("anura/core/atomic_task_manager.py").read_text(encoding="utf-8")


def _method_body(name: str, source: str) -> str:
    start = source.index(f"def {name}")
    rest = source[start:]
    end = rest.find("\n    def ", 1)
    return rest if end == -1 else rest[:end]


def _code_only(body: str) -> str:
    """Strip the docstring so prose about a removed call is not matched."""
    start = body.find('"""')
    end = body.find('"""', start + 3)
    if start == -1 or end == -1:
        return body
    return body[:start] + body[end + 3 :]


def test_tts_runs_on_a_daemon_thread():
    daemon_body = _method_body("execute_daemon", _manager_source())
    tts = Path("anura/controllers/tts_controller.py").read_text(encoding="utf-8")

    assert "daemon=True" in daemon_body
    assert "execute_daemon(" in tts
    # The pooled path would be joined at interpreter exit.
    assert "get_atomic_manager().execute(" not in tts


def test_shutdown_cancels_lanes_without_waiting():
    body = _code_only(_method_body("shutdown", _manager_source()))

    assert "self.cancel_all_lanes()" in body
    assert "thread_executor.shutdown(wait=False, cancel_futures=True)" in body
    assert "thread_executor.shutdown(wait=True" not in body
