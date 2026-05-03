# tests/test_language_manager.py
#
# Unit tests for anura/language_manager.py
# Focused on pure-Python logic: language mapping, ISO code lookups.
# GTK, network, and file I/O operations are excluded.

import pytest


@pytest.mark.gtk
class TestLanguageManager:
    """Tests for LanguageManager pure-Python methods."""

    @pytest.fixture(autouse=True)
    def language_manager(self):
        """Provide LanguageManager singleton for tests."""
        from anura.language_manager import language_manager
        return language_manager

    def test_get_language_returns_name(self, language_manager):
        """get_language('eng') returns a non-empty string."""
        result = language_manager.get_language("eng")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_get_language_unknown_returns_code(self, language_manager):
        """get_language('xyz_unknown') returns the code as fallback."""
        result = language_manager.get_language("xyz_unknown")
        assert result == "xyz_unknown"

    def test_get_language_item_returns_language_item(self, language_manager):
        """get_language_item('eng') returns a LanguageItem with code='eng'."""
        from anura.types.language_item import LanguageItem

        result = language_manager.get_language_item("eng")
        assert isinstance(result, LanguageItem)
        assert result.code == "eng"
        assert len(result.title) > 0

    def test_get_language_item_unknown_returns_none(self, language_manager):
        """get_language_item('xyz_unknown') returns None."""
        result = language_manager.get_language_item("xyz_unknown")
        assert result is None

    def test_get_available_codes_contains_eng_and_ita(self, language_manager):
        """get_available_codes() includes 'eng' and 'ita'."""
        codes = language_manager.get_available_codes()
        assert "eng" in codes
        assert "ita" in codes

    def test_get_language_code_reverse_lookup(self, language_manager):
        """get_language_code('English') returns 'eng'."""
        result = language_manager.get_language_code("English")
        assert result == "eng"

    def test_get_downloaded_codes_excludes_osd(self, tmp_path, monkeypatch, language_manager):
        """osd.traineddata never appears in results."""
        # Create fake tessdata directory with osd.traineddata
        fake_tessdata = tmp_path / "tessdata"
        fake_tessdata.mkdir()
        (fake_tessdata / "osd.traineddata").write_bytes(b"fake")
        (fake_tessdata / "eng.traineddata").write_bytes(b"fake")

        # Monkeypatch TESSDATA_DIR
        from anura import language_manager as lm_module
        monkeypatch.setattr(lm_module, "TESSDATA_DIR", str(fake_tessdata))
        monkeypatch.setattr(lm_module, "TESSDATA_SYSTEM_DIR", str(fake_tessdata))

        # Force cache refresh
        language_manager._need_update_cache = True

        codes = language_manager.get_downloaded_codes(force=True)
        assert "osd" not in codes
        assert "eng" in codes

    def test_get_downloaded_codes_includes_system_dir(self, tmp_path, monkeypatch, language_manager):
        """Models in TESSDATA_SYSTEM_DIR are included."""
        # Create separate user and system directories
        user_dir = tmp_path / "user_tessdata"
        system_dir = tmp_path / "system_tessdata"
        user_dir.mkdir()
        system_dir.mkdir()

        # Only system has the model
        (system_dir / "ita.traineddata").write_bytes(b"fake")

        # Monkeypatch directories
        from anura import language_manager as lm_module
        monkeypatch.setattr(lm_module, "TESSDATA_DIR", str(user_dir))
        monkeypatch.setattr(lm_module, "TESSDATA_SYSTEM_DIR", str(system_dir))

        # Force cache refresh
        language_manager._need_update_cache = True

        codes = language_manager.get_downloaded_codes(force=True)
        assert "ita" in codes
