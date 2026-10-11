# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""Tests for SilentRunner (headless `--silent` OCR mode).

The only other test that mentions SilentRunner replaces the class with a mock, so
nothing exercised its real code path.
"""

import faulthandler

import pytest

pytest.importorskip("gi")

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from anura.core.silent_runner import SilentRunner


class _StubApp:
    """Minimal stand-in for AnuraApplication used by SilentRunner."""

    def __init__(self, success: bool = True, text: str = "recognised text", error: str | None = None):
        self._result = (success, text, error, None, None)

    def _decode_image_synchronously(self, _file_path: str):
        return self._result


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
    """Run the runner; if its main loop never ends, dump the stack and abort quickly.

    pytest-timeout cannot interrupt a blocked GLib main loop, so a regression would
    otherwise hang the whole test session instead of failing.
    """
    faulthandler.dump_traceback_later(20, exit=True)
    try:
        return runner.run()
    finally:
        faulthandler.cancel_dump_traceback_later()


def test_silent_ocr_runs_on_the_real_glib_main_context(fake_clipboard):
    """Regression: the silent runner never ran (and then hung forever).

    Two defects on the same loop, both invisible to the mocked CLI test:
    - it called GLib.MainContext.push()/pop(), which do not exist (PyGObject only
      exposes push_thread_default()/pop_thread_default()): AttributeError;
    - its GSource callbacks took no arguments, but PyGObject calls a source callback
      with its user_data (None), so every callback raised TypeError, the OCR callback
      never ran and not even the 60 s timeout could end the loop.
    """
    runner = SilentRunner(_StubApp(), "/tmp/image.png")

    assert _run_with_hang_guard(runner) == 0

    fake_clipboard.set.assert_called_once_with("recognised text")


def test_silent_ocr_failure_exits_with_error_code(fake_clipboard):
    runner = SilentRunner(_StubApp(success=False, text="", error="no tesseract"), "/tmp/image.png")

    assert _run_with_hang_guard(runner) == 1

    fake_clipboard.set.assert_not_called()
