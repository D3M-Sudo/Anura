# tests/test_tts.py
#
# Unit tests for anura/services/tts.py
# Focused on pure-Python logic: language mapping, fallbacks.
# GStreamer playback tests are excluded (require audio hardware + display).

import pytest


@pytest.mark.gtk
class TestMapTesseractToGtts:
    """Tests for TTSService.map_tesseract_to_gtts() — no network, no GStreamer."""

    @pytest.fixture(autouse=True)
    def patch_gtts_langs(self, monkeypatch):
        """
        Stub out network call to gTTS API.
        Returns a minimal set of supported languages for tests.
        """
        supported = {
            "en": "English", "it": "Italian", "fr": "French",
            "de": "German", "es": "Spanish", "ja": "Japanese",
            "zh-CN": "Chinese (Simplified)", "ar": "Arabic",
        }
        from anura.services import tts as tts_module
        monkeypatch.setattr(tts_module.TTSService, "_gtts_languages", supported)

    @pytest.fixture
    def svc(self):
        from anura.services.tts import TTSService
        return TTSService

    # ── Direct LANG_MAP lookups ───────────────────────────────────────────────

    def test_eng_maps_to_en(self, svc):
        assert svc.map_tesseract_to_gtts("eng") == "en"

    def test_ita_maps_to_it(self, svc):
        assert svc.map_tesseract_to_gtts("ita") == "it"

    def test_jpn_maps_to_ja(self, svc):
        assert svc.map_tesseract_to_gtts("jpn") == "ja"

    def test_chi_sim_maps_to_zh_cn(self, svc):
        assert svc.map_tesseract_to_gtts("chi_sim") == "zh-CN"

    def test_jpn_vert_maps_to_ja(self, svc):
        """Vertical variant codes should map to the base language."""
        assert svc.map_tesseract_to_gtts("jpn_vert") == "ja"

    def test_case_insensitive(self, svc):
        """Input is normalized to lowercase before lookup."""
        assert svc.map_tesseract_to_gtts("ENG") == "en"
        assert svc.map_tesseract_to_gtts("ITA") == "it"

    # ── Fallback behaviour ────────────────────────────────────────────────────

    def test_unknown_code_falls_back_to_en(self, svc):
        """Unknown codes that are not in LANG_MAP fall back to English."""
        result = svc.map_tesseract_to_gtts("xyz_unknown_code")
        assert result == "en"

    def test_empty_string_falls_back_to_en(self, svc):
        result = svc.map_tesseract_to_gtts("")
        assert result == "en"


@pytest.mark.gtk
class TestDownloadStatePercentage:
    """Tests for DownloadState.percentage property."""

    def test_normal_percentage(self):
        from anura.types.download_state import DownloadState
        ds = DownloadState(total=1000, progress=250)
        assert ds.percentage == 25.0

    def test_zero_total_returns_zero(self):
        from anura.types.download_state import DownloadState
        ds = DownloadState(total=0, progress=0)
        assert ds.percentage == 0.0

    def test_complete_download(self):
        from anura.types.download_state import DownloadState
        ds = DownloadState(total=500, progress=500)
        assert ds.percentage == 100.0

    def test_negative_total_returns_zero(self):
        """Guard against malformed data from server responses."""
        from anura.types.download_state import DownloadState
        ds = DownloadState(total=-1, progress=0)
        assert ds.percentage == 0.0
