# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""Failure paths of SpeechGenerator.generate() (#547).

The gTTS constructor validates the language and can raise ValueError before any
request is made. It must map to the same empty-path result as a save failure so
the pipeline can emit its normal error signal, and no partial MP3 may be left
behind.
"""

import importlib.util
from pathlib import Path
import sys

import gtts
import pytest
import requests


def _load_speech_generator():
    """Import the module without running ``anura.services.tts.__init__`` (gi)."""
    name = "_anura_speech_generator_error_paths"
    if name in sys.modules:
        return sys.modules[name]

    path = Path(__file__).resolve().parents[1] / "anura" / "services" / "tts" / "speech_generator.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


module = _load_speech_generator()


@pytest.fixture
def generator(tmp_path, monkeypatch):
    monkeypatch.setattr(module.SpeechGenerator, "_speech_dir", tmp_path)
    return module.SpeechGenerator(), tmp_path


def test_constructor_value_error_returns_empty_path(generator, monkeypatch):
    service, cache_dir = generator

    def _raise(*_args, **_kwargs):
        raise ValueError("unsupported language: xx")

    monkeypatch.setattr(module, "_VerifiedTTS", _raise)

    assert service.generate("hello", lang="xx") == ""
    assert list(cache_dir.iterdir()) == []


def test_request_error_returns_empty_path(generator, monkeypatch):
    service, cache_dir = generator

    class _FailingTTS:
        def __init__(self, *_args, **_kwargs) -> None:
            pass

        def save(self, _path: str) -> None:
            raise requests.RequestException("network down")

    monkeypatch.setattr(module, "_VerifiedTTS", _FailingTTS)

    assert service.generate("hello", lang="en") == ""
    assert list(cache_dir.iterdir()) == []


def test_gtts_error_returns_empty_path(generator, monkeypatch):
    service, cache_dir = generator

    class _FailingTTS:
        def __init__(self, *_args, **_kwargs) -> None:
            pass

        def save(self, _path: str) -> None:
            raise gtts.gTTSError("api error")

    monkeypatch.setattr(module, "_VerifiedTTS", _FailingTTS)

    assert service.generate("hello", lang="en") == ""
    assert list(cache_dir.iterdir()) == []


def test_partial_file_is_removed_on_save_failure(generator, monkeypatch):
    service, cache_dir = generator

    class _PartialTTS:
        def __init__(self, *_args, **_kwargs) -> None:
            pass

        def save(self, path: str) -> None:
            Path(path).write_bytes(b"partial-mp3")
            raise OSError("disk full")

    monkeypatch.setattr(module, "_VerifiedTTS", _PartialTTS)

    assert service.generate("hello", lang="en") == ""
    assert list(cache_dir.iterdir()) == []


def test_system_exit_propagates(generator, monkeypatch):
    service, _cache_dir = generator

    def _raise(*_args, **_kwargs):
        raise SystemExit(1)

    monkeypatch.setattr(module, "_VerifiedTTS", _raise)

    with pytest.raises(SystemExit):
        service.generate("hello", lang="en")
