# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""Headless tests: the processing spinner is shown for screenshot OCR (VM bug #3).

Since the window restores on capture-finished (bug #5/#8) the OCR wait is
visible again, so the screenshot path must show the spinner like
``process_file()`` and the clipboard-paste flow already do. The spinner must
stay hidden when a capture hands nothing to OCR, and must be hidden again on
both OCR success and OCR error.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch


def _get_handler(name: str):
    from anura.window import AnuraWindow

    return getattr(AnuraWindow, name)


def _make_self():
    welcome = SimpleNamespace(
        show_spinner=MagicMock(),
        reset_drop_area_state=MagicMock(),
        reset_drop_area_visual_state=MagicMock(),
        hide_spinner=MagicMock(),
    )
    return SimpleNamespace(
        welcome_page=welcome,
        extracted_page=SimpleNamespace(set_extracted_text=MagicMock()),
        _cleanup_screenshot_state=MagicMock(),
        _ocr_operation_id=1,
        _finish_ocr_operation=MagicMock(),
        show_toast=MagicMock(),
    )


def test_successful_capture_shows_spinner_while_ocr_runs():
    """capture-finished(True) -> spinner visible, window restored."""
    self_fake = _make_self()

    _get_handler("_on_capture_finished")(self_fake, MagicMock(), True)

    self_fake.welcome_page.show_spinner.assert_called_once_with()
    self_fake._cleanup_screenshot_state.assert_called_once_with()


def test_failed_capture_does_not_show_spinner():
    """capture-finished(False) hands nothing to OCR -> no spinner to hide later."""
    self_fake = _make_self()

    _get_handler("_on_capture_finished")(self_fake, MagicMock(), False)

    self_fake.welcome_page.show_spinner.assert_not_called()
    self_fake._cleanup_screenshot_state.assert_called_once_with()


def test_extraction_completed_hides_spinner():
    """OCR success path resets the drop area, which stops the spinner."""
    self_fake = _make_self()

    _get_handler("_on_extraction_completed")(self_fake, MagicMock(), "text", "Name")

    self_fake._finish_ocr_operation.assert_called_once_with(1)
    self_fake.extracted_page.set_extracted_text.assert_called_once_with("text", "Name")


def test_ocr_error_hides_spinner():
    """OCR error path resets the drop area, which stops the spinner."""
    self_fake = _make_self()

    # Empty message -> early return after the UI reset (no dialog/toast branch).
    _get_handler("_on_ocr_error")(self_fake, MagicMock(), "")

    self_fake._finish_ocr_operation.assert_called_once_with(1)
    self_fake.show_toast.assert_not_called()


def test_stale_operation_cannot_hide_current_spinner():
    """A completion from an older request must not reset the current spinner."""
    self_fake = _make_self()
    self_fake._ocr_operation_id = 2
    self_fake._is_current_ocr_operation = lambda operation_id: operation_id == self_fake._ocr_operation_id

    _get_handler("_finish_ocr_operation")(self_fake, 1)

    self_fake.welcome_page.reset_drop_area_visual_state.assert_not_called()
    self_fake.welcome_page.hide_spinner.assert_not_called()


def test_current_operation_resets_spinner_and_drop_visuals():
    self_fake = _make_self()
    self_fake._ocr_operation_id = 2
    self_fake._is_current_ocr_operation = lambda operation_id: operation_id == self_fake._ocr_operation_id

    _get_handler("_finish_ocr_operation")(self_fake, 2)

    self_fake.welcome_page.reset_drop_area_visual_state.assert_called_once_with()
    self_fake.welcome_page.hide_spinner.assert_called_once_with()


def test_new_operation_is_published_before_previous_capture_is_cancelled():
    """Synchronous cancellation callbacks from the previous capture are stale immediately."""
    from anura.window import AnuraWindow

    backend = SimpleNamespace(active_operation_id=1)
    backend.cancel = MagicMock(
        side_effect=lambda: setattr(backend, "observed_operation_id", backend.active_operation_id)
    )
    welcome = SimpleNamespace(show_spinner=MagicMock(), cancel_pending_drop=MagicMock())
    window = SimpleNamespace(
        _ocr_operation_id=1,
        _screenshot_timeout_id=None,
        backend=backend,
        welcome_page=welcome,
    )

    with patch("anura.window.get_atomic_manager") as manager:
        operation_id = AnuraWindow._begin_ocr_operation(window)

    assert operation_id == 2
    assert backend.observed_operation_id == 2
    assert backend.active_operation_id == 2
    manager.return_value.cancel_lane.assert_called_once()
    welcome.show_spinner.assert_called_once_with()


if __name__ == "__main__":
    import pytest

    pytest.main([__file__])
