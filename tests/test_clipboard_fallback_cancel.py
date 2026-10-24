# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""The texture read must not clear the fallback's cancellable (#525).

``_on_read_texture().process_result()`` starts the URI-list fallback, which
installs a new ``Gio.Cancellable`` in ``self._cancellable``. The surrounding
``finally`` used to set that field to ``None`` regardless, so the fallback lost
its reference: the 10 s watchdog treated its timeout as stale and
``cancel_pending_operations()`` could no longer cancel it.
"""

from pathlib import Path


def _method_body(name: str, source: str) -> str:
    start = source.index(f"def {name}")
    rest = source[start:]
    end = rest.find("\n    def ", 1)
    return rest if end == -1 else rest[:end]


def test_clearing_is_guarded_by_identity():
    source = Path("anura/services/clipboard_service.py").read_text(encoding="utf-8")
    body = _method_body("_on_read_texture", source)

    assert "texture_cancellable = self._cancellable" in body
    assert "if self._cancellable is texture_cancellable:" in body
