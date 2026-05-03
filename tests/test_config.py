# tests/test_config.py
#
# Unit tests for anura/config.py
# No GTK/GLib required — pure Python only.

import re

import pytest


@pytest.mark.gtk
class TestLangCodePattern:
    """Tests for LANG_CODE_PATTERN — the security boundary before Tesseract."""

    @pytest.fixture(autouse=True)
    def import_pattern(self):
        from anura.config import LANG_CODE_PATTERN
        self.pattern = LANG_CODE_PATTERN

    def _match(self, code: str) -> bool:
        return bool(re.match(self.pattern, code))

    # ── Valid codes ────────────────────────────────────────────────────────────

    def test_standard_3letter(self):
        assert self._match("eng")
        assert self._match("ita")
        assert self._match("fra")

    def test_composite_code(self):
        # chi_sim, chi_tra, aze_cyrl — used in LANG_MAP
        assert self._match("chi_sim")
        assert self._match("chi_tra")
        assert self._match("aze_cyrl")

    def test_2letter_minimum(self):
        assert self._match("en")

    def test_8letter_maximum(self):
        assert self._match("abcdefgh")  # exactly 8 chars

    def test_uppercase_allowed(self):
        assert self._match("ENG")
        assert self._match("Chi_Sim")

    # ── Invalid / injection attempts ──────────────────────────────────────────

    def test_empty_string(self):
        assert not self._match("")

    def test_single_char(self):
        assert not self._match("e")

    def test_too_long(self):
        assert not self._match("abcdefghi")  # 9 chars

    def test_shell_injection_semicolon(self):
        assert not self._match("eng;rm -rf /")

    def test_shell_injection_backtick(self):
        assert not self._match("eng`id`")

    def test_path_traversal(self):
        assert not self._match("../etc/passwd")

    def test_space_not_allowed(self):
        assert not self._match("eng ita")

    def test_hyphen_not_allowed(self):
        # gTTS uses hyphens (zh-CN) but Tesseract uses underscore
        assert not self._match("zh-CN")

    def test_dot_not_allowed(self):
        assert not self._match("eng.exe")


@pytest.mark.gtk
class TestGetTesseractConfig:
    """Tests for get_tesseract_config() path resolution logic."""

    def test_user_model_takes_priority(self, tmp_path, monkeypatch):
        """User tessdata directory has priority over system directory."""
        user_dir = tmp_path / "user-tessdata"
        system_dir = tmp_path / "system-tessdata"
        user_dir.mkdir()
        system_dir.mkdir()
        (user_dir / "ita.traineddata").write_bytes(b"fake")
        (system_dir / "ita.traineddata").write_bytes(b"fake")

        monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
        import anura.config as cfg
        monkeypatch.setattr(cfg, "TESSDATA_DIR", str(user_dir))
        monkeypatch.setattr(cfg, "TESSDATA_SYSTEM_DIR", str(system_dir))

        result = cfg.get_tesseract_config("ita")
        assert str(user_dir) in result

    def test_fallback_to_system_dir(self, tmp_path, monkeypatch):
        """Falls back to system tessdata when user model is missing."""
        user_dir = tmp_path / "user-tessdata"
        system_dir = tmp_path / "system-tessdata"
        user_dir.mkdir()
        system_dir.mkdir()
        (system_dir / "eng.traineddata").write_bytes(b"fake")

        import anura.config as cfg
        monkeypatch.setattr(cfg, "TESSDATA_DIR", str(user_dir))
        monkeypatch.setattr(cfg, "TESSDATA_SYSTEM_DIR", str(system_dir))

        result = cfg.get_tesseract_config("eng")
        assert str(system_dir) in result

    def test_invalid_lang_code_defaults_to_eng(self, tmp_path, monkeypatch):
        """Invalid lang_code is rejected and falls back to 'eng'."""
        import anura.config as cfg
        monkeypatch.setattr(cfg, "TESSDATA_DIR", str(tmp_path))
        monkeypatch.setattr(cfg, "TESSDATA_SYSTEM_DIR", str(tmp_path))

        # Should not raise, should log error and use 'eng'
        result = cfg.get_tesseract_config("../../etc/passwd")
        assert result is not None
        assert "--psm 3" in result
        assert "--oem 1" in result

    def test_config_contains_psm_and_oem(self, tmp_path, monkeypatch):
        """Config string always contains Tesseract mode flags."""
        import anura.config as cfg
        monkeypatch.setattr(cfg, "TESSDATA_DIR", str(tmp_path))
        monkeypatch.setattr(cfg, "TESSDATA_SYSTEM_DIR", str(tmp_path))

        result = cfg.get_tesseract_config("eng")
        assert "--psm 3" in result
        assert "--oem 1" in result
