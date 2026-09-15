# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""Tests for the tessdata integrity manifest and its loader (NEW-F1).

Headless: the module under test depends only on the stdlib and loguru, so this
file runs in the default (non-GTK) suite.
"""

import json
from pathlib import Path

import pytest

from anura.config import TESSDATA_BEST_URL, TESSDATA_STANDARD_URL, TESSDATA_URL
from anura.models.tessdata_checksum import TessdataChecksum
from anura.utils import tessdata_integrity as integrity

#: Git blob hash of b"hello\n", cross-checked with `git hash-object --stdin`.
HELLO_GIT_BLOB_SHA1 = "ce013625030ba8dba906f756967f9e9ca394464a"

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


class TestGitBlobHasher:
    """The digest must reproduce `git hash-object` output."""

    def test_matches_git_blob_oracle(self) -> None:
        hasher = integrity.GitBlobHasher(declared_size=6)
        hasher.update(b"hello\n")

        expected = TessdataChecksum(filename="hello.txt", size=6, sha1=HELLO_GIT_BLOB_SHA1)
        assert hasher.received == 6
        assert hasher.matches(expected)

    def test_incremental_chunks_equal_single_write(self) -> None:
        one_shot = integrity.GitBlobHasher(declared_size=6)
        one_shot.update(b"hello\n")

        chunked = integrity.GitBlobHasher(declared_size=6)
        for chunk in (b"he", b"llo", b"\n"):
            chunked.update(chunk)

        assert chunked.received == one_shot.received
        assert chunked.matches(TessdataChecksum("x", 6, HELLO_GIT_BLOB_SHA1))

    def test_rejects_wrong_size(self) -> None:
        hasher = integrity.GitBlobHasher(declared_size=6)
        hasher.update(b"hello\n")
        assert not hasher.matches(TessdataChecksum("x", 7, HELLO_GIT_BLOB_SHA1))

    def test_rejects_tampered_content(self) -> None:
        hasher = integrity.GitBlobHasher(declared_size=6)
        hasher.update(b"hell0\n")
        assert not hasher.matches(TessdataChecksum("x", 6, HELLO_GIT_BLOB_SHA1))

    def test_negative_declared_size_is_rejected(self) -> None:
        with pytest.raises(ValueError):
            integrity.GitBlobHasher(declared_size=-1)


class TestCommittedManifest:
    """Schema and anti-drift checks on the manifest committed in the repo."""

    def test_manifest_is_well_formed(self) -> None:
        manifest = json.loads(integrity.CHECKSUMS_PATH.read_text(encoding="utf-8"))
        assert manifest["version"] == 1

        repositories = manifest["repositories"]
        assert {entry["url"] for entry in repositories.values()} == CONFIG_URLS

        for name, repository in repositories.items():
            assert repository["tag"] == "4.1.0", name
            assert repository["files"], f"{name} has no pinned files"
            for filename, entry in repository["files"].items():
                assert filename.endswith(".traineddata")
                assert entry["size"] > 0
                assert len(entry["sha1"]) == 40
                assert all(char in "0123456789abcdef" for char in entry["sha1"])

    def test_bundled_language_is_pinned(self) -> None:
        checksum = integrity.get_expected_checksum(TESSDATA_URL, "eng.traineddata")
        assert isinstance(checksum, TessdataChecksum)
        assert checksum.size > 0

    def test_missing_manifest_fails_closed(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        monkeypatch.setattr(integrity, "CHECKSUMS_PATH", tmp_path / "does-not-exist.json")
        assert integrity.load_checksums() == {}
        assert integrity.get_expected_checksum(TESSDATA_URL, "eng.traineddata") is None


class TestFailClosedLookups:
    """get_expected_checksum must refuse anything it cannot vouch for."""

    def _stub(self, monkeypatch: pytest.MonkeyPatch, repository: dict) -> None:
        monkeypatch.setattr(integrity, "load_checksums", lambda: {"tessdata": repository})

    def test_unknown_filename_is_refused(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self._stub(monkeypatch, {"tag": "4.1.0", "url": TESSDATA_URL, "files": {}})
        assert integrity.get_expected_checksum(TESSDATA_URL, "eng.traineddata") is None

    def test_unknown_repository_is_refused(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self._stub(monkeypatch, {"tag": "4.1.0", "url": TESSDATA_URL, "files": {}})
        assert integrity.get_expected_checksum(TESSDATA_BEST_URL, "eng.traineddata") is None

    def test_stale_ref_is_refused(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self._stub(
            monkeypatch,
            {"tag": "5.0.0", "url": TESSDATA_URL, "files": {"eng.traineddata": {"size": 1, "sha1": "a" * 40}}},
        )
        assert integrity.get_expected_checksum(TESSDATA_URL, "eng.traineddata") is None

    def test_malformed_entry_is_refused(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self._stub(monkeypatch, {"tag": "4.1.0", "url": TESSDATA_URL, "files": {"eng.traineddata": {"size": 1}}})
        assert integrity.get_expected_checksum(TESSDATA_URL, "eng.traineddata") is None

    def test_malformed_base_url_is_refused(self) -> None:
        assert integrity.get_expected_checksum("https://example.com/", "eng.traineddata") is None
