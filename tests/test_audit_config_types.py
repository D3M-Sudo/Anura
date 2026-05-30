# This file is part of Anura.
# Copyright (C) 2022-2025 Andrey Maksimov (Frog)
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

from pathlib import Path
import re
import sys
from unittest.mock import MagicMock

import pytest

# Mock gi for headless environments
mock_gi = MagicMock()
sys.modules["gi"] = mock_gi
sys.modules["gi.repository"] = MagicMock()
sys.modules["gi.repository.Gio"] = MagicMock()
sys.modules["gi.repository.GLib"] = MagicMock()
sys.modules["gi.repository.GObject"] = MagicMock()

import anura.config  # noqa: E402
from anura.models.download_state import DownloadState  # noqa: E402
from anura.models.language_item import LanguageItem  # noqa: E402
import anura.services.language_manager  # noqa: E402


class TestConfig:
    @pytest.fixture(autouse=True)
    def mock_lm_dependencies(self, monkeypatch):
        import anura.services.language_manager as lm

        mock_settings = MagicMock()
        mock_settings.get_string.return_value = "standard"
        monkeypatch.setattr(lm, "settings", mock_settings)

        self.mock_mgr = MagicMock()
        monkeypatch.setattr(lm, "get_language_manager", lambda: self.mock_mgr)

        return lm

    def test_lang_code_pattern(self):
        assert re.match(anura.config.LANG_CODE_PATTERN, "eng")
        assert re.match(anura.config.LANG_CODE_PATTERN, "chi_sim")
        assert re.match(anura.config.LANG_CODE_PATTERN, "eng+ita")
        assert not re.match(anura.config.LANG_CODE_PATTERN, "a")  # too short
        assert not re.match(anura.config.LANG_CODE_PATTERN, "very_long_language_code_exceeding_limit")
        assert not re.match(anura.config.LANG_CODE_PATTERN, "eng; drop table")

    def test_get_tesseract_config_happy_path(self, tmp_path, mock_lm_dependencies):
        lm = mock_lm_dependencies
        tessdata_dir = tmp_path / "tessdata"
        tessdata_dir.mkdir()
        (tessdata_dir / "eng.traineddata").touch()

        self.mock_mgr._get_model_quality_dir.return_value = tessdata_dir

        config = lm.get_tesseract_config("eng")
        assert f'--tessdata-dir "{tessdata_dir}"' in config

    def test_get_tesseract_config_invalid_code(self, mock_lm_dependencies):
        lm = mock_lm_dependencies
        # Should fallback to eng
        self.mock_mgr._get_model_quality_dir.return_value = Path("/tmp")

        config = lm.get_tesseract_config("invalid!")
        assert "--psm 3" in config


class TestDownloadState:
    def test_percentage_zero_total(self):
        ds = DownloadState(total=0, progress=10)
        assert ds.percentage == 0.0

    def test_percentage_happy_path(self):
        ds = DownloadState(total=100, progress=50)
        assert ds.percentage == 50.0

    def test_percentage_boundary(self):
        ds = DownloadState(total=100, progress=100)
        assert ds.percentage == 100.0
        ds = DownloadState(total=100, progress=0)
        assert ds.percentage == 0.0


class TestLanguageItem:
    @pytest.mark.skip(reason="Needs real GObject")
    def test_language_item_init(self):
        li = LanguageItem(code="fra", title="French", selected=True)
        assert li.code == "fra"
        assert li.title == "French"
        assert li.selected is True

    @pytest.mark.skip(reason="Needs real GObject")
    def test_language_item_repr(self):
        li = LanguageItem(code="fra", title="French", selected=False)
        assert "French" in repr(li)
        assert "fra" in repr(li)
