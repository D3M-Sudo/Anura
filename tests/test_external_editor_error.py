# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""Headless tests for the external-editor launch error surfacing (VM bug #6).

Gtk.FileLauncher routes through org.freedesktop.portal.OpenURI, so a launch
failure is usually environment-side (missing portal backend). The handler must
surface that context (portal name + raw error) instead of a generic toast, and
must stay quiet when the user merely cancels the chooser dialog.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock


class _FakeGError(Exception):
    """Stand-in for GLib.Error with the `message`/`matches` surface used here."""

    def __init__(self, message: str, cancelled: bool = False) -> None:
        super().__init__(message)
        self.message = message
        self._cancelled = cancelled

    def matches(self, _quark: object, _code: object) -> bool:
        return self._cancelled


def _install_fake_gi(monkeypatch) -> None:
    import anura.window as window_module

    fake_glib = SimpleNamespace(Error=_FakeGError)
    fake_gio = SimpleNamespace(
        io_error_quark=lambda: "fake-quark",
        IOErrorEnum=SimpleNamespace(CANCELLED=object()),
    )
    monkeypatch.setattr(window_module, "GLib", fake_glib, raising=False)
    monkeypatch.setattr(window_module, "Gio", fake_gio, raising=False)


def _make_self():
    toasts: list[str] = []
    return SimpleNamespace(show_toast=toasts.append, toasts=toasts)


def _get_handler():
    from anura.window import AnuraWindow

    return AnuraWindow._on_external_editor_launched


def test_success_shows_confirmation_toast(monkeypatch):
    _install_fake_gi(monkeypatch)
    self_fake = _make_self()
    launcher = MagicMock()
    launcher.launch_finish.return_value = True

    _get_handler()(self_fake, launcher, MagicMock())

    assert len(self_fake.toasts) == 1
    assert "external editor" in self_fake.toasts[0]


def test_user_cancellation_is_silent(monkeypatch):
    _install_fake_gi(monkeypatch)
    self_fake = _make_self()
    launcher = MagicMock()
    launcher.launch_finish.side_effect = _FakeGError("cancelled", cancelled=True)

    _get_handler()(self_fake, launcher, MagicMock())

    assert self_fake.toasts == []


def test_portal_failure_toast_names_portal_and_raw_error(monkeypatch):
    _install_fake_gi(monkeypatch)
    self_fake = _make_self()
    launcher = MagicMock()
    launcher.launch_finish.side_effect = _FakeGError("The application launch failed (0)")

    _get_handler()(self_fake, launcher, MagicMock())

    assert len(self_fake.toasts) == 1
    toast = self_fake.toasts[0]
    assert "org.freedesktop.portal.OpenURI" in toast
    assert "The application launch failed (0)" in toast
    assert "portal backend" in toast


def test_runtime_error_toast_includes_detail(monkeypatch):
    _install_fake_gi(monkeypatch)
    self_fake = _make_self()
    launcher = MagicMock()
    launcher.launch_finish.side_effect = RuntimeError("no default application")

    _get_handler()(self_fake, launcher, MagicMock())

    assert len(self_fake.toasts) == 1
    assert "no default application" in self_fake.toasts[0]
    assert "org.freedesktop.portal.OpenURI" in self_fake.toasts[0]


if __name__ == "__main__":
    import pytest

    pytest.main([__file__])
