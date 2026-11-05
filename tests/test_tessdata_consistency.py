#!/usr/bin/env python3
# tests/test_tessdata_consistency.py
"""Tests for build-aux/check_tessdata_consistency.py (manifest v2 / SHA-256).

Verifies that the tessdata consistency checker correctly:

- accepts a consistent v2 manifest whose URLs/tags match anura/config.py and
  whose entries carry valid positive sizes and raw SHA-256 digests;
- rejects a version 1 manifest, a non-sha256 algorithm, legacy SHA-1 fields,
  invalid digests, non-positive sizes, stale tags, and URLs not pinned in
  config.py.
"""

import json
from pathlib import Path
import sys

import pytest

# Import the checker module
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "build-aux"))
import check_tessdata_consistency as checker

BASE_URL = "https://github.com/tesseract-ocr/tessdata_best/raw/4.1.0/"
CONFIG_URLS = {
    "https://github.com/tesseract-ocr/tessdata/raw/4.1.0/",
    "https://github.com/tesseract-ocr/tessdata_best/raw/4.1.0/",
    "https://github.com/tesseract-ocr/tessdata_fast/raw/4.1.0/",
}


def _write_config(tmp_path: Path, urls: dict[str, str]) -> Path:
    config = tmp_path / "config.py"
    lines = [f'{name} = "{url}"' for name, url in urls.items()]
    config.write_text("\n".join(lines) + "\n")
    return config


def _write_checksums_manifest(
    tmp_path: Path,
    *,
    version: int = 2,
    algorithm: str = "sha256",
    repositories: dict | None = None,
) -> Path:
    manifest = tmp_path / "tessdata_checksums.json"
    manifest.write_text(
        json.dumps(
            {
                "version": version,
                "algorithm": algorithm,
                "repositories": repositories or {},
            }
        ),
        encoding="utf-8",
    )
    return manifest


def _repo_entry(url: str = BASE_URL, tag: str = "4.1.0", files: dict | None = None) -> dict:
    return {"url": url, "tag": tag, "files": files or {}}


def _file_entry(size: int = 1000, sha256: str = "a" * 64, sha1: bool = False) -> dict:
    entry: dict = {"size": size, "sha256": sha256}
    if sha1:
        entry["sha1"] = "b" * 40
    return entry


@pytest.fixture
def temp_config(tmp_path: Path) -> Path:
    return _write_config(
        tmp_path,
        {
            "TESSDATA_URL": "https://github.com/tesseract-ocr/tessdata/raw/4.1.0/",
            "TESSDATA_BEST_URL": BASE_URL,
            "TESSDATA_STANDARD_URL": "https://github.com/tesseract-ocr/tessdata_fast/raw/4.1.0/",
        },
    )


class TestCheckChecksumsManifest:
    """Direct tests of check_tessdata_consistency.check_checksums_manifest."""

    def test_consistent_v2_manifest_passes(
        self, temp_config: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        files = {"eng.traineddata": _file_entry()}
        repositories = {
            name: _repo_entry(url=url, files=dict(files))
            for name, url in (
                ("tessdata", "https://github.com/tesseract-ocr/tessdata/raw/4.1.0/"),
                ("tessdata_best", BASE_URL),
                ("tessdata_fast", "https://github.com/tesseract-ocr/tessdata_fast/raw/4.1.0/"),
            )
        }
        manifest = _write_checksums_manifest(
            tmp_path,
            repositories=repositories,
        )
        monkeypatch.setattr(checker, "CONFIG_PY", temp_config)
        monkeypatch.setattr(checker, "CHECKSUMS_MANIFEST", manifest)
        assert checker.check_checksums_manifest() == []

    def test_version_1_rejected(self, temp_config: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        manifest = _write_checksums_manifest(
            tmp_path,
            version=1,
            repositories={"tessdata_best": _repo_entry()},
        )
        monkeypatch.setattr(checker, "CONFIG_PY", temp_config)
        monkeypatch.setattr(checker, "CHECKSUMS_MANIFEST", manifest)
        errors = checker.check_checksums_manifest()
        assert errors
        assert any("version 2" in error for error in errors)

    def test_non_sha256_algorithm_rejected(
        self, temp_config: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        manifest = _write_checksums_manifest(
            tmp_path,
            algorithm="sha1",
            repositories={"tessdata_best": _repo_entry()},
        )
        monkeypatch.setattr(checker, "CONFIG_PY", temp_config)
        monkeypatch.setattr(checker, "CHECKSUMS_MANIFEST", manifest)
        errors = checker.check_checksums_manifest()
        assert errors
        assert any("sha256" in error for error in errors)

    def test_sha1_field_rejected(self, temp_config: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        files = {"eng.traineddata": _file_entry(sha1=True)}
        manifest = _write_checksums_manifest(
            tmp_path,
            repositories={"tessdata_best": _repo_entry(files=files)},
        )
        monkeypatch.setattr(checker, "CONFIG_PY", temp_config)
        monkeypatch.setattr(checker, "CHECKSUMS_MANIFEST", manifest)
        errors = checker.check_checksums_manifest()
        assert errors
        assert any("SHA-1" in error for error in errors)

    def test_invalid_digest_rejected(self, temp_config: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        files = {"eng.traineddata": _file_entry(sha256="not-hex")}
        manifest = _write_checksums_manifest(
            tmp_path,
            repositories={"tessdata_best": _repo_entry(files=files)},
        )
        monkeypatch.setattr(checker, "CONFIG_PY", temp_config)
        monkeypatch.setattr(checker, "CHECKSUMS_MANIFEST", manifest)
        errors = checker.check_checksums_manifest()
        assert errors
        assert any("sha256" in error for error in errors)

    def test_non_positive_size_rejected(
        self, temp_config: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        files = {"eng.traineddata": _file_entry(size=0)}
        manifest = _write_checksums_manifest(
            tmp_path,
            repositories={"tessdata_best": _repo_entry(files=files)},
        )
        monkeypatch.setattr(checker, "CONFIG_PY", temp_config)
        monkeypatch.setattr(checker, "CHECKSUMS_MANIFEST", manifest)
        errors = checker.check_checksums_manifest()
        assert errors
        assert any("size" in error for error in errors)

    def test_stale_tag_rejected(self, temp_config: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        files = {"eng.traineddata": _file_entry()}
        manifest = _write_checksums_manifest(
            tmp_path,
            repositories={"tessdata_best": _repo_entry(tag="5.0.0", files=files)},
        )
        monkeypatch.setattr(checker, "CONFIG_PY", temp_config)
        monkeypatch.setattr(checker, "CHECKSUMS_MANIFEST", manifest)
        errors = checker.check_checksums_manifest()
        assert errors
        assert any("tag" in error.lower() for error in errors)

    def test_url_not_pinned_in_config_rejected(
        self, temp_config: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        files = {"eng.traineddata": _file_entry()}
        manifest = _write_checksums_manifest(
            tmp_path,
            repositories={
                "tessdata_best": _repo_entry(
                    url="https://github.com/tesseract-ocr/tessdata_best/raw/5.0.0/",
                    files=files,
                )
            },
        )
        monkeypatch.setattr(checker, "CONFIG_PY", temp_config)
        monkeypatch.setattr(checker, "CHECKSUMS_MANIFEST", manifest)
        errors = checker.check_checksums_manifest()
        assert errors

    def test_missing_manifest_fails(self, tmp_path: Path) -> None:
        errors = checker.check_checksums_manifest()
        # Default CHECKSUMS_MANIFEST is the committed v1 file -> version error.
        assert errors
        assert any("version 2" in error for error in errors)


class TestMainIntegration:
    """Integration tests of the checker entry point (main)."""

    def test_consistent_state_passes(
        self,
        temp_config: Path,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        # Flatpak manifests with tessdata sources pinned to the same ref.
        flatpak = tmp_path / "manifest.json"
        flatpak.write_text(
            json.dumps(
                {
                    "modules": [
                        {
                            "name": "tessdata",
                            "sources": [
                                {
                                    "url": f"{BASE_URL}eng.traineddata",
                                    "sha256": "c" * 64,
                                }
                            ],
                        }
                    ]
                }
            )
        )
        checksums = _write_checksums_manifest(
            tmp_path,
            repositories={
                name: _repo_entry(url=url, files={"eng.traineddata": _file_entry()})
                for name, url in (
                    ("tessdata", "https://github.com/tesseract-ocr/tessdata/raw/4.1.0/"),
                    ("tessdata_best", BASE_URL),
                    ("tessdata_fast", "https://github.com/tesseract-ocr/tessdata_fast/raw/4.1.0/"),
                )
            },
        )
        monkeypatch.setattr(checker, "CONFIG_PY", temp_config)
        monkeypatch.setattr(checker, "MANIFEST_MAIN", flatpak)
        monkeypatch.setattr(checker, "MANIFEST_LOCAL", flatpak)
        monkeypatch.setattr(checker, "CHECKSUMS_MANIFEST", checksums)
        assert checker.main() == 0

    def test_stale_checksums_manifest_fails(
        self,
        temp_config: Path,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        flatpak = tmp_path / "manifest.json"
        flatpak.write_text(
            json.dumps(
                {
                    "modules": [
                        {
                            "name": "tessdata",
                            "sources": [
                                {
                                    "url": f"{BASE_URL}eng.traineddata",
                                    "sha256": "c" * 64,
                                }
                            ],
                        }
                    ]
                }
            )
        )
        checksums = _write_checksums_manifest(
            tmp_path,
            repositories={"tessdata_best": _repo_entry(tag="9.9.9")},
        )
        monkeypatch.setattr(checker, "CONFIG_PY", temp_config)
        monkeypatch.setattr(checker, "MANIFEST_MAIN", flatpak)
        monkeypatch.setattr(checker, "MANIFEST_LOCAL", flatpak)
        monkeypatch.setattr(checker, "CHECKSUMS_MANIFEST", checksums)
        assert checker.main() == 1
