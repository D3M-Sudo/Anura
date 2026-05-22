# This file is part of Anura.
# Copyright (C) 2022-2025 Andrey Maksimov (Frog)
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import pytest

pytest.importorskip("gi")

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


@pytest.mark.gtk
class TestLanguageManagerInitTessdata:
    """Tests for LanguageManager.init_tessdata() method."""

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path, monkeypatch):
        """Set up test environment and provide language_manager."""
        from anura.language_manager import get_language_manager

        self.language_manager = get_language_manager()
        self.tmp_path = tmp_path
        self.monkeypatch = monkeypatch

    def test_init_tessdata_creates_directory(self):
        """init_tessdata() creates tessdata directory if it doesn't exist."""
        import anura.language_manager as lm_module

        # Set tessdata to a non-existent path
        fake_tessdata = self.tmp_path / "nonexistent" / "tessdata"
        self.monkeypatch.setattr(lm_module, "TESSDATA_DIR", str(fake_tessdata))

        # Directory should not exist initially
        assert not fake_tessdata.exists()

        # Call init_tessdata - should create directory
        self.language_manager.init_tessdata()

        # Directory should now exist
        assert fake_tessdata.exists()

    def test_init_tessdata_handles_existing_directory(self):
        """init_tessdata() handles existing tessdata directory gracefully."""
        import anura.language_manager as lm_module

        fake_tessdata = self.tmp_path / "existing" / "tessdata"
        fake_tessdata.mkdir(parents=True)

        self.monkeypatch.setattr(lm_module, "TESSDATA_DIR", str(fake_tessdata))

        # Should not raise exception for existing directory
        self.language_manager.init_tessdata()

        # Directory should still exist
        assert fake_tessdata.exists()

    def test_init_tessdata_cleans_orphaned_temp_files(self):
        """init_tessdata() cleans up orphaned .tmp files."""
        import anura.language_manager as lm_module

        fake_tessdata = self.tmp_path / "cleanup_test" / "tessdata"
        fake_tessdata.mkdir(parents=True)

        # Create some orphaned temp files
        (fake_tessdata / "orphaned1.tmp").write_bytes(b"temp data")
        (fake_tessdata / "orphaned2.tmp").write_bytes(b"temp data")
        (fake_tessdata / "valid.traineddata").write_bytes(b"model data")

        self.monkeypatch.setattr(lm_module, "TESSDATA_DIR", str(fake_tessdata))

        # Call init_tessdata - should clean temp files
        self.language_manager.init_tessdata()

        # Temp files should be removed, valid files should remain
        assert not (fake_tessdata / "orphaned1.tmp").exists()
        assert not (fake_tessdata / "orphaned2.tmp").exists()
        assert (fake_tessdata / "valid.traineddata").exists()

    def test_init_tessdata_handles_permission_errors(self):
        """init_tessdata() handles permission errors gracefully."""
        from unittest.mock import patch

        import anura.language_manager as lm_module

        fake_tessdata = self.tmp_path / "restricted" / "tessdata"
        fake_tessdata.mkdir(parents=True)

        self.monkeypatch.setattr(lm_module, "TESSDATA_DIR", str(fake_tessdata))

        # Mock os.listdir to raise PermissionError
        with patch("os.listdir", side_effect=PermissionError("Permission denied")):
            # Should not raise exception
            self.language_manager.init_tessdata()

        # Directory should still exist
        assert fake_tessdata.exists()

    def test_init_tessdata_thread_safety(self):
        """init_tessdata() is thread-safe with lock protection."""
        import anura.language_manager as lm_module

        fake_tessdata = self.tmp_path / "thread_safe" / "tessdata"
        self.monkeypatch.setattr(lm_module, "TESSDATA_DIR", str(fake_tessdata))

        # Call init_tessdata multiple times concurrently
        import threading

        threads = []
        exceptions = []

        def call_init():
            try:
                self.language_manager.init_tessdata()
            except Exception as e:
                exceptions.append(e)

        # Start multiple threads
        for _ in range(5):
            thread = threading.Thread(target=call_init)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # No exceptions should have occurred
        assert len(exceptions) == 0
        # Directory should exist
        assert fake_tessdata.exists()
