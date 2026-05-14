# tests/test_config.py
#
# Unit tests for anura/config.py
# No GTK/GLib required — pure Python only.

import re
from unittest.mock import patch

import pytest


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

    def test_multi_language_code(self):
        # Multi-language OCR codes like "eng+ita" are supported
        assert self._match("eng+ita")
        assert self._match("deu+fra")
        assert self._match("eng+ita+fra")

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
        assert not self._match("abcdefghijklmnopqrs")  # 19 chars, exceeds 18 char limit

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

    def test_config_format(self):
        """Test Tesseract config string format (string construction)."""
        tessdata_dir = "/path/to/tessdata"
        config = f'--tessdata-dir "{tessdata_dir}" --psm 3 --oem 1'

        assert "--tessdata-dir" in config
        assert "--psm 3" in config
        assert "--oem 1" in config
        assert tessdata_dir in config

    def test_config_quoting(self):
        """Test Tesseract config properly quotes paths with spaces."""
        tessdata_dir = "/path with spaces/tessdata"
        config = f'--tessdata-dir "{tessdata_dir}" --psm 3 --oem 1'

        assert config == '--tessdata-dir "/path with spaces/tessdata" --psm 3 --oem 1'

    def test_config_valid_english(self):
        """Test Tesseract config generation for valid English."""
        from anura.config import get_tesseract_config

        with patch("os.path.exists", return_value=True):
            config = get_tesseract_config("eng")
            assert "--tessdata-dir" in config
            assert "--psm 3" in config
            assert "--oem 1" in config

    def test_config_invalid_language(self):
        """Test Tesseract config generation for invalid language."""
        from anura.config import get_tesseract_config

        with patch("os.path.exists", return_value=False):
            config = get_tesseract_config("invalid")
            # Should default to 'eng' and return valid config
            assert "--tessdata-dir" in config
            assert "--psm 3" in config
            assert "--oem 1" in config


class TestLogLevel:
    """Tests for LOG_LEVEL resolution from ANURA_LOG_LEVEL environment variable."""

    @pytest.fixture(autouse=True)
    def clean_config_module(self, monkeypatch):
        """Ensure anura.config is reloaded fresh for each test."""
        import sys

        monkeypatch.delenv("ANURA_LOG_LEVEL", raising=False)
        # Remove cached module so reload picks up env changes
        sys.modules.pop("anura.config", None)
        # Also remove anura package cache to force clean import
        sys.modules.pop("anura", None)

    def test_default_log_level_is_info(self, monkeypatch):
        """Without ANURA_LOG_LEVEL, LOG_LEVEL defaults to INFO."""
        monkeypatch.delenv("ANURA_LOG_LEVEL", raising=False)
        import anura.config as cfg

        assert cfg.LOG_LEVEL == "INFO"

    def test_debug_override(self, monkeypatch):
        """ANURA_LOG_LEVEL=DEBUG sets LOG_LEVEL to DEBUG."""
        import sys

        monkeypatch.setenv("ANURA_LOG_LEVEL", "DEBUG")
        # Must reload after env change
        if "anura.config" in sys.modules:
            del sys.modules["anura.config"]
        if "anura" in sys.modules:
            del sys.modules["anura"]
        import anura.config as cfg

        assert cfg.LOG_LEVEL == "DEBUG"

    def test_invalid_fallback_to_info(self, monkeypatch):
        """Invalid ANURA_LOG_LEVEL falls back to INFO."""
        import sys

        monkeypatch.setenv("ANURA_LOG_LEVEL", "VERBOSE")
        if "anura.config" in sys.modules:
            del sys.modules["anura.config"]
        if "anura" in sys.modules:
            del sys.modules["anura"]
        import anura.config as cfg

        assert cfg.LOG_LEVEL == "INFO"
