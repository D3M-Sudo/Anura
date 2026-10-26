# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""Time budget for a gTTS generation (#508).

gTTS 2.5.x splits the text into fragments of at most 100 characters and issues
one sequential HTTP request per fragment, so the wall-clock cost grows with the
text. The previous fixed 35 s watchdog fired on long texts even with a healthy
network, and was needlessly long for a single sentence.
"""

import math

from anura.config import TTS_TIMEOUT_BASE_S, TTS_TIMEOUT_MAX_S, TTS_TIMEOUT_PER_FRAGMENT_S

# gTTS splits text into requests of at most this many characters.
GTTS_FRAGMENT_CHARS = 100


def tts_timeout_seconds(text: str) -> int:
    """Return the watchdog budget, in whole seconds, for *text*.

    Budget = base + one allowance per gTTS fragment, capped so a pathological
    input cannot keep the UI in "generating" for an unbounded time.
    """
    fragments = max(1, math.ceil(len(text) / GTTS_FRAGMENT_CHARS))
    budget = TTS_TIMEOUT_BASE_S + fragments * TTS_TIMEOUT_PER_FRAGMENT_S
    return int(min(budget, TTS_TIMEOUT_MAX_S))
