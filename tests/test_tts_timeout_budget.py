# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""The TTS watchdog must grow with the text length (#508).

gTTS issues one sequential HTTP request per 100-character fragment, so the fixed
35 s budget fired on long texts even with a healthy network, and was needlessly
long for a single sentence.
"""

import importlib.util
from pathlib import Path
import sys

from anura.config import TTS_TIMEOUT_BASE_S, TTS_TIMEOUT_MAX_S, TTS_TIMEOUT_PER_FRAGMENT_S


def _load_timeout_module():
    """Import the module without running the TTS package initialiser (gi)."""
    name = "_anura_tts_timeout_under_test"
    if name in sys.modules:
        return sys.modules[name]

    path = Path(__file__).resolve().parents[1] / "anura" / "services" / "tts" / "timeout.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


tts_timeout_seconds = _load_timeout_module().tts_timeout_seconds


def test_empty_text_gets_one_fragment_of_budget():
    assert tts_timeout_seconds("") == int(TTS_TIMEOUT_BASE_S + TTS_TIMEOUT_PER_FRAGMENT_S)


def test_budget_grows_with_the_fragment_count():
    one_fragment = tts_timeout_seconds("a" * 100)
    ten_fragments = tts_timeout_seconds("a" * 1000)

    # ceil(1000 / 100) == 10 requests
    assert ten_fragments == int(TTS_TIMEOUT_BASE_S + 10 * TTS_TIMEOUT_PER_FRAGMENT_S)
    assert ten_fragments > one_fragment


def test_maximum_text_gets_a_proportional_budget():
    # MAX_TTS_TEXT_LENGTH is 10,000 characters => 100 fragments.
    budget = tts_timeout_seconds("a" * 10_000)

    assert budget == int(TTS_TIMEOUT_BASE_S + 100 * TTS_TIMEOUT_PER_FRAGMENT_S)
    assert budget > 35  # the fixed budget this replaces


def test_budget_is_capped():
    assert tts_timeout_seconds("a" * 1_000_000) == int(TTS_TIMEOUT_MAX_S)


def test_budget_is_monotonic():
    budgets = [tts_timeout_seconds("a" * n) for n in (0, 50, 100, 101, 500, 1000, 5000)]

    assert budgets == sorted(budgets)
