# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""Headless tests: capture-finished settles exactly when capture settles.

The window restores itself on capture-finished (before OCR runs), so the
GUI is no longer hidden for the whole OCR duration (bug #5/#8).

These tests run in ANURA_CI_TEST_MODE=1 — gi is stubbed by conftest, and
the service is exercised via __new__ + MagicMock providers so no real GTK
or GObject runtime is needed. No pytest.importorskip: gi is always
importable here (real or stubbed).
"""

from unittest.mock import MagicMock, patch

from anura.services.screenshot_service import ScreenshotService


def _make_service():
    with patch("anura.services.screenshot_service._configure_tesseract_path"):
        s = ScreenshotService.__new__(ScreenshotService)
        s.provider = MagicMock()
        s.fallback_provider = MagicMock()
        s._is_capturing = False
        s._current_task_id = None
        s._emit_decode_error = MagicMock()
        s._log_portal_environment = MagicMock()
        s._emit_portal_failure = MagicMock()
        s._emit_capture_finished = MagicMock()
        return s


def test_capture_success_emits_capture_finished_true():
    """URI handed to the OCR pipeline -> capture-finished(True)."""
    svc = _make_service()

    def _mock_capture(lang, copy, callback):
        callback(True, "file:///tmp/shot.png", None)

    svc.provider.capture = MagicMock(side_effect=_mock_capture)

    # The background OCR hand-off must not run in this headless test.
    with patch("anura.services.screenshot_service.get_atomic_manager"):
        ScreenshotService.capture(svc, "eng", False)

    svc._emit_capture_finished.assert_called_once_with(True)


def test_user_cancel_emits_capture_finished_false_no_fallback():
    """User cancellation (error=None) settles capture without fallback."""
    svc = _make_service()

    def _mock_capture(lang, copy, callback):
        callback(False, None, None)

    svc.provider.capture = MagicMock(side_effect=_mock_capture)
    ScreenshotService.capture(svc, "eng", False)

    svc.fallback_provider.capture.assert_not_called()
    svc._emit_capture_finished.assert_called_once_with(False)


def test_fallback_failure_emits_capture_finished_false_once():
    """Primary error then fallback error -> exactly one capture-finished(False)."""
    svc = _make_service()

    def _mock_capture(lang, copy, callback):
        callback(False, None, "portal boom")

    def _mock_fallback(lang, copy, callback):
        callback(False, None, "scrot boom")

    svc.provider.capture = MagicMock(side_effect=_mock_capture)
    svc.fallback_provider.capture = MagicMock(side_effect=_mock_fallback)
    ScreenshotService.capture(svc, "eng", False)

    assert svc.provider.capture.call_count == 1
    assert svc.fallback_provider.capture.call_count == 1
    svc._emit_capture_finished.assert_called_once_with(False)


def test_fallback_started_does_not_emit_yet():
    """While the fallback is in flight, capture has NOT settled -> no emit yet."""
    svc = _make_service()

    def _mock_capture(lang, copy, callback):
        callback(False, None, "portal boom")

    svc.provider.capture = MagicMock(side_effect=_mock_capture)
    # Fallback swallows the callback: capture never settles in this scenario.
    svc.fallback_provider.capture = MagicMock(side_effect=lambda *a: None)
    ScreenshotService.capture(svc, "eng", False)

    svc._emit_capture_finished.assert_not_called()
