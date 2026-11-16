# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""Shutdown must not instantiate optional services (#536).

``AnuraApplication._cleanup_services()`` called ``get_tts_service().cleanup()``,
and the lazy getter created ``TTSService`` — which starts a background fetch of
the Google TTS language catalog — just to tear it down. A silent CLI run that
only did OCR therefore made an outbound request at process exit.
"""

from pathlib import Path

import pytest

from anura.utils import singleton as singleton_module
from anura.utils.singleton import ThreadSafeSingleton, get_existing_instance, get_instance


class _Service:
    def __init__(self) -> None:
        self.constructed = True


@pytest.fixture(autouse=True)
def _reset_singletons():
    ThreadSafeSingleton.reset_for_testing()
    yield
    ThreadSafeSingleton.reset_for_testing()


def test_existing_lookup_does_not_construct():
    created: list[_Service] = []

    class _Tracked:
        def __init__(self) -> None:
            created.append(self)

    assert get_existing_instance(_Tracked) is None
    assert created == []


def test_existing_lookup_returns_the_singleton_once_created():
    service = get_instance(_Service)

    assert get_existing_instance(_Service) is service


def test_existing_lookup_is_a_no_op_for_unrelated_classes():
    get_instance(_Service)

    assert get_existing_instance(dict) is None


def test_shutdown_uses_the_non_initializing_lookup():
    source = Path("anura/main.py").read_text(encoding="utf-8")
    cleanup = source[source.index("def _cleanup_services") : source.index("def do_activate")]

    assert "get_existing_instance(TTSService)" in cleanup
    assert "get_tts_service()" not in cleanup


def test_module_level_helper_delegates():
    assert singleton_module.get_existing_instance is not None
