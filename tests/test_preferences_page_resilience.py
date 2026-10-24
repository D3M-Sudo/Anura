# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""Headless regression tests for preferences page __init__ resilience.

Regression (History V1): a failure in `_setup_tts_language()` (e.g. the
pre-ad5f49d `get_supported_gtts_languages()` AttributeError) used to abort
`PreferencesGeneralPage.__init__` before `_setup_history()` ran, leaving the
`history-enabled` switch unbound to GSettings and its value never persisted.

UI modernization (fase 3, sep 2026): Editor and Text-to-Speech settings were
extracted out of `PreferencesGeneralPage` into their own
`PreferencesEditorPage` / `PreferencesVoicePage` classes, each with an
independent `__init__`. This makes the original failure mode structurally
impossible in `PreferencesGeneralPage` (it no longer references TTS at all),
so the TTS-failure-isolation test is moved to `PreferencesVoicePage`, scoped
to what it must still protect there: a failure in `_setup_tts_language()`
must not prevent `_setup_tts_volume()`'s binding from taking effect. A
simple unconditional-binding test is kept for `PreferencesGeneralPage` to
confirm the split didn't silently drop the history binding.
"""

from unittest.mock import MagicMock

import gi
from gi.repository import Adw

gi.require_version("Adw", "1")
Adw.init()

from anura.core.resources import load_gresource_bundle  # noqa: E402


class FakeSettings:
    """Records GSettings calls made by the page under test."""

    def __init__(self):
        self.bound_keys: list[str] = []

    def bind(self, key, *_args, **_kwargs):
        self.bound_keys.append(key)

    def get_int(self, key):
        if key != "history-limit":
            raise KeyError(key)
        return 50

    def set_int(self, _key, _value):
        pass

    def set_double(self, _key, _value):
        pass

    def get_string(self, _key):
        return ""

    def get_double(self, _key):
        return 0.5


def _make_general_page(monkeypatch):
    """Build PreferencesGeneralPage with mocked collaborators."""
    load_gresource_bundle()
    import anura.widgets.preferences_general_page as mod

    fake_settings = FakeSettings()
    monkeypatch.setattr(mod, "settings", fake_settings)

    fake_lang_manager = MagicMock()
    monkeypatch.setattr(mod, "get_language_manager", lambda: fake_lang_manager)

    page = mod.PreferencesGeneralPage()
    return page, fake_settings


def _make_voice_page(monkeypatch, tts_raises: Exception | None):
    """Build PreferencesVoicePage with mocked collaborators; returns (page, settings)."""
    load_gresource_bundle()
    import anura.widgets.preferences_voice_page as mod

    fake_settings = FakeSettings()
    monkeypatch.setattr(mod, "settings", fake_settings)

    if tts_raises is not None:

        def _boom():
            raise tts_raises

        monkeypatch.setattr(mod, "get_tts_service", _boom)

    page = mod.PreferencesVoicePage()
    return page, fake_settings


def test_history_bound_unconditionally(monkeypatch, headless_gi_mocks):
    """General page no longer touches TTS at all, so history always binds."""
    _page, fake_settings = _make_general_page(monkeypatch)

    assert "history-enabled" in fake_settings.bound_keys
    assert "autocopy" in fake_settings.bound_keys


def test_history_limit_changed_persists(monkeypatch, headless_gi_mocks):
    """The SpinRow change handler persists the limit as an int."""
    page, _fake_settings = _make_general_page(monkeypatch)

    spin_row = MagicMock()
    spin_row.get_value.return_value = 120.0
    persisted: list[tuple[str, int]] = []

    class RecordingSettings(FakeSettings):
        def set_int(self, key, value):
            persisted.append((key, value))

    recording = RecordingSettings()
    page.settings = recording
    page._on_history_limit_changed(spin_row, None)

    assert persisted == [("history-limit", 120)]


def test_voice_page_volume_bound_when_tts_language_fails(monkeypatch, headless_gi_mocks):
    """A TTS-language setup failure must not prevent the volume row setup."""
    page, _fake_settings = _make_voice_page(monkeypatch, tts_raises=AttributeError("boom"))

    # _setup_tts_volume() ran and set the widget from settings (0.5 -> 50%),
    # proving it wasn't skipped/aborted by the later TTS-language failure.
    assert page.volume_row.get_value() == 50.0


def test_voice_page_init_completes_normally(monkeypatch, headless_gi_mocks):
    """Happy path: volume is set from settings when TTS setup succeeds."""
    page, _fake_settings = _make_voice_page(monkeypatch, tts_raises=None)

    assert page.volume_row.get_value() == 50.0
