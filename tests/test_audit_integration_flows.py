# tests/test_integration_flows.py
import pytest

pytest.importorskip("gi")

from unittest.mock import MagicMock, patch

from gi.repository import GLib

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
            # Create a mock error that looks like portal backend missing
            from gi.repository import Gio

            error = GLib.Error.new_literal(Gio.io_error_quark(), "Screenshot failed", Gio.IOErrorEnum.FAILED)

            # We need to mock the portal object itself
            mock_portal = MagicMock()
            mock_portal.take_screenshot_finish.side_effect = error
            service.portal = mock_portal

            # Call finish callback (simulating portal response)
            service.take_screenshot_finish(None, MagicMock(), ("eng", False))

            mock_fallback.assert_called_once_with("eng", False)
