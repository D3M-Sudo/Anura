# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""License collection must fail closed (#477).

Most modules copied their license with ``find ... || true``, so a missing file
ended the build successfully and shipped a bundle without the notices. The
manifest now installs a deterministic file per module (source ``LICENSE`` for
sdists, dist-info license for wheels) and the loguru wheel — which contains no
license file at all — uses the LICENSE from its sdist as a pinned source.
"""

import json
from pathlib import Path
import re

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = REPO_ROOT / "flatpak" / "io.github.d3msudo.anura.local.json"

LICENSE_DEST_RE = re.compile(r"share/licenses/io\.github\.d3msudo\.anura/([^/\"]+)/LICENSE")


@pytest.fixture(scope="module")
def manifest() -> dict:
    if not MANIFEST_PATH.exists():
        pytest.skip("local manifest not available")
    return json.loads(MANIFEST_PATH.read_text())


def _license_commands(manifest: dict) -> list[tuple[str, str]]:
    return [
        (module["name"], cmd)
        for module in manifest["modules"]
        for cmd in module.get("build-commands") or []
        if "share/licenses" in cmd
    ]


def test_no_license_command_is_best_effort(manifest: dict) -> None:
    """`|| true` turns a missing license into a silent success."""
    offenders = [name for name, cmd in _license_commands(manifest) if "|| true" in cmd]

    assert offenders == []


def test_every_license_command_installs_into_a_unique_destination(manifest: dict) -> None:
    destinations = [LICENSE_DEST_RE.search(cmd).group(1) for _, cmd in _license_commands(manifest)]

    assert len(destinations) == len(set(destinations)), "duplicate license destination"
    assert "loguru" in destinations


def test_fail_closed_wheel_commands_check_for_the_file(manifest: dict) -> None:
    """Wheel-based commands must fail when `find` returns nothing."""
    wheel_commands = [(name, cmd) for name, cmd in _license_commands(manifest) if "dist-info" in cmd]

    assert wheel_commands
    for name, cmd in wheel_commands:
        assert "exit 1" in cmd, f"{name} does not fail when the license is missing"


def test_loguru_ships_its_license_from_the_upstream_file(manifest: dict) -> None:
    """Neither the loguru wheel nor its sdist contains a license file."""
    loguru = next(m for m in manifest["modules"] if m["name"] == "python3-loguru")
    license_sources = [src for src in loguru["sources"] if src.get("dest-filename") == "loguru-LICENSE"]

    assert len(license_sources) == 1
    source = license_sources[0]
    assert source["url"].endswith("/0.7.3/LICENSE")
    assert source["sha256"], "the upstream license must be hash-pinned"

    license_commands = [cmd for cmd in loguru["build-commands"] if "share/licenses" in cmd]
    assert len(license_commands) == 1
    assert license_commands[0].startswith("install -Dm0644 loguru-LICENSE")
