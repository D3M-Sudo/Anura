#!/usr/bin/env python3
# tests/test_tessdata_consistency.py
"""Tests for build-aux/check_tessdata_consistency.py."""

import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "build-aux"))
import check_tessdata_consistency as checker

BASE_URL = "https://github.com/tesseract-ocr/tessdata_best/raw/4.1.0/"


@pytest.fixture(autouse=True)
def small_expected_inventory(monkeypatch: pytest.MonkeyPatch) -> None:
    """Use a small synthetic inventory; production constants remain 489."""
    monkeypatch.setattr(
        checker,
        "EXPECTED_REPOSITORY_COUNTS",
        {"tessdata": 1, "tessdata_best": 1, "tessdata_fast": 1},
    )


def _write_config(tmp_path: Path, *, alias: bool = True) -> Path:
    config = tmp_path / "config.py"
    fast_assignment = (
        'TESSDATA_FAST_URL = "https://github.com/tesseract-ocr/tessdata_fast/raw/4.1.0/"\n'
        "TESSDATA_STANDARD_URL = TESSDATA_FAST_URL"
        if alias
        else 'TESSDATA_STANDARD_URL = "https://github.com/tesseract-ocr/tessdata_fast/raw/4.1.0/"'
    )
    config.write_text(
        'TESSDATA_URL = "https://github.com/tesseract-ocr/tessdata/raw/4.1.0/"\n'
        f'TESSDATA_BEST_URL = "{BASE_URL}"\n'
        f"{fast_assignment}\n",
        encoding="utf-8",
    )
    return config


def _write_manifest(
    tmp_path: Path,
    repositories: dict,
    *,
    version: int = 2,
    algorithm: str = "sha256",
) -> Path:
    path = tmp_path / "checksums.json"
    path.write_text(
        json.dumps({"version": version, "algorithm": algorithm, "repositories": repositories}),
        encoding="utf-8",
    )
    return path


def _repo(url: str, files: dict | None = None, tag: str = "4.1.0") -> dict:
    return {
        "url": url,
        "tag": tag,
        "files": files if files is not None else {"eng.traineddata": {"size": 10, "sha256": "a" * 64}},
    }


def _repositories() -> dict:
    return {
        "tessdata": _repo("https://github.com/tesseract-ocr/tessdata/raw/4.1.0/"),
        "tessdata_best": _repo(BASE_URL),
        "tessdata_fast": _repo("https://github.com/tesseract-ocr/tessdata_fast/raw/4.1.0/"),
    }


def _configure_checker(
    monkeypatch: pytest.MonkeyPatch,
    config: Path,
    manifest: Path,
) -> None:
    monkeypatch.setattr(checker, "CONFIG_PY", config)
    monkeypatch.setattr(checker, "CHECKSUMS_MANIFEST", manifest)


class TestConfigAliasResolution:
    def test_standard_alias_resolves_to_fast_repository(self, tmp_path: Path) -> None:
        urls = checker.extract_tessdata_urls_from_config(_write_config(tmp_path))
        assert urls == {
            "tessdata": "https://github.com/tesseract-ocr/tessdata/raw/4.1.0/",
            "tessdata_best": BASE_URL,
            "tessdata_fast": "https://github.com/tesseract-ocr/tessdata_fast/raw/4.1.0/",
        }


class TestManifestValidation:
    def test_complete_v2_manifest_passes(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        config = _write_config(tmp_path)
        manifest = _write_manifest(tmp_path, _repositories())
        _configure_checker(monkeypatch, config, manifest)
        assert checker.check_checksums_manifest() == []

    @pytest.mark.parametrize(
        ("version", "algorithm", "message"),
        [(1, "sha256", "version 2"), (2, "sha1", "sha256")],
    )
    def test_legacy_manifest_rejected(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        version: int,
        algorithm: str,
        message: str,
    ) -> None:
        config = _write_config(tmp_path)
        manifest = _write_manifest(tmp_path, _repositories(), version=version, algorithm=algorithm)
        _configure_checker(monkeypatch, config, manifest)
        assert any(message in error for error in checker.check_checksums_manifest())

    def test_missing_repository_rejected(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        config = _write_config(tmp_path)
        repositories = _repositories()
        repositories.pop("tessdata_fast")
        manifest = _write_manifest(tmp_path, repositories)
        _configure_checker(monkeypatch, config, manifest)
        assert any("repository keys" in error for error in checker.check_checksums_manifest())

    def test_unexpected_repository_rejected(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        config = _write_config(tmp_path)
        repositories = _repositories()
        repositories["unexpected"] = _repo("https://github.com/tesseract-ocr/unexpected/raw/4.1.0/")
        manifest = _write_manifest(tmp_path, repositories)
        _configure_checker(monkeypatch, config, manifest)
        assert any("Unexpected tessdata repository" in error for error in checker.check_checksums_manifest())

    def test_repository_key_must_match_url(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        config = _write_config(tmp_path)
        repositories = _repositories()
        repositories["tessdata_best"]["url"] = "https://github.com/tesseract-ocr/tessdata_fast/raw/4.1.0/"
        manifest = _write_manifest(tmp_path, repositories)
        _configure_checker(monkeypatch, config, manifest)
        assert any("does not match URL repository" in error for error in checker.check_checksums_manifest())

    def test_wrong_model_count_rejected(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        config = _write_config(tmp_path)
        repositories = _repositories()
        repositories["tessdata"]["files"]["extra.traineddata"] = {
            "size": 11,
            "sha256": "b" * 64,
        }
        manifest = _write_manifest(tmp_path, repositories)
        _configure_checker(monkeypatch, config, manifest)
        assert any("must contain 1 models" in error for error in checker.check_checksums_manifest())

    def test_sha1_field_and_invalid_digest_rejected(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        config = _write_config(tmp_path)
        repositories = _repositories()
        repositories["tessdata"]["files"]["eng.traineddata"] = {
            "size": 10,
            "sha256": "invalid",
            "sha1": "b" * 40,
        }
        manifest = _write_manifest(tmp_path, repositories)
        _configure_checker(monkeypatch, config, manifest)
        errors = checker.check_checksums_manifest()
        assert any("exactly" in error for error in errors)
        assert any("invalid raw SHA-256" in error for error in errors)

    def test_nested_model_path_rejected(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        config = _write_config(tmp_path)
        repositories = _repositories()
        repositories["tessdata"]["files"] = {
            "nested/eng.traineddata": {"size": 10, "sha256": "a" * 64}
        }
        manifest = _write_manifest(tmp_path, repositories)
        _configure_checker(monkeypatch, config, manifest)
        assert any("Invalid tessdata model filename" in error for error in checker.check_checksums_manifest())


class TestMainIntegration:
    def test_consistent_flatpak_refs_pass(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        config = _write_config(tmp_path)
        flatpak = tmp_path / "flatpak.json"
        flatpak.write_text(
            json.dumps(
                {"modules": [{"name": "tessdata", "sources": [{"url": f"{BASE_URL}eng.traineddata"}]}]}
            ),
            encoding="utf-8",
        )
        manifest = _write_manifest(tmp_path, _repositories())
        _configure_checker(monkeypatch, config, manifest)
        monkeypatch.setattr(checker, "MANIFEST_MAIN", flatpak)
        monkeypatch.setattr(checker, "MANIFEST_LOCAL", flatpak)
        assert checker.main() == 0
