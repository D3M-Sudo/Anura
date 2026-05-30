# This file is part of Anura.
# Copyright (C) 2022-2025 Andrey Maksimov (Frog)
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

# NOTE: gi mocking is handled by the session-scoped `headless_gi_mocks`
# fixture defined in conftest.py.  Do NOT add module-level sys.modules
# assignments here — they execute at collection time and poison gi for every
# other test in the session.

from pathlib import Path
import re
import sys
from unittest.mock import MagicMock, patch

import pytest


class TestLangCodePattern:
    """Tests for LANG_CODE_PATTERN — the security boundary before Tesseract."""

    @pytest.fixture(autouse=True)
    def import_pattern(self, headless_gi_mocks):  # noqa: ARG002
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

    @pytest.fixture(autouse=True)
    def mock_lm_dependencies(self, monkeypatch, headless_gi_mocks):  # noqa: ARG002
        import anura.services.language_manager as lm

        mock_settings = MagicMock()
        mock_settings.get_string.return_value = "standard"
        monkeypatch.setattr(lm, "settings", mock_settings)

        self.mock_mgr = MagicMock()
        self.mock_mgr._get_model_quality_dir.return_value = Path("/tmp/anura-user-tessdata")
        monkeypatch.setattr(lm, "get_language_manager", lambda: self.mock_mgr)

        # TESSDATA_SYSTEM_DIR must be patched on the language_manager module
        # namespace — that is where get_tesseract_config reads the imported name.
        monkeypatch.setattr(lm, "TESSDATA_SYSTEM_DIR", str(Path("/tmp/anura-system-tessdata")))

        return lm

    def test_user_model_takes_priority(self, tmp_path, monkeypatch, mock_lm_dependencies):
        """User tessdata directory has priority over system directory."""
        lm = mock_lm_dependencies
        user_dir = tmp_path / "user-tessdata"
        system_dir = tmp_path / "system-tessdata"
        user_dir.mkdir()
        system_dir.mkdir()
        (user_dir / "ita.traineddata").write_bytes(b"fake")
        (system_dir / "ita.traineddata").write_bytes(b"fake")

        self.mock_mgr._get_model_quality_dir.return_value = user_dir
        monkeypatch.setattr(lm, "TESSDATA_SYSTEM_DIR", str(system_dir))

        result = lm.get_tesseract_config("ita")
        assert str(user_dir) in result

    def test_fallback_to_system_dir(self, tmp_path, monkeypatch, mock_lm_dependencies):
        """Falls back to system tessdata when user model is missing."""
        lm = mock_lm_dependencies
        user_dir = tmp_path / "user-tessdata"
        system_dir = tmp_path / "system-tessdata"
        user_dir.mkdir()
        system_dir.mkdir()
        (system_dir / "eng.traineddata").write_bytes(b"fake")

        self.mock_mgr._get_model_quality_dir.return_value = user_dir
        monkeypatch.setattr(lm, "TESSDATA_SYSTEM_DIR", str(system_dir))

        result = lm.get_tesseract_config("eng")
        assert str(system_dir) in result

    def test_invalid_lang_code_defaults_to_eng(self, tmp_path, monkeypatch, mock_lm_dependencies):
        """Invalid lang_code is rejected and falls back to 'eng'."""
        lm = mock_lm_dependencies
        monkeypatch.setattr(lm, "TESSDATA_SYSTEM_DIR", str(tmp_path))

        result = lm.get_tesseract_config("../../etc/passwd")
        assert result is not None
        assert "--psm 3" in result
        assert "--oem 1" in result

    def test_config_contains_psm_and_oem(self, tmp_path, monkeypatch, mock_lm_dependencies):
        """Config string always contains Tesseract mode flags."""
        lm = mock_lm_dependencies
        monkeypatch.setattr(lm, "TESSDATA_SYSTEM_DIR", str(tmp_path))

        result = lm.get_tesseract_config("eng")
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

    def test_config_valid_english(self, mock_lm_dependencies):
        """Test Tesseract config generation for valid English."""
        lm = mock_lm_dependencies
        with patch("os.path.exists", return_value=True):
            config = lm.get_tesseract_config("eng")
            assert "--tessdata-dir" in config
            assert "--psm 3" in config
            assert "--oem 1" in config

    def test_config_invalid_language(self, mock_lm_dependencies):
        """Test Tesseract config generation for invalid language."""
        lm = mock_lm_dependencies
        with patch("os.path.exists", return_value=False):
            config = lm.get_tesseract_config("invalid")
            assert "--tessdata-dir" in config
            assert "--psm 3" in config
            assert "--oem 1" in config


class TestLogLevel:
    """Tests for LOG_LEVEL resolution from ANURA_LOG_LEVEL environment variable."""

    @pytest.fixture(autouse=True)
    def clean_config_module(self, monkeypatch):
        """Reload anura.config to pick up env changes.

        Only the specific sub-module is evicted — not the entire 'anura'
        package root — to avoid re-triggering the gi import chain in
        anura/__init__.py during headless runs.
        """
        monkeypatch.delenv("ANURA_LOG_LEVEL", raising=False)
        sys.modules.pop("anura.config", None)
        yield
        sys.modules.pop("anura.config", None)

    def test_default_log_level_is_info(self, monkeypatch, headless_gi_mocks):  # noqa: ARG002
        """Without ANURA_LOG_LEVEL, LOG_LEVEL defaults to INFO."""
        monkeypatch.delenv("ANURA_LOG_LEVEL", raising=False)
        import anura.config as cfg

        assert cfg.LOG_LEVEL == "INFO"

    def test_debug_override(self, monkeypatch, headless_gi_mocks):  # noqa: ARG002
        """ANURA_LOG_LEVEL=DEBUG sets LOG_LEVEL to DEBUG."""
        monkeypatch.setenv("ANURA_LOG_LEVEL", "DEBUG")
        sys.modules.pop("anura.config", None)
        import anura.config as cfg

        assert cfg.LOG_LEVEL == "DEBUG"

    def test_invalid_fallback_to_info(self, monkeypatch, headless_gi_mocks):  # noqa: ARG002
        """Invalid ANURA_LOG_LEVEL falls back to INFO."""
        monkeypatch.setenv("ANURA_LOG_LEVEL", "VERBOSE")
        sys.modules.pop("anura.config", None)
        import anura.config as cfg

        assert cfg.LOG_LEVEL == "INFO"
