# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""Waiting for scrot's output must not block the GTK main loop (#523).

``Gio.Subprocess.wait_async()`` resumes its callback in the thread-default main
context, i.e. the UI thread for a screenshot started from the window. Polling
with ``time.sleep()`` there froze the window for up to five seconds.
"""

from pathlib import Path


def _provider_source() -> str:
    return Path("anura/services/screenshot/legacy_provider.py").read_text(encoding="utf-8")


def _method_body(name: str, source: str) -> str:
    start = source.index(f"def {name}")
    rest = source[start:]
    end = rest.find("\n    def ", 1)
    return rest if end == -1 else rest[:end]


def test_on_finish_does_not_poll_synchronously():
    body = _method_body("_on_finish", _provider_source())

    assert "wait_for_file(" not in body
    assert "time.sleep(" not in body
    assert "_await_output_ready(output_path, callback)" in body


def test_polling_is_scheduled_on_the_main_loop():
    source = _provider_source()
    body = _method_body("_await_output_ready", source)

    assert "GLib.timeout_add(" in body
    assert "GLib.SOURCE_REMOVE" in body
    # The retry policy still decides how many attempts and how long to wait.
    assert "self._file_retry.retries" in body
    assert "self._file_retry.delay" in body


def test_ready_file_is_completed_once():
    body = _method_body("_await_output_ready", _provider_source())

    # Exactly one completion path for the success case and one for exhaustion.
    assert body.count("self._finish_success(") == 1
    assert body.count("callback(False, None,") == 1
