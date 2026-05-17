import os
from unittest.mock import patch
import pytest
from anura.config import get_tesseract_config, TESSDATA_DIR, TESSDATA_SYSTEM_DIR

class TestAuditConfig:
    def test_get_tesseract_config_valid(self):
        config = get_tesseract_config("eng")
        assert "--tessdata-dir" in config

    def test_get_tesseract_config_invalid_code(self):
        config = get_tesseract_config("invalid; rm -rf /")
        assert "--tessdata-dir" in config

    def test_get_tesseract_config_multi_lang(self):
        config = get_tesseract_config("eng+fra")
        assert "--tessdata-dir" in config

    def test_get_tesseract_config_priority(self, tmp_path):
        user_dir = tmp_path / "user_tessdata"
        system_dir = tmp_path / "system_tessdata"
        user_dir.mkdir()
        system_dir.mkdir()

        user_model = user_dir / "testlang.traineddata"
        system_model = system_dir / "testlang.traineddata"

        system_model.write_text("system")

        with patch("anura.config.TESSDATA_DIR", str(user_dir)), \
             patch("anura.config.TESSDATA_SYSTEM_DIR", str(system_dir)):

            config = get_tesseract_config("testlang")
            assert f'--tessdata-dir "{system_dir}"' in config

            user_model.write_text("user")
            config = get_tesseract_config("testlang")
            assert f'--tessdata-dir "{user_dir}"' in config

            config = get_tesseract_config("nonexistent")
            assert f'--tessdata-dir "{user_dir}"' in config
