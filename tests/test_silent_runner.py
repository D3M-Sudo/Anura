# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""Tests for SilentRunner (headless `--silent` OCR mode)."""

import faulthandler
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

pytest.importorskip("gi")

pytestmark = pytest.mark.gtk

from anura.core.silent_runner import SilentRunner


class _StubApp:
    """Minimal GApplication stand-in used by SilentRunner."""

    def __init__(self, success: bool = True, text: str = "recognised text", error: str | None = None):
        self._result = (success, text, error, None, None)
        self.holds = 0

    def _decode_image_synchronously(self, _file_path: str):
        return self._result

    def hold(self):
        self.holds += 1

    def release(self):
        self.holds -= 1


@pytest.fixture
def fake_clipboard():
    service = MagicMock()
    with (
        patch("anura.core.silent_runner.get_clipboard_service", return_value=service),
        patch(
            "anura.services.result_dispatcher.get_result_dispatcher",
            return_value=MagicMock(dispatch=lambda text, _result: SimpleNamespace(text=text)),
        ),
    ):
        yield service


def _run_with_hang_guard(runner: SilentRunner) -> int:
    """Abort quickly if a GLib main loop regresses into an uninterruptible hang."""
    faulthandler.dump_traceback_later(20, exit=True)
    try:
        return runner.run()
    finally:
        faulthandler.cancel_dump_traceback_later()


def test_silent_ocr_runs_on_the_real_glib_main_context_and_defers_clipboard_release(fake_clipboard):
    """OCR succeeds, then the application remains held for asynchronous clipboard serving."""
    app = _StubApp()
    runner = SilentRunner(app, "/tmp/image.png")

    assert _run_with_hang_guard(runner) == 0
    fake_clipboard.set.assert_called_once_with("recognised text")
    fake_clipboard.keep_available_async.assert_called_once()
    args = fake_clipboard.keep_available_async.call_args.args
    assert args[0] == 30
    assert args[2] == runner.interrupted.is_set
    assert app.holds == 1
    args[1]("stored")
    assert app.holds == 0


def test_silent_ocr_failure_exits_without_holding_the_application(fake_clipboard):
    app = _StubApp(success=False, text="", error="no tesseract")
    runner = SilentRunner(app, "/tmp/image.png")

    assert _run_with_hang_guard(runner) == 1
    fake_clipboard.set.assert_not_called()
    fake_clipboard.keep_available_async.assert_not_called()
    assert app.holds == 0


def test_clipboard_timeout_releases_the_application_after_successful_ocr(fake_clipboard):
    app = _StubApp()
    runner = SilentRunner(app, "/tmp/image.png")

    assert _run_with_hang_guard(runner) == 0
    assert app.holds == 1
    callback = fake_clipboard.keep_available_async.call_args.args[1]
    callback("timeout")
    assert app.holds == 0


def test_signal_while_serving_clipboard_releases_the_application(fake_clipboard):
    app = _StubApp()
    runner = SilentRunner(app, "/tmp/image.png")

    assert _run_with_hang_guard(runner) == 0
    assert app.holds == 1
    should_stop = fake_clipboard.keep_available_async.call_args.args[2]
    runner.interrupted.set()
    assert should_stop() is True
    callback = fake_clipboard.keep_available_async.call_args.args[1]
    callback("interrupted")
    assert app.holds == 0
