# tests/test_phase2_a.py
import re
from unittest.mock import patch

import pytest

pytest.importorskip("gi")

import anura.config
from anura.types.download_state import DownloadState
from anura.types.language_item import LanguageItem


class TestConfig:
    def test_lang_code_pattern(self):
        assert re.match(anura.config.LANG_CODE_PATTERN, "eng")
        assert re.match(anura.config.LANG_CODE_PATTERN, "chi_sim")
        assert re.match(anura.config.LANG_CODE_PATTERN, "eng+ita")
        assert not re.match(anura.config.LANG_CODE_PATTERN, "a")  # too short
        assert not re.match(anura.config.LANG_CODE_PATTERN, "very_long_language_code_exceeding_limit")
        assert not re.match(anura.config.LANG_CODE_PATTERN, "eng; drop table")

    def test_get_tesseract_config_happy_path(self, tmp_path):
        tessdata_dir = tmp_path / "tessdata"
        tessdata_dir.mkdir()
        (tessdata_dir / "eng.traineddata").touch()

        with patch.object(anura.config, "TESSDATA_DIR", str(tessdata_dir)):
            config = anura.config.get_tesseract_config("eng")
            assert f'--tessdata-dir "{tessdata_dir}"' in config

    def test_get_tesseract_config_invalid_code(self):
        # Should fallback to eng
        config = anura.config.get_tesseract_config("invalid!")
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
    @pytest.mark.gtk
    def test_language_item_init(self):
        li = LanguageItem(code="fra", title="French", selected=True)
        assert li.code == "fra"
        assert li.title == "French"
        assert li.selected is True

    @pytest.mark.gtk
    def test_language_item_repr(self):
        li = LanguageItem(code="fra", title="French", selected=False)
        assert "French" in repr(li)
        assert "fra" in repr(li)
