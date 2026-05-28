# This file is part of Anura.
# Copyright (C) 2022-2025 Andrey Maksimov (Frog)
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import pytest

pytest.importorskip("gi")

from unittest.mock import MagicMock, patch

from anura.services.screenshot_service import ScreenshotService
from anura.services.share_service import ShareService
from anura.services.tts import TTSService


class TestIntegrationFlows:
    @pytest.mark.gtk
    def test_ocr_to_share_flow(self):
        # This test simulates the flow: image decoded -> emitted decoded signal -> shared
        screenshot_service = ScreenshotService()
        share_service = ShareService()

        decoded_text = "Extracted OCR text for testing"

        # Track if share was called
        share_called = []
        with patch.object(share_service, "share") as mock_share:

            def on_decoded(service, text, copy, ocr_result):
                share_service.share("email", text)
                share_called.append(text)

            screenshot_service.connect("decoded", on_decoded)

            # Manually trigger decoded signal (simulating successful OCR)
            # Signal signature: (str, bool, object) — text, copy_requested, ocr_result
            screenshot_service.emit("decoded", decoded_text, False, None)

            assert decoded_text in share_called
            mock_share.assert_called_once_with("email", decoded_text)

    @pytest.mark.gtk
    def test_ocr_to_tts_flow(self):
        screenshot_service = ScreenshotService()
        tts_service = TTSService()

        extracted_text = "Hello, this is OCR text."

        # Track if TTS generate was called
        with patch.object(tts_service, "generate", return_value="/tmp/test.mp3") as mock_gen:

            def on_decoded(service, text, copy, ocr_result):
                tts_service.generate(text, lang="en")

            screenshot_service.connect("decoded", on_decoded)

            # Signal signature: (str, bool, object) — text, copy_requested, ocr_result
            screenshot_service.emit("decoded", extracted_text, False, None)

            mock_gen.assert_called_once_with(extracted_text, lang="en")

    @pytest.mark.gtk
    def test_portal_failure_to_fallback_flow(self):
        # Simulates portal failure triggering host fallback
        service = ScreenshotService()

        with patch.object(service, "fallback_provider") as mock_fallback_provider:
            # Create a mock error that looks like portal backend missing

            # Mock the provider's capture method to simulate failure
            mock_provider = MagicMock()

            def capture_side_effect(lang, copy, callback):
                callback(False, None, "Screenshot failed: generic error")
            mock_provider.capture = capture_side_effect
            service.provider = mock_provider

            # Call capture which will trigger fallback
            service.capture("eng", False)

            # Verify fallback was invoked
            mock_fallback_provider.capture.assert_called()
