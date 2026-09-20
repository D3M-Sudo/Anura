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
from unittest.mock import MagicMock


def _get_handler(name: str):
    from anura.window import AnuraWindow

    return getattr(AnuraWindow, name)


def _make_self():
    welcome = SimpleNamespace(show_spinner=MagicMock(), reset_drop_area_state=MagicMock())
    return SimpleNamespace(
        welcome_page=welcome,
        extracted_page=SimpleNamespace(set_extracted_text=MagicMock()),
        _cleanup_screenshot_state=MagicMock(),
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

    self_fake.welcome_page.reset_drop_area_state.assert_called_once_with()
    self_fake.extracted_page.set_extracted_text.assert_called_once_with("text", "Name")


def test_ocr_error_hides_spinner():
    """OCR error path resets the drop area, which stops the spinner."""
    self_fake = _make_self()

    # Empty message -> early return after the UI reset (no dialog/toast branch).
    _get_handler("_on_ocr_error")(self_fake, MagicMock(), "")

    self_fake.welcome_page.reset_drop_area_state.assert_called_once_with()
    self_fake.show_toast.assert_not_called()


if __name__ == "__main__":
    import pytest

    pytest.main([__file__])
