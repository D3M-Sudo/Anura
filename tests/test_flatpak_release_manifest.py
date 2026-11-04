# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""Tests for local-to-release Flatpak manifest generation and drift detection."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


GENERATOR = _load_module("generate_release_manifest", ROOT / "build-aux" / "generate_release_manifest.py")
CHECKER = _load_module("check_manifest_consistency", ROOT / "build-aux" / "check_manifest_consistency.py")


def _local_manifest() -> dict[str, Any]:
    return json.loads((ROOT / "flatpak" / "io.github.d3msudo.anura.local.json").read_text(encoding="utf-8"))


def test_release_generation_preserves_all_shared_manifest_data() -> None:
    local = _local_manifest()
    generated = GENERATOR.generate_release_manifest(local, "0.2.1")

    assert "branch" not in generated
    assert "separate-locales" not in generated
    assert generated["runtime-version"] == "51"
    assert generated["sdk"] == local["sdk"]
    assert generated["finish-args"] == local["finish-args"]
    local_shared = {m["name"]: m for m in local["modules"] if m["name"] != "anura"}
    generated_shared = {m["name"]: m for m in generated["modules"] if m["name"] != "anura"}
    assert generated_shared == local_shared
    app = next(module for module in generated["modules"] if module["name"] == "anura")
    assert app["sources"] == [{"type": "git", "url": GENERATOR.APP_SOURCE_URL, "tag": "v0.2.1"}]


def test_ci_generation_pins_exact_checked_out_commit() -> None:
    commit = "0123456789abcdef0123456789abcdef01234567"
    generated = GENERATOR.generate_release_manifest(_local_manifest(), "0.2.1", source_path="..", source_commit=commit)
    app = next(module for module in generated["modules"] if module["name"] == "anura")
    assert app["sources"] == [{"type": "git", "path": "..", "commit": commit}]


def test_generator_rejects_incomplete_or_invalid_ci_source() -> None:
    local = _local_manifest()
    for kwargs in (
        {"source_path": ".."},
        {"source_commit": "0123456789abcdef0123456789abcdef01234567"},
        {"source_path": "/absolute/path", "source_commit": "0123456789abcdef0123456789abcdef01234567"},
        {"source_path": "..", "source_commit": "not-a-commit"},
    ):
        try:
            GENERATOR.generate_release_manifest(local, "0.2.1", **kwargs)
        except ValueError:
            pass
        else:
            raise AssertionError(f"invalid source arguments were accepted: {kwargs}")


def test_checker_detects_runtime_permission_module_and_checksum_drift() -> None:
    local = _local_manifest()
    generated = GENERATOR.generate_release_manifest(local, "0.2.1")
    assert CHECKER._differences(CHECKER.normalize_manifest(local), CHECKER.normalize_manifest(generated)) == []

    changed = json.loads(json.dumps(generated))
    changed["runtime-version"] = "50"
    changed["finish-args"].append("--filesystem=host")
    changed["modules"][0]["sources"][0]["sha256"] = "0" * 64
    differences = CHECKER._differences(CHECKER.normalize_manifest(local), CHECKER.normalize_manifest(changed))
    assert "$.runtime-version" in differences
    assert "$.finish-args (length" in differences
    assert any(".sha256" in item for item in differences)
