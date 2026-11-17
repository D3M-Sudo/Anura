# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""Headless regression tests for Preferences pages resilience.

Tests that Preferences page initialization and settings callbacks remain
reliable when optional subsystems (TTS catalog, language manager) fail.

GeneralPage covers history settings, color-scheme mapping and extra-language
selection/removal. VoicePage covers volume settings and asynchronous catalog
failure/disposal behavior.
"""

from unittest.mock import MagicMock

import pytest


class FakeSettings:
    """Records GSettings calls made by the page under test."""

    def __init__(self, values=None):
        self.bound_keys: list[str] = []
        self.values = {"tts-volume": 0.5, "color-scheme": "default", "extra-language": ""}
        self.values.update(values or {})
        self.handlers: dict[int, tuple[str, object]] = {}
        self._next_handler = 1

    def bind(self, key, *_args, **_kwargs):
        self.bound_keys.append(key)

    def get_int(self, key):
        if key != "history-limit":
            raise KeyError(key)
        return 50

    def set_int(self, _key, _value):
        pass

    def get_string(self, key):
        return self.values.get(key, "")

    def set_string(self, key, value):
        self.values[key] = value

    def get_double(self, key):
        return self.values[key]

    def set_double(self, key, value):
        self.values[key] = value
        for _signal, callback in list(self.handlers.values()):
            if _signal == f"changed::{key}":
                callback(self, key)

    def connect(self, signal, callback):
        handler_id = self._next_handler
        self._next_handler += 1
        self.handlers[handler_id] = (signal, callback)
        return handler_id

    def disconnect(self, handler_id):
        self.handlers.pop(handler_id, None)


# ---------------------------------------------------------------------------
# GeneralPage
# ---------------------------------------------------------------------------
def _make_general_page(monkeypatch, settings_values=None, language_manager=None):
    """Build PreferencesGeneralPage with mocked collaborators."""
    import anura.widgets.preferences_general_page as mod

    fake_settings = FakeSettings(settings_values)
    monkeypatch.setattr(mod, "settings", fake_settings)

    fake_lang_manager = language_manager if language_manager is not None else MagicMock()
    monkeypatch.setattr(mod, "get_language_manager", lambda: fake_lang_manager)

    page = mod.PreferencesGeneralPage()
    return page, fake_settings, fake_lang_manager


def test_general_init_completes_normally(monkeypatch, headless_gi_mocks):
    """Happy path: all expected keys are bound."""
    _page, fake_settings, _manager = _make_general_page(monkeypatch)

    assert "autocopy" in fake_settings.bound_keys
    assert "magic-processor-enabled" in fake_settings.bound_keys
    assert "history-enabled" in fake_settings.bound_keys


@pytest.mark.parametrize(
    ("stored_scheme", "expected_index"),
    [("default", 0), ("force-light", 1), ("force-dark", 2), ("unknown", 0)],
)
def test_general_color_scheme_setting_initializes_combo(monkeypatch, headless_gi_mocks, stored_scheme, expected_index):
    """The stored color-scheme value selects its corresponding combo item."""
    page, _settings, _manager = _make_general_page(monkeypatch, settings_values={"color-scheme": stored_scheme})

    page.color_scheme_combo.set_selected.assert_called_with(expected_index)


@pytest.mark.parametrize(
    ("selected_index", "expected_scheme"),
    [(0, "default"), (1, "force-light"), (2, "force-dark"), (99, "default")],
)
def test_general_color_scheme_selection_persists_setting(
    monkeypatch, headless_gi_mocks, selected_index, expected_scheme
):
    """Selecting a color-scheme item persists the matching GSettings value."""
    page, fake_settings, _manager = _make_general_page(monkeypatch)
    page.color_scheme_combo.get_selected.return_value = selected_index

    page._on_color_scheme_changed(page.color_scheme_combo, None)

    assert fake_settings.get_string("color-scheme") == expected_scheme


def test_general_extra_language_setting_selects_downloaded_language(monkeypatch, headless_gi_mocks):
    """A configured language code selects its downloaded language title."""
    manager = MagicMock()
    manager.get_downloaded_languages.return_value = ["English", "Italian"]
    manager.get_language.return_value = "Italian"

    page, _settings, _manager = _make_general_page(
        monkeypatch,
        settings_values={"extra-language": "ita"},
        language_manager=manager,
    )

    page.extra_language_combo.set_selected.assert_called_once_with(1)


def test_general_extra_language_selection_persists_language_code(monkeypatch, headless_gi_mocks):
    """Selecting a language title persists the manager's canonical language code."""
    manager = MagicMock()
    manager.get_downloaded_languages.return_value = ["English", "Italian"]
    manager.get_language_code.return_value = "ita"
    page, fake_settings, _manager = _make_general_page(monkeypatch, language_manager=manager)

    selected_item = MagicMock()
    selected_item.get_string.return_value = "Italian"
    page.extra_language_combo.get_selected_item.return_value = selected_item

    page._on_extra_language_changed(page.extra_language_combo, None)

    assert fake_settings.get_string("extra-language") == "ita"


def test_general_removing_active_extra_language_clears_setting_and_refreshes_model(monkeypatch, headless_gi_mocks):
    """Removing the configured extra language clears it and refreshes choices."""
    manager = MagicMock()
    manager.get_downloaded_languages.return_value = ["English"]
    page, fake_settings, _manager = _make_general_page(
        monkeypatch,
        settings_values={"extra-language": "ita"},
        language_manager=manager,
    )
    page.extra_language_combo.set_model.reset_mock()

    page._on_language_changed(manager, "ita")

    assert fake_settings.get_string("extra-language") == ""
    page.extra_language_combo.set_model.assert_called_once()


def test_general_history_limit_changed_persists(monkeypatch, headless_gi_mocks):
    """The SpinRow change handler persists the limit as an int."""
    page, _fake_settings, _manager = _make_general_page(monkeypatch)

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

    assert page.volume_row is not None


def test_voice_page_init_completes_normally(monkeypatch, headless_gi_mocks):
    """Happy path: volume row and language combo are present."""
    page, fake_settings = _make_voice_page(monkeypatch, tts_raises=AttributeError("catalog unavailable"))

    assert page.volume_row is not None
    assert page.tts_language_combo is not None
    assert any(signal == "changed::tts-volume" for signal, _callback in fake_settings.handlers.values())


def test_voice_volume_initial_value_uses_saved_setting(monkeypatch, headless_gi_mocks):
    """The SpinRow is initialized from the saved normalized GSettings value."""
    page, _fake_settings = _make_voice_page(monkeypatch, tts_raises=AttributeError("catalog unavailable"))

    assert page.volume_row.set_value.call_args_list[0].args == (50.0,)


def test_voice_volume_change_persists_normalized_setting(monkeypatch, headless_gi_mocks):
    """A percentage change is persisted as a normalized GSettings double."""
    page, fake_settings = _make_voice_page(monkeypatch, tts_raises=AttributeError("catalog unavailable"))

    page.volume_row.get_value.return_value = 30.0
    page._on_volume_changed(page.volume_row, None)

    assert fake_settings.get_double("tts-volume") == 0.3


def test_external_volume_setting_change_updates_row(monkeypatch, headless_gi_mocks):
    """External GSettings changes update the row without a feedback write."""
    page, fake_settings = _make_voice_page(monkeypatch, tts_raises=AttributeError("catalog unavailable"))

    page.volume_row.get_value.return_value = 50.0
    page.volume_row.set_value.reset_mock()
    fake_settings.set_double("tts-volume", 0.3)

    page.volume_row.set_value.assert_called_once_with(30.0)


def test_voice_catalog_worker_failure_resets_loading_state(monkeypatch, headless_gi_mocks):
    """A failed asynchronous catalog fetch must not leave the page loading forever."""
    import anura.widgets.preferences_voice_page as mod

    class Service:
        def get_cached_supported_languages(self):
            return None

        def get_supported_languages(self):
            raise RuntimeError("network unavailable")

    class InlineThread:
        def __init__(self, target, **_kwargs):
            self.target = target

        def start(self):
            self.target()

    monkeypatch.setattr(mod, "get_tts_service", lambda: Service())
    monkeypatch.setattr(mod.threading, "Thread", InlineThread)
    monkeypatch.setattr(mod.GLib, "idle_add", lambda callback, *args: callback(*args))

    fake_settings = FakeSettings()
    monkeypatch.setattr(mod, "settings", fake_settings)
    page = mod.PreferencesVoicePage()

    assert page._tts_catalog_loading is False
