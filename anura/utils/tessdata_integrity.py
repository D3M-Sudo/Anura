# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""SHA-256 integrity verification for runtime-downloaded Tesseract models."""

from functools import lru_cache
import hashlib
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from loguru import logger

from anura.models.tessdata_checksum import TessdataChecksum

CHECKSUMS_PATH = Path(__file__).resolve().parent.parent / "data" / "tessdata_checksums.json"
_GITHUB_URL_PREFIX = "https://github.com/"


def _parse_base_url(base_url: str) -> tuple[str, str, str] | None:
    if not isinstance(base_url, str) or not base_url.startswith(_GITHUB_URL_PREFIX):
        return None
    parts = [segment for segment in urlparse(base_url).path.split("/") if segment]
    if len(parts) != 4 or parts[2] != "raw":
        return None
    return parts[0], parts[1], parts[3]


def repo_key_from_url(base_url: str) -> str | None:
    parsed = _parse_base_url(base_url)
    return parsed[1] if parsed else None


def ref_from_url(base_url: str) -> str | None:
    parsed = _parse_base_url(base_url)
    return parsed[2] if parsed else None


def tree_api_url(base_url: str) -> str | None:
    parsed = _parse_base_url(base_url)
    if parsed is None:
        return None
    owner, repo, ref = parsed
    return f"https://api.github.com/repos/{owner}/{repo}/git/trees/{ref}?recursive=1"


@lru_cache(maxsize=1)
def load_checksums() -> dict[str, Any]:
    try:
        manifest = json.loads(CHECKSUMS_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        logger.error(f"Anura: Cannot read tessdata checksums manifest '{CHECKSUMS_PATH}': {error}")
        return {}
    if not isinstance(manifest, dict):
        logger.error("Anura: Tessdata checksums manifest is not a JSON object.")
        return {}
    if manifest.get("version") != 2 or manifest.get("algorithm") != "sha256":
        logger.error("Anura: Unsupported tessdata checksums manifest; version 2 / sha256 is required.")
        return {}
    repositories = manifest.get("repositories")
    if not isinstance(repositories, dict):
        logger.error("Anura: Tessdata checksums manifest has no valid repositories object.")
        return {}
    return repositories


def get_expected_checksum(base_url: str, filename: str) -> TessdataChecksum | None:
    repo = repo_key_from_url(base_url)
    if repo is None:
        logger.error(f"Anura: Malformed tessdata base URL: '{base_url}'")
        return None
    repository = load_checksums().get(repo)
    if not isinstance(repository, dict):
        logger.error(f"Anura: No pinned checksums for repository '{repo}'.")
        return None
    if repository.get("tag") != ref_from_url(base_url) or repository.get("url") != base_url:
        logger.error(f"Anura: Checksums manifest for '{repo}' does not match the configured URL/ref.")
        return None
    files = repository.get("files")
    if not isinstance(files, dict):
        logger.error(f"Anura: Malformed checksums manifest for repository '{repo}'.")
        return None
    entry = files.get(filename)
    if not isinstance(entry, dict):
        logger.error(f"Anura: No pinned checksum for '{repo}/{filename}'.")
        return None
    try:
        return TessdataChecksum.from_dict(filename, entry)
    except (KeyError, TypeError, ValueError) as error:
        logger.error(f"Anura: Invalid checksum entry for '{repo}/{filename}': {error}")
        return None


class Sha256Hasher:
    """Incremental raw-content SHA-256 hasher for streamed model downloads."""

    __slots__ = ("_hash", "_received")

    def __init__(self) -> None:
        self._hash = hashlib.sha256()
        self._received = 0

    def update(self, chunk: bytes) -> None:
        self._hash.update(chunk)
        self._received += len(chunk)

    @property
    def received(self) -> int:
        return self._received

    def hexdigest(self) -> str:
        return self._hash.hexdigest()

    def matches(self, expected: TessdataChecksum) -> bool:
        return self._received == expected.size and self.hexdigest() == expected.sha256.lower()
