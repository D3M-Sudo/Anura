# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""Tests for the tessdata integrity manifest and its loader (SHA-256 / v2).

Headless: the module under test depends only on the stdlib and loguru, so this
file runs in the default (non-GTK) suite.
"""

import json
from pathlib import Path

import pytest

from anura.config import TESSDATA_BEST_URL, TESSDATA_STANDARD_URL, TESSDATA_URL
from anura.models.tessdata_checksum import TessdataChecksum
from anura.utils import tessdata_integrity as integrity

CONFIG_URLS = {TESSDATA_URL, TESSDATA_STANDARD_URL, TESSDATA_BEST_URL}


@pytest.fixture(autouse=True)
def clear_checksum_cache():
    """Keep the lru_cache from leaking between tests."""
    _clear_checksum_cache()
    yield
    _clear_checksum_cache()


def _clear_checksum_cache() -> None:
    """Clear the loader cache when it is the real cached function.

    Tests that stub ``load_checksums`` replace it with a plain callable, which
    has no ``cache_clear``; teardown order makes either case possible.
    """
    cache_clear = getattr(integrity.load_checksums, "cache_clear", None)
    if cache_clear is not None:
        cache_clear()


class TestUrlParsing:
    """Pinned base URL parsing shared by runtime and tooling."""

    def test_parses_configured_repositories(self) -> None:
        assert integrity.repo_key_from_url(TESSDATA_URL) == "tessdata"
        assert integrity.repo_key_from_url(TESSDATA_STANDARD_URL) == "tessdata_fast"
        assert integrity.repo_key_from_url(TESSDATA_BEST_URL) == "tessdata_best"

    def test_extracts_pinned_ref(self) -> None:
        for url in CONFIG_URLS:
            assert integrity.ref_from_url(url) == "4.1.0"

    def test_builds_tree_api_url(self) -> None:
        expected = "https://api.github.com/repos/tesseract-ocr/tessdata_fast/git/trees/4.1.0?recursive=1"
        assert integrity.tree_api_url(TESSDATA_STANDARD_URL) == expected

    @pytest.mark.parametrize(
        "malformed",
        [
            "",
            "https://example.com/tessdata/raw/4.1.0/",
            "https://github.com/tesseract-ocr/tessdata/",
            "https://github.com/tesseract-ocr/tessdata/blob/4.1.0/",
        ],
    )
    def test_malformed_urls_are_rejected(self, malformed: str) -> None:
        assert integrity.repo_key_from_url(malformed) is None
        assert integrity.ref_from_url(malformed) is None
        assert integrity.tree_api_url(malformed) is None


class TestTessdataChecksum:
    """TessdataChecksum data model validation (NEW-F1 data model)."""

    def test_valid_checksum_accepted(self) -> None:
        checksum = TessdataChecksum(filename="eng.traineddata", size=23_466_654, sha256="a" * 64)
        assert checksum.filename == "eng.traineddata"
        assert checksum.size == 23_466_654
        assert checksum.sha256 == "a" * 64

    def test_uppercase_hex_digest_accepted(self) -> None:
        checksum = TessdataChecksum(filename="eng.traineddata", size=1, sha256="A" * 64)
        assert checksum.sha256 == "A" * 64

    def test_safe_nested_model_path_accepted(self) -> None:
        checksum = TessdataChecksum(
            filename="script/Arabic.traineddata",
            size=123,
            sha256="a" * 64,
        )
        assert checksum.filename == "script/Arabic.traineddata"

    def test_invalid_filename_rejected(self) -> None:
        with pytest.raises(ValueError, match="filename"):
            TessdataChecksum(filename="eng.txt", size=1, sha256="a" * 64)
        with pytest.raises(ValueError, match="filename"):
            TessdataChecksum(filename="../eng.traineddata", size=1, sha256="a" * 64)
        with pytest.raises(ValueError, match="filename"):
            TessdataChecksum(filename="/abs/eng.traineddata", size=1, sha256="a" * 64)

    def test_zero_or_negative_size_rejected(self) -> None:
        with pytest.raises(ValueError, match="size"):
            TessdataChecksum(filename="x.traineddata", size=0, sha256="a" * 64)
        with pytest.raises(ValueError, match="size"):
            TessdataChecksum(filename="x.traineddata", size=-1, sha256="a" * 64)
        with pytest.raises(ValueError, match="size"):
            TessdataChecksum(filename="x.traineddata", size=True, sha256="a" * 64)

    def test_invalid_sha256_length_rejected(self) -> None:
        with pytest.raises(ValueError, match="sha256"):
            TessdataChecksum(filename="x.traineddata", size=1, sha256="a" * 63)
        with pytest.raises(ValueError, match="sha256"):
            TessdataChecksum(filename="x.traineddata", size=1, sha256="a" * 65)

    def test_non_hexadecimal_sha256_rejected(self) -> None:
        with pytest.raises(ValueError, match="sha256"):
            TessdataChecksum(filename="x.traineddata", size=1, sha256="g" * 64)

    def test_from_dict_rejects_sha1_field(self) -> None:
        with pytest.raises(ValueError, match="SHA-1"):
            TessdataChecksum.from_dict("x.traineddata", {"size": 1, "sha1": "a" * 40})

    def test_from_dict_rejects_missing_sha256(self) -> None:
        with pytest.raises(ValueError):
            TessdataChecksum.from_dict("x.traineddata", {"size": 1})

    def test_from_dict_rejects_non_dict_entry(self) -> None:
        with pytest.raises(ValueError):
            TessdataChecksum.from_dict("x.traineddata", "not-a-dict")  # type: ignore[arg-type]


class TestManifestV2:
    """Manifest loading: version 2 / sha256 required, malformed rejected."""

    def _write_manifest(self, tmp_path: Path, data: dict) -> Path:
        manifest = tmp_path / "tessdata_checksums.json"
        manifest.write_text(json.dumps(data), encoding="utf-8")
        return manifest

    def _stub_load(self, monkeypatch: pytest.MonkeyPatch, repository: dict) -> None:
        monkeypatch.setattr(integrity, "load_checksums", lambda: {"tessdata": repository})

    def test_valid_v2_manifest_accepted(self, monkeypatch, tmp_path) -> None:
        repository = {
            "url": TESSDATA_URL,
            "tag": "4.1.0",
            "files": {"eng.traineddata": {"size": 10, "sha256": "a" * 64}},
        }
        manifest = self._write_manifest(
            tmp_path,
            {
                "version": 2,
                "algorithm": "sha256",
                "repositories": {"tessdata": repository},
            },
        )
        monkeypatch.setattr(integrity, "CHECKSUMS_PATH", manifest)
        assert integrity.load_checksums() == {"tessdata": repository}

    def test_version_1_rejected(self, monkeypatch, tmp_path) -> None:
        manifest = self._write_manifest(tmp_path, {"version": 1, "repositories": {}})
        monkeypatch.setattr(integrity, "CHECKSUMS_PATH", manifest)
        assert integrity.load_checksums() == {}
        assert integrity.get_expected_checksum(TESSDATA_URL, "eng.traineddata") is None

    def test_unsupported_algorithm_rejected(self, monkeypatch, tmp_path) -> None:
        manifest = self._write_manifest(tmp_path, {"version": 2, "algorithm": "sha1", "repositories": {}})
        monkeypatch.setattr(integrity, "CHECKSUMS_PATH", manifest)
        assert integrity.load_checksums() == {}

    def test_missing_algorithm_rejected(self, monkeypatch, tmp_path) -> None:
        manifest = self._write_manifest(tmp_path, {"version": 2, "repositories": {}})
        monkeypatch.setattr(integrity, "CHECKSUMS_PATH", manifest)
        assert integrity.load_checksums() == {}

    def test_malformed_manifest_rejected(self, monkeypatch, tmp_path) -> None:
        manifest = tmp_path / "bad.json"
        manifest.write_text("not json", encoding="utf-8")
        monkeypatch.setattr(integrity, "CHECKSUMS_PATH", manifest)
        assert integrity.load_checksums() == {}

    def test_sha1_entry_rejected(self, monkeypatch, tmp_path) -> None:
        repository = {
            "url": TESSDATA_URL,
            "tag": "4.1.0",
            "files": {"eng.traineddata": {"size": 1, "sha1": "a" * 40}},
        }
        manifest = self._write_manifest(
            tmp_path,
            {
                "version": 2,
                "algorithm": "sha256",
                "repositories": {"tessdata": repository},
            },
        )
        monkeypatch.setattr(integrity, "CHECKSUMS_PATH", manifest)
        assert integrity.get_expected_checksum(TESSDATA_URL, "eng.traineddata") is None

    def test_invalid_digest_entry_rejected(self, monkeypatch, tmp_path) -> None:
        repository = {
            "url": TESSDATA_URL,
            "tag": "4.1.0",
            "files": {"eng.traineddata": {"size": 1, "sha256": "not-hex"}},
        }
        manifest = self._write_manifest(
            tmp_path,
            {
                "version": 2,
                "algorithm": "sha256",
                "repositories": {"tessdata": repository},
            },
        )
        monkeypatch.setattr(integrity, "CHECKSUMS_PATH", manifest)
        assert integrity.get_expected_checksum(TESSDATA_URL, "eng.traineddata") is None


class TestFailClosedLookups:
    """get_expected_checksum must refuse anything it cannot vouch for."""

    def test_unknown_filename_is_refused(self, monkeypatch) -> None:
        self._stub(monkeypatch, {"tag": "4.1.0", "url": TESSDATA_URL, "files": {}})
        assert integrity.get_expected_checksum(TESSDATA_URL, "eng.traineddata") is None

    def test_unknown_repository_is_refused(self, monkeypatch) -> None:
        self._stub(monkeypatch, {"tag": "4.1.0", "url": TESSDATA_URL, "files": {}})
        assert integrity.get_expected_checksum(TESSDATA_BEST_URL, "eng.traineddata") is None

    def test_stale_tag_is_refused(self, monkeypatch) -> None:
        self._stub(
            monkeypatch,
            {
                "tag": "5.0.0",
                "url": TESSDATA_URL,
                "files": {"eng.traineddata": {"size": 1, "sha256": "a" * 64}},
            },
        )
        assert integrity.get_expected_checksum(TESSDATA_URL, "eng.traineddata") is None

    def test_stale_url_is_refused(self, monkeypatch) -> None:
        self._stub(
            monkeypatch,
            {
                "tag": "4.1.0",
                "url": "https://github.com/tesseract-ocr/tessdata/raw/4.1.0/",
                "files": {"eng.traineddata": {"size": 1, "sha256": "a" * 64}},
            },
        )
        assert integrity.get_expected_checksum(TESSDATA_BEST_URL, "eng.traineddata") is None

    def test_malformed_entry_is_refused(self, monkeypatch) -> None:
        self._stub(
            monkeypatch,
            {
                "tag": "4.1.0",
                "url": TESSDATA_URL,
                "files": {"eng.traineddata": {"size": 1}},
            },
        )
        assert integrity.get_expected_checksum(TESSDATA_URL, "eng.traineddata") is None

    def test_malformed_base_url_is_refused(self) -> None:
        assert integrity.get_expected_checksum("https://example.com/", "eng.traineddata") is None

    def _stub(self, monkeypatch: pytest.MonkeyPatch, repository: dict) -> None:
        monkeypatch.setattr(integrity, "load_checksums", lambda: {"tessdata": repository})


class TestCommittedManifest:
    """Structural checks on the manifest committed in the repo.

    The committed manifest is still format v1 (git-blob SHA-1) until the
    production checksums are regenerated against raw-content SHA-256 digests
    (see the manifest-regeneration limitation in the issue #577 handover).
    These tests assert the structural invariants that hold of the committed
    file and that must be preserved by regeneration.
    """

    def test_committed_manifest_has_configured_repositories(self) -> None:
        manifest = json.loads(integrity.CHECKSUMS_PATH.read_text(encoding="utf-8"))
        assert {entry["url"] for entry in manifest["repositories"].values()} == CONFIG_URLS
        assert set(manifest["repositories"].keys()) == {
            "tessdata",
            "tessdata_best",
            "tessdata_fast",
        }

    def test_all_489_entries_present(self) -> None:
        manifest = json.loads(integrity.CHECKSUMS_PATH.read_text(encoding="utf-8"))
        total = sum(len(repository["files"]) for repository in manifest["repositories"].values())
        assert total == 489, f"expected 489 pinned models, found {total}"

    def test_all_entries_are_traineddata_with_positive_size(self) -> None:
        manifest = json.loads(integrity.CHECKSUMS_PATH.read_text(encoding="utf-8"))
        for repository in manifest["repositories"].values():
            for filename, entry in repository["files"].items():
                assert filename.endswith(".traineddata"), filename
                assert entry["size"] > 0, filename
