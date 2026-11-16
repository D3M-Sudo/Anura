# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""Playback URIs for generated audio (#528).

``AudioPlayer.play()`` used ``f"file://{filepath}"``. A filesystem path is not a
URI: with a cache directory containing a space, ``#`` or non-ASCII characters,
GStreamer received an invalid or misinterpreted URI and playback failed even
though generation succeeded.
"""

from pathlib import Path
from urllib.parse import unquote, urlparse

import pytest

from anura.utils.file_uri import file_uri


def _roundtrip(uri: str) -> str:
    return unquote(urlparse(uri).path)


@pytest.mark.parametrize(
    "name",
    [
        "speech.mp3",
        "speech with spaces.mp3",
        "speech#fragment.mp3",
        "speech?query.mp3",
        "speech 100%.mp3",
        "voce-città.mp3",
        "日本語.mp3",
    ],
)
def test_paths_become_parseable_uris(tmp_path, name):
    path = tmp_path / name
    path.write_bytes(b"mp3")

    uri = file_uri(path)

    assert uri.startswith("file:///")
    assert " " not in uri
    assert _roundtrip(uri) == str(path)


def test_spaces_and_reserved_characters_are_escaped(tmp_path):
    path = tmp_path / "a b#c?d.mp3"

    uri = file_uri(path)

    assert " " not in uri
    assert "#" not in uri
    assert "?" not in uri


def test_relative_path_is_made_absolute():
    uri = file_uri("speech.mp3")

    assert uri.startswith("file:///")
    assert uri.endswith("/speech.mp3")


def test_audio_player_does_not_concatenate_file_prefix():
    source = (Path(__file__).resolve().parents[1] / "anura" / "services" / "tts" / "audio_player.py").read_text(
        encoding="utf-8"
    )

    assert 'f"file://' not in source
    assert "file_uri(filepath)" in source
