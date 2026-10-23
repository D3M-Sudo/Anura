# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""Streamed HTTP responses must be closed on every download exit path (#520).

``download_begin()`` returns early for an oversized Content-Length, a size
mismatch with the pinned model, cancellation and an oversized stream. Each of
those returns used to leave the streamed response open, retaining its
connection and socket until garbage collection.

The behavioural assertions run in the GTK tier
(``tests/test_language_download_integrity.py``); this headless test keeps the
structure that makes them pass.
"""

from pathlib import Path


def _download_begin_source() -> str:
    source = Path("anura/services/language/download_manager.py").read_text(encoding="utf-8")
    start = source.index("def download_begin")
    end = source.index("def download_done(", start)
    return source[start:end]


def test_response_is_tracked_before_the_guarded_block():
    body = _download_begin_source()

    assert "response: requests.Response | None = None" in body
    assert body.index("response: requests.Response | None = None") < body.index("response = self.session.get(")


def test_response_is_closed_before_the_temp_file_is_removed():
    body = _download_begin_source()

    close_at = body.index("response.close()")
    assert close_at < body.index("tmp_path.unlink()")
    # The close must not be on an early-return branch: it sits in the finally
    # that also removes the temporary model file.
    assert body.rindex("finally:", 0, close_at) > body.rindex("with tmp_path.open", 0, close_at)
