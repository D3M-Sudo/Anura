# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""The gTTS catalog must never be fetched from the GTK main thread (#532).

Opening Preferences called ``get_supported_languages()`` synchronously, which on
a cold cache ran ``gtts.lang.tts_langs()`` on the UI thread and froze the dialog.
The page now reads a cached-only view and refreshes it on a worker thread.
"""

import importlib.util
from pathlib import Path
import sys

import pytest
import requests


def _load_language_mapper():
    """Import the module without running the TTS package initialiser (gi)."""
    name = "_anura_language_mapper_under_test"
    if name in sys.modules:
        return sys.modules[name]

    path = Path(__file__).resolve().parents[1] / "anura" / "services" / "tts" / "language_mapper.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


LanguageMapper = _load_language_mapper().LanguageMapper


@pytest.fixture(autouse=True)
def _reset_catalog():
    LanguageMapper._gtts_cache = None
    yield
    LanguageMapper._gtts_cache = None


def _patch_fetch(monkeypatch, behaviour):
    calls: list[int] = []

    def fake() -> dict:
        calls.append(1)
        return behaviour(len(calls))

    monkeypatch.setattr("gtts.lang.tts_langs", fake)
    return calls


def test_peek_never_fetches(monkeypatch):
    calls = _patch_fetch(monkeypatch, lambda _n: {"en": "English"})

    assert LanguageMapper.peek_supported_gtts_languages() is None
    assert calls == []


def test_refresh_caches_the_catalog(monkeypatch):
    calls = _patch_fetch(monkeypatch, lambda _n: {"en": "English"})

    assert LanguageMapper.refresh_supported_gtts_languages() == {"en": "English"}
    assert LanguageMapper.peek_supported_gtts_languages() == {"en": "English"}

    # A second refresh uses the cache.
    LanguageMapper.refresh_supported_gtts_languages()
    assert len(calls) == 1


def test_failed_fetch_is_not_cached_and_can_retry(monkeypatch):
    def behaviour(attempt: int) -> dict:
        if attempt == 1:
            raise requests.RequestException("offline")
        return {"en": "English"}

    calls = _patch_fetch(monkeypatch, behaviour)

    assert LanguageMapper.refresh_supported_gtts_languages() == {}
    # The empty result was not cached: a later attempt may still succeed.
    assert LanguageMapper.peek_supported_gtts_languages() is None

    assert LanguageMapper.get_supported_gtts_languages() == {"en": "English"}
    assert len(calls) == 2


def _page_source() -> str:
    return Path("anura/widgets/preferences_general_page.py").read_text(encoding="utf-8")


def _method_body(name: str, source: str) -> str:
    start = source.index(f"def {name}")
    rest = source[start:]
    end = rest.find("\n    def ", 1)
    return rest if end == -1 else rest[:end]


def _code_only(body: str) -> str:
    """Strip the docstring so prose about a removed call is not matched."""
    start = body.find('"""')
    end = body.find('"""', start + 3)
    if start == -1 or end == -1:
        return body
    return body[:start] + body[end + 3 :]


def test_page_initialization_uses_the_cached_view_only():
    body = _code_only(_method_body("_setup_tts_language", _page_source()))

    assert "get_cached_supported_languages()" in body
    assert "get_supported_languages()" not in body
    assert "_refresh_tts_catalog_async()" in body


def test_cold_cache_is_refreshed_off_the_ui_thread():
    body = _method_body("_refresh_tts_catalog_async", _page_source())

    assert "threading.Thread(" in body
    assert "daemon=True" in body
    assert "GLib.idle_add(self._on_tts_catalog_ready" in body


def test_programmatic_updates_do_not_write_the_setting_back():
    assert "if self._updating_tts_combo:" in _page_source()
