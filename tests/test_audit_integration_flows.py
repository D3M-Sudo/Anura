# This file is part of Anura.
# Copyright (C) 2022-2025 Andrey Maksimov (Frog)
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import pytest

pytest.importorskip("gi")

from unittest.mock import patch

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

            def on_decoded(service, text, copy):
                share_service.share("email", text)
                share_called.append(text)

            screenshot_service.connect("decoded", on_decoded)

            # Manually trigger decoded signal (simulating successful OCR)
            screenshot_service.emit("decoded", decoded_text, False)

            assert decoded_text in share_called
            mock_share.assert_called_once_with("email", decoded_text)

    @pytest.mark.gtk
    def test_ocr_to_tts_flow(self):
        screenshot_service = ScreenshotService()
        tts_service = TTSService()

        extracted_text = "Hello, this is OCR text."

        # Track if TTS generate was called
        with patch.object(tts_service, "generate", return_value="/tmp/test.mp3") as mock_gen:

            def on_decoded(service, text, copy):
                tts_service.generate(text, lang="en")

            screenshot_service.connect("decoded", on_decoded)

            screenshot_service.emit("decoded", extracted_text, False)

            mock_gen.assert_called_once_with(extracted_text, lang="en")

    @pytest.mark.gtk
    def test_portal_failure_to_fallback_flow(self):
        # Simulates portal failure triggering host fallback
        service = ScreenshotService()

        with patch.object(service, "_try_host_screenshot_fallback") as mock_fallback:
            # The flow is now ScreenshotService.capture -> PortalProvider.capture -> PortalProvider._on_finish
            # which calls the callback with error -> ScreenshotService._on_capture_result
            # -> _try_host_screenshot_fallback (if generic failure)

            # Manually trigger the callback logic in ScreenshotService
            # This is cleaner than mocking the whole Gio.AsyncResult chain
            service._is_capturing = True
            # In current implementation, _on_capture_result is a closure in capture()
            # but we can test the fallback logic by simulating the generic error.

            # Get the actual capture method and mock its internal callback
            with patch("anura.services.screenshot.portal_provider.PortalProvider.capture") as mock_portal_cap:
                def side_effect(lang, copy, callback):
                    callback(False, None, "Screenshot failed")

                mock_portal_cap.side_effect = side_effect

                service.capture("eng", False)

            mock_fallback.assert_called_once_with("eng", False)
