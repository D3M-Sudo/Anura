# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""Regression tests for WelcomePage's asynchronous URI-list drop lifecycle."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest


def _patch_drag_actions(monkeypatch):
    import anura.widgets.welcome_page as welcome_page

    actions = SimpleNamespace(COPY=object(), NONE=object())
    monkeypatch.setattr(welcome_page.Gdk, "DragAction", actions)
    return actions


def _page(headless_gi_mocks):
    from anura.widgets.welcome_page import WelcomePage

    page = WelcomePage()
    window = MagicMock()
    window._begin_ocr_operation.return_value = 41
    window._is_current_ocr_operation.return_value = True
    page.get_root = MagicMock(return_value=window)
    page._set_drop_area_processing_state = MagicMock()
    page._show_error_toast = MagicMock()
    page._process_dropped_path = MagicMock()
    return page, window


def _bytes_result(monkeypatch, payload: bytes):
    import anura.widgets.welcome_page as welcome_page

    stream = MagicMock()
    stream.read_bytes_finish.return_value.get_data.return_value = payload
    monkeypatch.setattr(welcome_page.Gio, "File", MagicMock())
    welcome_page.Gio.File.new_for_uri.return_value.get_path.return_value = "/tmp/dropped.png"
    monkeypatch.setattr(welcome_page.Path, "exists", lambda _path: True)
    monkeypatch.setattr(welcome_page, "guess_type", lambda _path: ("image/png", None))
    return stream


def _run_bytes_callback(page, stream, drop, cancellable, operation_id=41):
    page._drop_cancellable = cancellable
    page._on_drop_bytes_ready(stream, MagicMock(), (stream, drop, cancellable, operation_id))


def test_local_image_uri_finishes_copy_exactly_once_and_dispatches(monkeypatch, headless_gi_mocks):
    actions = _patch_drag_actions(monkeypatch)
    page, _window = _page(headless_gi_mocks)
    stream = _bytes_result(monkeypatch, b"file:///tmp/dropped.png\\r\\n")
    drop = MagicMock()
    cancellable = MagicMock()

    _run_bytes_callback(page, stream, drop, cancellable)

    drop.finish.assert_called_once_with(actions.COPY)
    page._process_dropped_path.assert_called_once_with("/tmp/dropped.png", 41)
    page._show_error_toast.assert_not_called()
    assert page._drop_cancellable is None


@pytest.mark.parametrize("payload", [b"", b"# comment\\r\\n\\r\\n"])
def test_empty_or_uri_free_payload_finishes_none(monkeypatch, headless_gi_mocks, payload):
    actions = _patch_drag_actions(monkeypatch)
    page, _window = _page(headless_gi_mocks)
    stream = _bytes_result(monkeypatch, payload)
    drop = MagicMock()

    _run_bytes_callback(page, stream, drop, MagicMock())

    drop.finish.assert_called_once_with(actions.NONE)
    page._process_dropped_path.assert_not_called()
    page._show_error_toast.assert_called_once()


def test_non_local_uri_finishes_none(monkeypatch, headless_gi_mocks):
    import anura.widgets.welcome_page as welcome_page

    actions = _patch_drag_actions(monkeypatch)
    page, _window = _page(headless_gi_mocks)
    stream = _bytes_result(monkeypatch, b"https://example.test/image.png\\r\\n")
    welcome_page.Gio.File.new_for_uri.return_value.get_path.return_value = None
    drop = MagicMock()

    _run_bytes_callback(page, stream, drop, MagicMock())

    drop.finish.assert_called_once_with(actions.NONE)
    page._process_dropped_path.assert_not_called()
    page._show_error_toast.assert_called_once()


def test_read_async_failure_finishes_none_and_reports_error(monkeypatch, headless_gi_mocks):
    import anura.widgets.welcome_page as welcome_page

    actions = _patch_drag_actions(monkeypatch)
    page, _window = _page(headless_gi_mocks)
    monkeypatch.setattr(welcome_page.GLib, "Error", RuntimeError)
    drop = MagicMock()
    drop.read_finish.side_effect = RuntimeError("stream unavailable")

    page._on_drop_stream_ready(drop, MagicMock(), (drop, MagicMock(), 41))

    drop.finish.assert_called_once_with(actions.NONE)
    page._show_error_toast.assert_called_once()
    page._process_dropped_path.assert_not_called()


def test_read_bytes_failure_finishes_none_and_reports_error(monkeypatch, headless_gi_mocks):
    import anura.widgets.welcome_page as welcome_page

    actions = _patch_drag_actions(monkeypatch)
    page, _window = _page(headless_gi_mocks)
    monkeypatch.setattr(welcome_page.GLib, "Error", RuntimeError)
    stream = MagicMock()
    stream.read_bytes_finish.side_effect = RuntimeError("read cancelled")
    drop = MagicMock()
    cancellable = MagicMock()

    _run_bytes_callback(page, stream, drop, cancellable)

    drop.finish.assert_called_once_with(actions.NONE)
    page._show_error_toast.assert_called_once()
    page._process_dropped_path.assert_not_called()
    assert page._drop_cancellable is None


def test_cancelled_previous_drop_does_not_replace_new_cancellable(headless_gi_mocks):
    page, _window = _page(headless_gi_mocks)
    previous = MagicMock()
    page._drop_cancellable = previous
    drop = MagicMock()

    accepted = page._on_dnd_drop(MagicMock(), drop, 0.0, 0.0)

    assert accepted is True
    previous.cancel.assert_called_once()
    assert page._drop_cancellable is not previous
    drop.read_async.assert_called_once()


def test_stale_callback_finishes_none_without_processing_or_toast(monkeypatch, headless_gi_mocks):
    actions = _patch_drag_actions(monkeypatch)
    page, window = _page(headless_gi_mocks)
    window._is_current_ocr_operation.return_value = False
    stream = _bytes_result(monkeypatch, b"file:///tmp/dropped.png\\r\\n")
    drop = MagicMock()

    _run_bytes_callback(page, stream, drop, MagicMock())

    drop.finish.assert_called_once_with(actions.NONE)
    page._process_dropped_path.assert_not_called()
    page._show_error_toast.assert_not_called()
