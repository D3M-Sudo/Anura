# This file is part of Anura.
# Copyright (C) 2022-2025 Andrey Maksimov (Frog)
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT


def __getattr__(name: str):
    if name == "TTSService":
        from anura.services.tts.service import TTSService

        return TTSService
    if name == "get_tts_service":
        from anura.services.tts.service import get_tts_service

        return get_tts_service
    if name == "AudioPlayer":
        from anura.services.tts.audio_player import AudioPlayer

        return AudioPlayer
    if name == "LanguageMapper":
        from anura.services.tts.language_mapper import LanguageMapper

        return LanguageMapper
    if name == "PipelineManager":
        from anura.services.tts.pipeline_manager import PipelineManager

        return PipelineManager
    if name == "SpeechGenerator":
        from anura.services.tts.speech_generator import SpeechGenerator

        return SpeechGenerator
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["AudioPlayer", "LanguageMapper", "PipelineManager", "SpeechGenerator", "TTSService", "get_tts_service"]
