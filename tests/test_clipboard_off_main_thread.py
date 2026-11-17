# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""The clipboard image decode must leave the GTK main thread (#581).

The behavioural tests live in ``tests/test_clipboard_service.py`` (GTK tier);
this headless check pins the structure, so a refactor cannot silently move the
PIL decode back into the main-loop callback.
"""

from pathlib import Path

SOURCE = Path("anura/services/clipboard_service.py").read_text(encoding="utf-8")


def _method_body(name: str) -> str:
    start = SOURCE.index(f"def {name}")
    rest = SOURCE[start:]
    end = rest.find("\n    def ", 1)
    return rest if end == -1 else rest[:end]


def test_emit_texture_from_file_only_dispatches():
    body = _method_body("_emit_texture_from_file")

    assert "execute_daemon(" in body
    assert "lane=CLIPBOARD_LANE" in body
    # The blocking work must not be here any more.
    assert "Image.open" not in body
    assert "img.load()" not in body


def test_decode_helper_runs_without_gtk():
    body = _method_body("_decode_image_file")

    assert "Image.open" in body
    # Only PIL work: no texture creation, no signal emission.
    assert "Gdk.Texture" not in body
    assert "self.emit(" not in body


def test_texture_creation_happens_in_the_idle_callback():
    body = _method_body("_on_image_decoded")

    assert "Gdk.Texture.new_from_bytes" in body
    assert 'emit("paste_from_clipboard"' in body
