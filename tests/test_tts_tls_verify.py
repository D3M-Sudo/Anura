# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""TLS verification for the Google TTS traffic (#505).

gTTS 2.5.4 hardcodes ``verify=False`` with no public switch, so the client used
by Anura is a subclass that performs the same request loop with verification
enabled. These tests pin both the request parameter and the wiring.
"""

import base64
import importlib.util
from pathlib import Path
import sys

import gtts
import requests


def _load_speech_generator():
    """Import the module without running ``anura.services.tts.__init__``.

    The package initialiser imports ``AudioPlayer``, which imports PyGObject;
    the generator itself only needs ``gtts``/``requests``, so loading the file
    directly keeps this a headless test.
    """
    name = "_anura_speech_generator_under_test"
    if name in sys.modules:
        return sys.modules[name]

    path = Path(__file__).resolve().parents[1] / "anura" / "services" / "tts" / "speech_generator.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_VerifiedTTS = _load_speech_generator()._VerifiedTTS

_AUDIO_B64 = base64.b64encode(b"fake-mp3").decode("ascii")
_AUDIO_LINE = ('garbage jQ1olc","[\\"' + _AUDIO_B64 + '\\"] trailer').encode()


class _FakeResponse:
    status_code = 200

    def raise_for_status(self) -> None:
        pass

    def iter_lines(self, chunk_size: int = 1024):
        return iter([_AUDIO_LINE])


def test_stream_sends_the_request_with_tls_verification(monkeypatch):
    captured: dict[str, object] = {}

    def fake_send(self, request, verify=None, proxies=None, timeout=None):
        captured["verify"] = verify
        captured["timeout"] = timeout
        return _FakeResponse()

    monkeypatch.setattr(requests.Session, "send", fake_send)

    client = _VerifiedTTS("hello world", lang="en", lang_check=False, timeout=7)
    chunks = list(client.stream())

    assert captured["verify"] is True
    assert captured["timeout"] == 7
    assert chunks == [b"fake-mp3"]


def test_client_overrides_the_upstream_stream():
    assert issubclass(_VerifiedTTS, gtts.gTTS)
    assert _VerifiedTTS.stream is not gtts.gTTS.stream


def test_speech_generator_uses_the_verified_client():
    source = Path("anura/services/tts/speech_generator.py").read_text(encoding="utf-8")

    assert "_VerifiedTTS(" in source
    # The unverified upstream class must never be constructed directly.
    assert "gtts.gTTS(" not in source
