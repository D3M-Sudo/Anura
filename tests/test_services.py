# tests/test_services.py
#
# Unit tests for Anura services
# No GTK/GLib required — pure Python only with mocks

from unittest.mock import Mock, patch

import pytest

import anura.services.tts as tts_module


class TestTTSServiceLanguageMapping:
    """Tests for TTSService language mapping logic without audio hardware."""

    @pytest.fixture(autouse=True)
    def isolate_gtts(self, monkeypatch):
        """Mock gTTS to avoid network calls and audio dependencies."""
        # Mock the gtts.lang.tts_langs function
        mock_langs = {
            "en": "English",
            "it": "Italian",
            "fr": "French",
            "de": "German",
            "es": "Spanish",
            "zh-CN": "Chinese (Simplified)",
            "zh-TW": "Chinese (Traditional)",
            "ja": "Japanese",
            "ko": "Korean"
        }
        mock_tts_langs = Mock(return_value=mock_langs)
        monkeypatch.setattr(tts_module.gtts.lang, "tts_langs", mock_tts_langs)

        # Mock Gst.is_initialized to avoid GStreamer dependency
        monkeypatch.setattr(tts_module.Gst, "is_initialized", Mock(return_value=False))
        monkeypatch.setattr(tts_module.Gst, "init", Mock())

        # Mock os.makedirs to avoid filesystem operations
        mock_makedirs = Mock()
        monkeypatch.setattr("os.makedirs", mock_makedirs)

    def test_map_tesseract_to_gtts_standard_codes(self):
        """Test mapping of standard Tesseract language codes to gTTS codes."""
        # Test common language codes
        assert tts_module.TTSService.map_tesseract_to_gtts("eng") == "en"
        assert tts_module.TTSService.map_tesseract_to_gtts("ita") == "it"
        assert tts_module.TTSService.map_tesseract_to_gtts("fra") == "fr"
        assert tts_module.TTSService.map_tesseract_to_gtts("deu") == "de"
        assert tts_module.TTSService.map_tesseract_to_gtts("spa") == "es"

    def test_map_tesseract_to_gtts_chinese_variants(self):
        """Test mapping of Chinese language variants."""
        assert tts_module.TTSService.map_tesseract_to_gtts("chi_sim") == "zh-CN"
        assert tts_module.TTSService.map_tesseract_to_gtts("chi_tra") == "zh-TW"

    def test_map_tesseract_to_gtts_east_asian(self):
        """Test mapping of East Asian languages."""
        assert tts_module.TTSService.map_tesseract_to_gtts("jpn") == "ja"
        assert tts_module.TTSService.map_tesseract_to_gtts("kor") == "ko"

    def test_map_tesseract_to_gtts_case_insensitive(self):
        """Test that mapping is case insensitive."""
        assert tts_module.TTSService.map_tesseract_to_gtts("ENG") == "en"
        assert tts_module.TTSService.map_tesseract_to_gtts("Eng") == "en"
        assert tts_module.TTSService.map_tesseract_to_gtts("ITA") == "it"
        assert tts_module.TTSService.map_tesseract_to_gtts("Ita") == "it"

    def test_map_tesseract_to_gtts_vertical_variants(self):
        """Test mapping of vertical writing variants."""
        assert tts_module.TTSService.map_tesseract_to_gtts("jpn_vert") == "ja"
        assert tts_module.TTSService.map_tesseract_to_gtts("kor_vert") == "ko"
        assert tts_module.TTSService.map_tesseract_to_gtts("chi_sim_vert") == "zh-CN"

    def test_map_tesseract_to_gtts_historical_variants(self):
        """Test mapping of historical language variants."""
        assert tts_module.TTSService.map_tesseract_to_gtts("lat") == "la"
        assert tts_module.TTSService.map_tesseract_to_gtts("grc") == "el"
        assert tts_module.TTSService.map_tesseract_to_gtts("enm") == "en"
        assert tts_module.TTSService.map_tesseract_to_gtts("frm") == "fr"

    def test_map_tesseract_to_gtts_2char_fallback(self):
        """Test fallback to 2-character codes when in supported languages."""
        # Mock supported languages to include a 2-char code not in LANG_MAP
        with patch.object(tts_module.TTSService, 'get_supported_gtts_languages') as mock_supported:
            mock_supported.return_value = {"en", "it", "fr", "de", "es", "ru"}

            # Test fallback to 2-char code when supported
            assert tts_module.TTSService.map_tesseract_to_gtts("rus") == "ru"

    def test_map_tesseract_to_gtts_unsupported_fallback(self):
        """Test fallback to English for unsupported languages."""
        # Mock supported languages to only include English
        with patch.object(tts_module.TTSService, 'get_supported_gtts_languages') as mock_supported:
            mock_supported.return_value = {"en"}

            # Test unsupported codes fall back to English
            assert tts_module.TTSService.map_tesseract_to_gtts("xyz") == "en"
            assert tts_module.TTSService.map_tesseract_to_gtts("unknown") == "en"

    def test_get_supported_gtts_languages_caching(self):
        """Test that gTTS languages are cached after first call."""
        # Clear the cache first
        tts_module.TTSService._gtts_languages = None

        # First call should fetch from gtts
        result1 = tts_module.TTSService.get_supported_gtts_languages()
        assert isinstance(result1, dict)
        assert "en" in result1

        # Second call should return cached result
        with patch.object(tts_module.gtts.lang, 'tts_langs') as mock_tts_langs:
            tts_module.TTSService._gtts_languages = None  # Reset cache
            tts_module.TTSService.get_supported_gtts_languages()
            # Should not call gtts.lang.tts_langs again
            mock_tts_langs.assert_not_called()

    def test_get_supported_gtts_languages_network_error(self):
        """Test graceful handling of network errors when fetching languages."""
        # Clear cache and mock network error
        tts_module.TTSService._gtts_languages = None

        with patch.object(tts_module.gtts.lang, 'tts_langs', side_effect=Exception("Network error")):
            result = tts_module.TTSService.get_supported_gtts_languages()
            # Should return empty dict on error
            assert result == {}

    @pytest.mark.gtk
    class TestTTSServiceIntegration:
        """Integration tests that require GTK (marked appropriately)."""

        def test_service_initialization(self):
            """Test TTSService can be initialized without errors."""
            # This test would require GTK/GStreamer, so mark with @pytest.mark.gtk
            # For now, just test that the class exists and can be instantiated with mocks
            with patch('os.makedirs'), \
                 patch('anura.services.tts.Gst.is_initialized', return_value=True), \
                 patch('anura.services.tts.Gst.init'):

                service = tts_module.TTSService()
                assert service is not None
                assert hasattr(service, 'LANG_MAP')
                assert isinstance(service.LANG_MAP, dict)


class TestLanguageManagerBasics:
    """Basic tests for LanguageManager without filesystem dependencies."""

    def test_language_mapping_completeness(self):
        """Test that all language codes in LANG_MAP have corresponding entries."""
        from anura.language_manager import language_manager

        # Test that common languages are mapped
        assert language_manager.get_language("eng") == "English"
        assert language_manager.get_language("ita") == "Italian"
        assert language_manager.get_language("fra") == "French"
        assert language_manager.get_language("deu") == "German"

        # Test that unknown codes return the code itself
        assert language_manager.get_language("unknown") == "unknown"

    def test_language_item_creation(self):
        """Test LanguageItem creation and properties."""
        from anura.types.language_item import LanguageItem

        item = LanguageItem(code="eng", title="English")
        assert item.code == "eng"
        assert item.title == "English"

    def test_get_language_item_valid_codes(self):
        """Test getting language items for valid codes."""
        from anura.language_manager import language_manager

        item = language_manager.get_language_item("eng")
        assert item is not None
        assert item.code == "eng"
        assert item.title == "English"

        # Test invalid code returns None
        item = language_manager.get_language_item("invalid")
        assert item is None
