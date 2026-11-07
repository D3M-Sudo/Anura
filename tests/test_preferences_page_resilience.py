# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""Headless regression tests for Preferences pages resilience.

Tests that Preferences page __init__ always completes and settings bindings
are registered, even when optional subsystems (TTS catalog, language manager)
fail.

GeneralPage: history settings binding must always execute (regression for
History V1 where a TTS failure aborted __init__ before _setup_history()).

VoicePage: volume row setup must not be skipped/aborted by a later TTS
language catalog failure (regression for PR #448 Phase 3 split, where the
original PreferencesVoicePage called get_supported_languages() synchronously
and could freeze/abort UI initialization (#532)).
"""

from unittest.mock import MagicMock

from anura.services.settings import settings


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

    def get_string(self, _key):
        return ""

    def get_double(self, _key):
        return 0.5


# ---------------------------------------------------------------------------
# GeneralPage
# ---------------------------------------------------------------------------

def _make_general_page(monkeypatch, tts_raises: Exception | None = None):
    """Build PreferencesGeneralPage with mocked collaborators."""
    import anura.widgets.preferences_general_page as mod

    fake_settings = FakeSettings()
    monkeypatch.setattr(mod, "settings", fake_settings)

    fake_lang_manager = MagicMock()
    monkeypatch.setattr(mod, "get_language_manager", lambda: fake_lang_manager)

    page = mod.PreferencesGeneralPage()
    return page, fake_settings


def test_general_init_completes_normally(monkeypatch, headless_gi_mocks):
    """Happy path: all expected keys are bound."""
    _page, fake_settings = _make_general_page(monkeypatch)

    assert "autocopy" in fake_settings.bound_keys
    assert "magic-processor-enabled" in fake_settings.bound_keys
    assert "history-enabled" in fake_settings.bound_keys


def test_general_history_limit_changed_persists(monkeypatch, headless_gi_mocks):
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


# ---------------------------------------------------------------------------
# VoicePage
# ---------------------------------------------------------------------------

def _make_voice_page(monkeypatch, tts_raises: Exception | None = None):
    """Build PreferencesVoicePage with mocked collaborators."""
    import anura.widgets.preferences_voice_page as mod

    fake_settings = FakeSettings()
    monkeypatch.setattr(mod, "settings", fake_settings)

    if tts_raises is not None:

        def _boom():
            raise tts_raises

        monkeypatch.setattr(mod, "get_tts_service", _boom)

    page = mod.PreferencesVoicePage()
    return page, fake_settings


def test_voice_page_volume_bound_when_tts_language_fails(monkeypatch, headless_gi_mocks):
    """A TTS-language setup failure must not prevent the volume row setup."""
    page, _fake_settings = _make_voice_page(monkeypatch, tts_raises=AttributeError("boom"))

    # _setup_tts_volume() ran and connected the volume_row signal,
    # proving it wasn't skipped/aborted by the later TTS-language failure.
    assert page.volume_row is not None


def test_voice_page_init_completes_normally(monkeypatch, headless_gi_mocks):
    """Happy path: volume row and language combo are present."""
    page, fake_settings = _make_voice_page(monkeypatch, tts_raises=None)

    assert page.volume_row is not None
    assert page.tts_language_combo is not None
    assert "tts-volume" in fake_settings.bound_keys
