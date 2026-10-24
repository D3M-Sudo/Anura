# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""Language-refresh idle callbacks must be cancellable (#539).

``PreferencesDialog`` scheduled refreshes with ``GLib.idle_add()`` from
language-manager signals and discarded the source id. Disconnecting the signals
in ``do_destroy()`` does not cancel an idle that is already queued, so a
download finishing while the dialog closed could run the refresh against
destroyed child pages.
"""

from pathlib import Path


def _source() -> str:
    return Path("anura/widgets/preferences_dialog.py").read_text(encoding="utf-8")


def _method_body(name: str, source: str) -> str:
    start = source.index(f"def {name}")
    rest = source[start:]
    end = rest.find("\n    def ", 1)
    return rest if end == -1 else rest[:end]


def test_refresh_is_scheduled_through_the_tracked_helper():
    source = _source()

    assert "self._schedule_idle(self.on_language_downloaded, code)" in source
    assert "GLib.idle_add(self.on_language_downloaded" not in source


def test_destroy_removes_pending_idle_sources():
    body = _method_body("do_destroy", _source())

    assert "self._disposed = True" in body
    assert "GLib.source_remove(source_id)" in body
    assert "self._pending_idle_sources.clear()" in body


def test_idle_wrapper_checks_the_disposed_flag():
    body = _method_body("_schedule_idle", _source())

    assert "if not self._disposed:" in body
    assert "self._pending_idle_sources.discard(source[0])" in body
