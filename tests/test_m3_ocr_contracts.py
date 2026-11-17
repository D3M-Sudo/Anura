# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

from unittest.mock import MagicMock


def test_ocr_status_updates_visible_label_and_deduplicates_announcements(headless_gi_mocks, monkeypatch):
    import anura.widgets.welcome_page as module

    announce = MagicMock(return_value=True)
    monkeypatch.setattr(module, "announce_accessible", announce)
    page = MagicMock()
    page.drop_area_label = MagicMock()
    page._last_announced_status = None

    module.WelcomePage.set_status(page, "Loading image")
    module.WelcomePage.set_status(page, "Loading image")
    module.WelcomePage.set_status(page, "Recognizing text")
    module.WelcomePage.set_status(page, "")
    module.WelcomePage.set_status(page, "Loading image")

    assert [call.args[0] for call in page.drop_area_label.set_label.call_args_list] == [
        "Loading image", "Loading image", "Recognizing text", "", "Loading image"
    ]
    assert [call.args[1] for call in announce.call_args_list] == [
        "Loading image", "Recognizing text", "Loading image"
    ]


def test_ocr_controller_forwards_backend_status_signal(headless_gi_mocks):
    from anura.controllers.ocr_controller import OcrController

    controller = MagicMock()
    OcrController._on_status_changed(controller, MagicMock(), "Recognizing text")

    controller.emit.assert_called_once_with("status-changed", "Recognizing text")


def test_window_forwards_ocr_status_to_welcome_page(headless_gi_mocks):
    from anura.window import AnuraWindow

    window = MagicMock()
    AnuraWindow._on_ocr_status_changed(window, MagicMock(), "Recognizing text")

    window.welcome_page.set_status.assert_called_once_with("Recognizing text")


def test_window_successful_ocr_completion_finishes_operation_and_presents_result(headless_gi_mocks):
    from anura.window import AnuraWindow

    window = MagicMock()
    window._ocr_operation_id = 17

    AnuraWindow._on_extraction_completed(window, MagicMock(), "recognized text", "Smart Parse")

    window._cleanup_screenshot_state.assert_called_once_with()
    window._finish_ocr_operation.assert_called_once_with(17)
    window.extracted_page.set_extracted_text.assert_called_once_with("recognized text", "Smart Parse")


def test_stale_ocr_completion_does_not_release_current_ui_state(headless_gi_mocks):
    from anura.window import AnuraWindow

    window = MagicMock()
    window._ocr_operation_id = 18
    window._is_current_ocr_operation = lambda operation_id: operation_id == window._ocr_operation_id

    AnuraWindow._finish_ocr_operation(window, 17)

    window.welcome_page.reset_drop_area_visual_state.assert_not_called()
    window.welcome_page.hide_spinner.assert_not_called()


def test_screenshot_timeout_invalidates_operation_before_backend_cancellation(headless_gi_mocks):
    import anura.window as module

    window = MagicMock()
    window._screenshot_timeout_id = 303
    window._ocr_operation_id = 21
    window.backend.active_operation_id = 21
    window._finish_ocr_operation = MagicMock()

    def assert_generation_invalidated_before_cancel():
        assert window._ocr_operation_id == 22
        assert window.backend.active_operation_id == 22

    window.backend.cancel.side_effect = assert_generation_invalidated_before_cancel
    module.GLib.SOURCE_REMOVE = False

    result = module.AnuraWindow._on_screenshot_timeout(window)

    assert result is False
    assert window._ocr_operation_id == 22
    assert window.backend.active_operation_id == 22
    window._finish_ocr_operation.assert_called_once_with(21)
    window.backend.cancel.assert_called_once_with()
    window.present.assert_called_once_with()
    window.show_toast.assert_called_once()



def test_window_ocr_error_cleans_up_and_displays_message(headless_gi_mocks, monkeypatch):
    import anura.services.screenshot_service as screenshot_service
    from anura.window import AnuraWindow

    backend = MagicMock()
    backend.fallback_provider = object()
    monkeypatch.setattr(screenshot_service, "get_screenshot_service", lambda: backend)

    window = MagicMock()
    window._ocr_operation_id = 31

    AnuraWindow._on_ocr_error(window, MagicMock(), "OCR recognition failed")

    window._cleanup_screenshot_state.assert_called_once_with()
    window._finish_ocr_operation.assert_called_once_with(31)
    window.show_toast.assert_called_once_with("OCR recognition failed")


def test_stale_ocr_result_does_not_navigate(headless_gi_mocks):
    from anura.controllers.ocr_controller import OcrController
    from anura.controllers import ocr_controller as module

    controller = MagicMock()
    controller._window._is_current_ocr_operation.return_value = False
    result = OcrController._navigate_to_extracted_page(controller, "old-task", 30)

    assert result == module.GLib.SOURCE_REMOVE
    controller.emit.assert_not_called()
