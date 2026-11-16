# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""Pin the release manifest's Anura source to a commit (#501)."""

import importlib.util
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "build-aux" / "pin_source_commit.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("pin_source_commit", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


pinner = _load_module()

COMMIT = "0123456789abcdef0123456789abcdef01234567"


def _manifest() -> dict:
    return {
        "app-id": "io.github.d3msudo.anura",
        "modules": [
            {"name": "other", "sources": [{"type": "archive", "url": "https://example.invalid/x.tar.gz"}]},
            {
                "name": "anura",
                "sources": [
                    {
                        "type": "git",
                        "url": "https://github.com/D3M-Sudo/Anura.git",
                        "tag": "v0.2.1",
                    }
                ],
            },
        ],
    }


def test_pin_source_adds_the_commit_and_keeps_the_tag():
    manifest = _manifest()

    tag = pinner.pin_source(manifest, COMMIT)

    source = pinner.anura_source(manifest)
    assert tag == "v0.2.1"
    assert source["commit"] == COMMIT
    assert source["tag"] == "v0.2.1"


def test_pin_source_rejects_a_short_or_invalid_sha():
    with pytest.raises(pinner.PinError):
        pinner.pin_source(_manifest(), "abc123")


def test_anura_source_requires_the_module():
    with pytest.raises(pinner.PinError):
        pinner.anura_source({"modules": []})


def test_anura_source_requires_a_git_source():
    manifest = {"modules": [{"name": "anura", "sources": [{"type": "dir", "path": ".."}]}]}

    with pytest.raises(pinner.PinError):
        pinner.anura_source(manifest)


def test_cli_writes_the_pin(tmp_path):
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(_manifest()), encoding="utf-8")

    code = pinner.main(["--manifest", str(manifest_path), "--tag", "v0.2.1", "--commit", COMMIT])

    assert code == 0
    pinned = json.loads(manifest_path.read_text())["modules"][1]["sources"][0]
    assert pinned["commit"] == COMMIT


def test_cli_check_fails_until_pinned(tmp_path):
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(_manifest()), encoding="utf-8")

    assert pinner.main(["--manifest", str(manifest_path), "--commit", COMMIT, "--check"]) == 1

    pinner.main(["--manifest", str(manifest_path), "--commit", COMMIT])

    assert pinner.main(["--manifest", str(manifest_path), "--commit", COMMIT, "--check"]) == 0


def test_cli_fails_without_a_tag(tmp_path):
    manifest = _manifest()
    del manifest["modules"][1]["sources"][0]["tag"]
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    assert pinner.main(["--manifest", str(manifest_path), "--commit", COMMIT]) == 1
