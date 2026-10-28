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


def test_loguru_ships_its_license_from_the_pinned_sdist(manifest: dict) -> None:
    """The loguru wheel has no license file, so the sdist provides it."""
    loguru = next(m for m in manifest["modules"] if m["name"] == "python3-loguru")
    sources = loguru["sources"]

    assert any(src.get("url", "").endswith("loguru-0.7.3.tar.gz") for src in sources)
    assert any(src.get("sha256") for src in sources if src.get("url", "").endswith(".tar.gz"))
    # The layout of the extracted sdist is not guaranteed when the module has
    # several sources, so the command locates the file and fails closed.
    license_commands = [cmd for cmd in loguru["build-commands"] if "share/licenses" in cmd]
    assert len(license_commands) == 1
    assert "share/licenses/io.github.d3msudo.anura/loguru/LICENSE" in license_commands[0]
    assert "exit 1" in license_commands[0]
