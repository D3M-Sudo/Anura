# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""Headless regression tests for ExtractedPage undo/redo handlers.

Regression context: `_on_undo`/`_on_redo` used to call
`self.buffer.can_undo()`/`can_redo()` as if they were methods. They are
GObject *properties* exposed by PyGObject as `get_can_undo()`/`get_can_redo()`,
so clicking Undo/Redo raised `AttributeError` and silently did nothing.
These tests invoke the handlers directly so a regression here is not silent.
"""

from unittest.mock import MagicMock

import pytest


def _make_page(buffer):
    """Build a bare ExtractedPage without touching widget templates."""
    from anura.widgets.extracted_page import ExtractedPage

    page = object.__new__(ExtractedPage)
    page.buffer = buffer
    return page


def test_on_undo_calls_undo_when_buffer_can_undo(headless_gi_mocks):
    buffer = MagicMock()
    buffer.get_can_undo.return_value = True
    page = _make_page(buffer)

    page._on_undo()

    buffer.undo.assert_called_once()


def test_on_undo_skips_when_buffer_cannot_undo(headless_gi_mocks):
    buffer = MagicMock()
    buffer.get_can_undo.return_value = False
    page = _make_page(buffer)

    page._on_undo()

    buffer.undo.assert_not_called()


def test_on_redo_calls_redo_when_buffer_can_redo(headless_gi_mocks):
    buffer = MagicMock()
    buffer.get_can_redo.return_value = True
    page = _make_page(buffer)

    page._on_redo()

    buffer.redo.assert_called_once()


def test_on_redo_skips_when_buffer_cannot_redo(headless_gi_mocks):
    buffer = MagicMock()
    buffer.get_can_redo.return_value = False
    page = _make_page(buffer)

    page._on_redo()

    buffer.redo.assert_not_called()


def test_handlers_noop_with_no_buffer(headless_gi_mocks):
    page = _make_page(None)

    page._on_undo()
    page._on_redo()


def test_handlers_never_call_nonexistent_can_undo_method(headless_gi_mocks):
    """Guard against regression to `buffer.can_undo()` (raises AttributeError)."""
    buffer = MagicMock(spec=["get_can_undo", "get_can_redo", "undo", "redo"])
    buffer.get_can_undo.return_value = True
    buffer.get_can_redo.return_value = True
    page = _make_page(buffer)

    page._on_undo()
    page._on_redo()

    buffer.undo.assert_called_once()
    buffer.redo.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])
