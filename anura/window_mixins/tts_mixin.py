# This file is part of Anura.
# Copyright (C) 2022-2025 Andrey Maksimov (Frog)
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

class WindowTTSMixin:
    """Mixin class for AnuraWindow to handle TTS playback logic."""

    def on_listen(self) -> None:
        """Start TTS playback for the currently extracted text."""
        self.extracted_page.listen()

    def on_listen_cancel(self) -> None:
        """Stop any active TTS playback."""
        self.extracted_page._on_listen_stop()

    def on_listen_pause(self) -> None:
        """Pause/Resume any active TTS playback."""
        self.extracted_page.listen_pause()
