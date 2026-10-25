# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""Shutdown must interrupt an in-flight model download (#531).

``executor.shutdown(wait=False, cancel_futures=True)`` only drops queued work.
The running ``session.get(..., stream=True)`` kept streaming until the request
and retry timeouts expired, and Python joins the executor workers at
interpreter shutdown, so the process could outlive the window.
"""

from pathlib import Path


def _source() -> str:
    return Path("anura/services/language/download_manager.py").read_text(encoding="utf-8")


def _method_body(name: str, source: str) -> str:
    start = source.index(f"def {name}")
    rest = source[start:]
    end = rest.find("\n    def ", 1)
    return rest if end == -1 else rest[:end]


def test_shutdown_sets_the_manager_signal_and_closes_the_response():
    body = _method_body("shutdown", _source())

    assert "self._shutdown.set()" in body
    assert "response.close()" in body
    # The signal is set before the executor is detached.
    assert body.index("self._shutdown.set()") < body.rindex("executor.shutdown(wait=False")


def test_stream_loop_checks_the_shutdown_signal():
    body = _method_body("download_begin", _source())

    assert "self._shutdown.is_set() or (cancellable and cancellable.is_cancelled())" in body
    assert "self._active_response = response" in body


def test_active_response_is_released_when_the_download_finishes():
    body = _method_body("download_begin", _source())

    assert "if self._active_response is response:" in body


def test_new_downloads_are_refused_after_shutdown():
    body = _method_body("download_begin", _source())

    assert "Skipping download" in body
