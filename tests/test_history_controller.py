# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""Headless tests for HistoryController (History V2 copy action).

Follows the repository's headless convention: the controller module is
imported inside the test bodies, after `headless_gi_mocks` is active.
"""

from unittest.mock import MagicMock

import pytest


def _make_controller(monkeypatch, clipboard):
    import anura.controllers.history_controller as module

    monkeypatch.setattr(module, "get_clipboard_service", lambda: clipboard)
    window = MagicMock()
    controller = module.HistoryController(window)
    controller.emit = MagicMock()
    return controller, window


def test_copy_hands_text_to_clipboard_and_emits_copied(headless_gi_mocks, monkeypatch):
    clipboard = MagicMock()
    controller, _window = _make_controller(monkeypatch, clipboard)

    assert controller.copy_entry_text("hello") is True

    clipboard.set.assert_called_once_with("hello")
    controller.emit.assert_called_once_with("copied")


def test_empty_text_reports_error_without_touching_clipboard(headless_gi_mocks, monkeypatch):
    clipboard = MagicMock()
    controller, _window = _make_controller(monkeypatch, clipboard)

    assert controller.copy_entry_text("") is False

    clipboard.set.assert_not_called()
    controller.emit.assert_called_once_with("error-occurred", "No text to copy")


def test_clipboard_unavailable_reports_error_and_no_success(headless_gi_mocks, monkeypatch):
    clipboard = MagicMock()
    clipboard.set.side_effect = RuntimeError("No display available.")
    controller, _window = _make_controller(monkeypatch, clipboard)

    assert controller.copy_entry_text("hello") is False

    controller.emit.assert_called_once_with("error-occurred", "Failed to copy text to clipboard")


def test_unexpected_errors_are_not_swallowed(headless_gi_mocks, monkeypatch):
    """A bug (not a documented clipboard failure) must surface, not be silenced."""
    clipboard = MagicMock()
    clipboard.set.side_effect = ValueError("bug")
    controller, _window = _make_controller(monkeypatch, clipboard)

    with pytest.raises(ValueError, match="bug"):
        controller.copy_entry_text("hello")

    controller.emit.assert_not_called()


def test_open_entry_exports_in_background_and_emits_file_ready(headless_gi_mocks, monkeypatch, tmp_path):
    from pathlib import Path
    import anura.controllers.history_controller as module

    manager = MagicMock()
    monkeypatch.setattr(module, "get_atomic_manager", lambda: manager)
    monkeypatch.setattr(module, "write_export_file", lambda text: tmp_path / "history.txt")
    controller, _window = _make_controller(monkeypatch, MagicMock())

    assert controller.open_entry_in_external_editor("stored OCR text") is True
    call = manager.execute_daemon.call_args
    assert call.args[0] is module.write_export_file
    assert call.args[1] == ("stored OCR text",)
    assert call.kwargs["lane"] == module.EXPORT_LANE
    call.kwargs["callback"](Path(tmp_path / "history.txt"))
    controller.emit.assert_called_with("editor-file-ready", str(tmp_path / "history.txt"))


def test_open_entry_rejects_empty_text_without_scheduling(headless_gi_mocks, monkeypatch):
    import anura.controllers.history_controller as module
    manager = MagicMock()
    monkeypatch.setattr(module, "get_atomic_manager", lambda: manager)
    controller, _window = _make_controller(monkeypatch, MagicMock())

    assert controller.open_entry_in_external_editor("") is False
    manager.execute_daemon.assert_not_called()
    controller.emit.assert_called_once_with("error-occurred", "No text to open in external editor")


def test_export_failure_reports_existing_editor_error(headless_gi_mocks, monkeypatch):
    import anura.controllers.history_controller as module
    manager = MagicMock()
    monkeypatch.setattr(module, "get_atomic_manager", lambda: manager)
    controller, _window = _make_controller(monkeypatch, MagicMock())
    controller.open_entry_in_external_editor("stored OCR text")
    manager.execute_daemon.call_args.kwargs["errorback"](OSError("disk full"), "traceback")
    controller.emit.assert_called_with("error-occurred", "Failed to open external editor")

def test_controller_registers_itself_for_window_teardown(headless_gi_mocks, monkeypatch):
    controller, window = _make_controller(monkeypatch, MagicMock())

    window.register_controller.assert_called_once_with(controller)


def test_controller_tolerates_a_host_without_register_controller(headless_gi_mocks, monkeypatch):
    import anura.controllers.history_controller as module

    monkeypatch.setattr(module, "get_clipboard_service", lambda: MagicMock())

    assert module.HistoryController(object()) is not None


def test_teardown_disconnects_all_signals(headless_gi_mocks, monkeypatch):
    controller, _window = _make_controller(monkeypatch, MagicMock())
    controller.disconnect_all_signals = MagicMock()

    controller.teardown()

    controller.disconnect_all_signals.assert_called_once_with()


def test_cleanup_survives_a_failing_disconnect(headless_gi_mocks, monkeypatch):
    controller, _window = _make_controller(monkeypatch, MagicMock())
    controller.disconnect_all_signals = MagicMock(side_effect=RuntimeError("already finalised"))

    controller.cleanup()  # must not raise
