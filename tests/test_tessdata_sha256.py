# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""Tests for SHA-256 tessdata integrity verification (Issue #577).

Covers the streaming SHA-256 pipeline end to end:

- negative: corrupted payloads, wrong sizes, tampered content, unknown files
- streaming: incremental SHA-256 matches a single-shot digest over chunks
- network-failure: unreachable / refused downloads leave nothing installed
- cleanup: temporary files are removed on every failure path
- manifest-validation: missing/malformed sha256 entries fail closed
- atomic-installation: successful downloads use os.replace, no partial model visible

Run with the system python3 + venv site-packages pattern documented in
``docs/reference/dependencies.md`` (the download tests need PyGObject, marked
``gtk``; the hasher/manifest tests are headless).
"""

import hashlib
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

pytest.importorskip("gi")

from anura.config import TESSDATA_URL
from anura.models.tessdata_checksum import TessdataChecksum
from anura.services.language.download_manager import DownloadManager
from anura.utils.tessdata_integrity import (
    Sha256Hasher,
    get_expected_checksum,
    ref_from_url,
    repo_key_from_url,
)


def _response(payloads, headers=None):
    """Build a fake streaming ``requests`` response yielding ``payloads``."""
    response = MagicMock()
    response.headers = headers if headers is not None else {}
    response.iter_content = lambda chunk_size=8192: iter(payloads)
    response.raise_for_status = MagicMock()
    return response


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data, usedforsecurity=True).hexdigest()


def _git_blob_sha1(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\\x00".encode() + data, usedforsecurity=False).hexdigest()


@pytest.fixture
def stub_integrity(monkeypatch):
    """Pin a test payload in a synthetic integrity manifest (with sha256)."""

    def _install(base_url: str, filename: str, payload: bytes) -> None:
        repository = {
            "url": base_url,
            "tag": ref_from_url(base_url),
            "files": {
                filename: {
                    "size": len(payload),
                    "sha1": _git_blob_sha1(payload),
                    "sha256": _sha256(payload),
                }
            },
        }
        repo = repo_key_from_url(base_url)
        monkeypatch.setattr(
            "anura.utils.tessdata_integrity.load_checksums",
            lambda: {repo: repository},
        )

    return _install


class TestSha256Hasher:
    """The incremental SHA-256 must match a single-shot digest."""

    def test_matches_single_shot_digest(self) -> None:
        payload = b"MODEL-DATA" * 64
        hasher = Sha256Hasher(declared_size=len(payload))
        hasher.update(payload)

        expected = TessdataChecksum(
            filename="fra.traineddata",
            size=len(payload),
            sha256=_sha256(payload),
            sha1=_git_blob_sha1(payload),
        )
        assert hasher.received == len(payload)
        assert hasher.matches(expected)

    def test_incremental_chunks_equal_single_write(self) -> None:
        payload = b"MODEL-DATA" * 64
        chunks = [payload[i : i + 1000] for i in range(0, len(payload), 1000)]

        one_shot = Sha256Hasher(declared_size=len(payload))
        one_shot.update(payload)

        chunked = Sha256Hasher(declared_size=len(payload))
        for chunk in chunks:
            chunked.update(chunk)

        assert chunked.received == one_shot.received
        expected = TessdataChecksum("x", len(payload), _sha256(payload), _git_blob_sha1(payload))
        assert chunked.matches(expected)
        assert one_shot.matches(expected)

    def test_tampered_content_is_rejected(self) -> None:
        payload = b"GENUINE-MODEL"
        hasher = Sha256Hasher(declared_size=len(payload))
        hasher.update(payload[:-1] + b"X")  # corrupt last byte

        expected = TessdataChecksum("x", len(payload), _sha256(payload), _git_blob_sha1(payload))
        assert not hasher.matches(expected)

    def test_wrong_size_is_rejected(self) -> None:
        payload = b"GENUINE-MODEL"
        hasher = Sha256Hasher(declared_size=len(payload))
        hasher.update(payload)

        expected = TessdataChecksum("x", len(payload) + 1, _sha256(payload), _git_blob_sha1(payload))
        assert not hasher.matches(expected)

    def test_empty_payload(self) -> None:
        payload = b""
        hasher = Sha256Hasher(declared_size=0)
        expected = TessdataChecksum("x", 0, _sha256(payload), _git_blob_sha1(payload))
        assert hasher.matches(expected)


# ---------------------------------------------------------------------------
# Negative: download refused on integrity failure (headless, no GTK)
# ---------------------------------------------------------------------------


class TestNegativeIntegrity:
    """Any checksum failure must refuse installation (fail closed)."""

    @pytest.fixture
    def manager(self, tmp_path: Path):
        tessdata_dir = tmp_path / "tessdata"
        tessdata_dir.mkdir()
        with (
            patch("anura.services.language.download_manager.TESSDATA_DIR", str(tessdata_dir)),
            patch("anura.services.language.download_manager.settings") as mock_settings,
        ):
            mock_settings.get_string.return_value = "fast"
            yield DownloadManager(), tessdata_dir

    def _stub_get(self, dm, payload: bytes, headers=None):
        return patch.object(dm.session, "get", return_value=_response([payload], headers))

    def test_wrong_sha256_is_refused(self, manager, monkeypatch) -> None:
        dm, tessdata_dir = manager
        payload = b"MODEL-DATA" * 64
        different = b"OTHER-DATA" * 64
        repository = {
            "url": TESSDATA_URL,
            "tag": ref_from_url(TESSDATA_URL),
            "files": {
                "fra.traineddata": {
                    "size": len(different),
                    "sha1": _git_blob_sha1(different),
                    "sha256": _sha256(different),
                }
            },
        }
        monkeypatch.setattr(
            "anura.utils.tessdata_integrity.load_checksums",
            lambda: {repo_key_from_url(TESSDATA_URL): repository},
        )

        with self._stub_get(dm, payload, {"content-length": str(len(payload))}):
            patch(
                "anura.services.language.download_manager.shutil.which",
                return_value="/usr/bin/tesseract",
            ).start()
            try:
                result = dm.download_begin("fra")
            finally:
                patch.stopall()

        assert result is None
        assert not (tessdata_dir / "fra.traineddata").exists()
        assert list(tessdata_dir.glob("*.tmp")) == []

    def test_truncated_payload_is_refused(self, manager, monkeypatch) -> None:
        dm, tessdata_dir = manager
        full = b"MODEL-DATA" * 64
        truncated = full[: len(full) // 2]
        repository = {
            "url": TESSDATA_URL,
            "tag": ref_from_url(TESSDATA_URL),
            "files": {
                "fra.traineddata": {
                    "size": len(full),
                    "sha1": _git_blob_sha1(full),
                    "sha256": _sha256(full),
                }
            },
        }
        monkeypatch.setattr(
            "anura.utils.tessdata_integrity.load_checksums",
            lambda: {repo_key_from_url(TESSDATA_URL): repository},
        )

        with self._stub_get(dm, truncated, {"content-length": str(len(truncated))}):
            patch(
                "anura.services.language.download_manager.shutil.which",
                return_value="/usr/bin/tesseract",
            ).start()
            try:
                result = dm.download_begin("fra")
            finally:
                patch.stopall()

        assert result is None
        assert not (tessdata_dir / "fra.traineddata").exists()
        assert list(tessdata_dir.glob("*.tmp")) == []

    def test_unknown_filename_is_refused(self, manager, monkeypatch) -> None:
        _dm, _tessdata_dir = manager
        repository = {
            "url": TESSDATA_URL,
            "tag": ref_from_url(TESSDATA_URL),
            "files": {},
        }
        monkeypatch.setattr(
            "anora.utils.tessdata_integrity.load_checksums",
            lambda: {repo_key_from_url(TESSDATA_URL): repository},
        )

        with self._stub_get(_dm, b"MODEL-DATA", {"content-length": str(len(b"MODEL-DATA"))}):
            patch(
                "anura.services.language.download_manager.shutil.which",
                return_value="/usr/bin/tesseract",
            ).start()
            try:
                result = _dm.download_begin("zzz")
            finally:
                patch.stopall()

        assert result is None

    def test_missing_sha256_entry_fails_closed(self, manager, monkeypatch) -> None:
        """A pinned entry without a sha256 must never be trusted (version 1 legacy)."""
        _dm, _tessdata_dir = manager
        payload = b"MODEL-DATA" * 64
        repository = {
            "url": TESSDATA_URL,
            "tag": ref_from_url(TESSDATA_URL),
            "files": {
                "fra.traineddata": {
                    "size": len(payload),
                    "sha1": _git_blob_sha1(payload),
                    # no sha256
                }
            },
        }
        monkeypatch.setattr(
            "anura.utils.tessdata_integrity.load_checksums",
            lambda: {repo_key_from_url(TESSDATA_URL): repository},
        )

        assert get_expected_checksum(TESSDATA_URL, "fra.traineddata") is None


# ---------------------------------------------------------------------------
# Network-failure: download never installs anything on connection errors
# ---------------------------------------------------------------------------


class TestNetworkFailure:
    """Unreachable / refused downloads leave the filesystem untouched."""

    @pytest.fixture
    def manager(self, tmp_path: Path):
        tessdata_dir = tmp_path / "tessdata"
        tessdata_dir.mkdir()
        with (
            patch("anura.services.language.download_manager.TESSDATA_DIR", str(tessdata_dir)),
            patch("anura.services.language.download_manager.settings") as mock_settings,
        ):
            mock_settings.get_string.return_value = "fast"
            yield DownloadManager(), tessdata_dir

    def test_connection_error_refuses_install(self, manager, monkeypatch) -> None:
        dm, tessdata_dir = manager
        import requests

        import anura.utils.tessdata_integrity as integrity

        repository = {
            "url": TESSDATA_URL,
            "tag": ref_from_url(TESSDATA_URL),
            "files": {
                "fra.traineddata": {
                    "size": 100,
                    "sha1": "a" * 40,
                    "sha256": "b" * 64,
                }
            },
        }
        monkeypatch.setattr(
            integrity,
            "load_checksums",
            lambda: {repo_key_from_url(TESSDATA_URL): repository},
        )

        def boom(*args, **kwargs):
            raise requests.ConnectionError("refused")

        with (
            patch.object(dm.session, "get", side_effect=boom),
            patch(
                "anura.services.language.download_manager.shutil.which",
                return_value="/usr/bin/tesseract",
            ),
        ):
            result = dm.download_begin("fra")

        assert result is None
        assert not (tessdata_dir / "fra.traineddata").exists()
        assert list(tessdata_dir.glob("*.tmp")) == []


# ---------------------------------------------------------------------------
# Atomic installation
# ---------------------------------------------------------------------------


class TestAtomicInstallation:
    """Success installs via os.replace; nothing partial is ever visible."""

    @pytest.fixture
    def manager(self, tmp_path: Path):
        tessdata_dir = tmp_path / "tessdata"
        tessdata_dir.mkdir()
        with (
            patch("anura.services.language.download_manager.TESSDATA_DIR", str(tessdata_dir)),
            patch("anura.services.language.download_manager.settings") as mock_settings,
        ):
            mock_settings.get_string.return_value = "fast"
            yield DownloadManager(), tessdata_dir

    def test_successful_download_installs_atomically(self, manager, stub_integrity) -> None:
        dm, tessdata_dir = manager
        payload = b"MODEL-DATA" * 64
        stub_integrity(TESSDATA_URL, "fra.traineddata", payload)
        response = _response([payload], {"content-length": str(len(payload))})

        final_path = tessdata_dir / "fra.traineddata"
        partial_visible: list[bool] = []

        def iter_content(chunk_size: int = 8192):
            partial_visible.append(final_path.exists())
            yield payload

        response.iter_content = iter_content

        with (
            patch.object(dm.session, "get", return_value=response),
            patch(
                "anura.services.language.download_manager.shutil.which",
                return_value="/usr/bin/tesseract",
            ),
        ):
            result = dm.download_begin("fra")

        assert result == "fra"
        assert partial_visible == [False]  # model not visible until the rename
        response.close.assert_called_once()
        assert final_path.read_bytes() == payload
        assert list(tessdata_dir.glob("*.tmp")) == []

    def test_failed_download_leaves_existing_model_untouched(self, manager, stub_integrity) -> None:
        dm, tessdata_dir = manager
        existing = b"EXISTING-GOOD-MODEL"
        (tessdata_dir / "fra.traineddata").write_bytes(existing)

        # New payload has a *different* sha256 -> verification fails.
        stub_integrity(TESSDATA_URL, "fra.traineddata", b"CORRUPTED-PAYLOAD")
        response = _response([b"CORRUPTED-PAYLOAD"], {"content-length": str(len(b"CORRUPTED-PAYLOAD"))})

        with (
            patch.object(dm.session, "get", return_value=response),
            patch(
                "anura.services.language.download_manager.shutil.which",
                return_value="/usr/bin/tesseract",
            ),
        ):
            result = dm.download_begin("fra")

        assert result is None
        assert (tessdata_dir / "fra.traineddata").read_bytes() == existing
        assert list(tessdata_dir.glob("*.tmp")) == []
