# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""Drag-and-drop cancellable ownership (#538).

``_on_dnd_drop()`` replaces ``self._drop_cancellable`` for every drop, but the
bytes callback cleared that field unconditionally. A delayed callback from a
cancelled drop could therefore drop the *new* drop's cancellable, leaving the
active read uncancellable by the next drop or by ``do_destroy()``.
"""

from pathlib import Path


def _source() -> str:
    return Path("anura/widgets/welcome_page.py").read_text(encoding="utf-8")


def _method_body(name: str, source: str) -> str:
    start = source.index(f"def {name}")
    rest = source[start:]
    end = rest.find("\n    def ", 1)
    return rest if end == -1 else rest[:end]


def test_cancellable_is_carried_through_the_async_chain():
    source = _source()

    assert "(drop, cancellable)" in source
    assert "(input_stream, drop, cancellable)" in source


def test_bytes_callback_clears_only_its_own_cancellable():
    body = _method_body("_on_drop_bytes_ready", _source())

    assert "stream, drop, cancellable = user_data" in body
    assert "if self._drop_cancellable is cancellable:" in body
