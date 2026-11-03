# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT
# ruff: noqa: I001

from pathlib import Path
import os
import subprocess


SCRIPT = Path(__file__).resolve().parents[1] / "po" / "update_potfiles.sh"


def _fixture(tmp_path: Path) -> tuple[Path, Path]:
    root = tmp_path / "repo"
    po = root / "po"
    fakebin = tmp_path / "bin"
    (root / "anura").mkdir(parents=True)
    (root / "data" / "ui").mkdir(parents=True)
    po.mkdir()
    fakebin.mkdir()
    (root / "meson.build").write_text(
        "project('anura', version: '1.2.3')\n", encoding="utf-8"
    )
    (root / "anura" / "sample.py").write_text("_('Sample')\n", encoding="utf-8")
    (root / "data" / "ui" / "sample.blp").write_text("// sample\n", encoding="utf-8")
    (root / "data" / "sample.desktop.in").write_text("Name=Sample\n", encoding="utf-8")
    (root / "data" / "sample.metainfo.xml.in").write_text(
        "<component/>\n", encoding="utf-8"
    )
    (po / "update_potfiles.sh").write_text(
        SCRIPT.read_text(encoding="utf-8"), encoding="utf-8"
    )
    (po / "io.github.d3msudo.anura.pot").write_text(
        "PREVIOUS VALID POT\n", encoding="utf-8"
    )
    (po / "POTFILES").write_text("previous.py\n", encoding="utf-8")

    (fakebin / "xgettext").write_text(
        "#!/bin/sh\n"
        "if [ \"$FAIL_XGETTEXT\" = 1 ]; then exit 23; fi\n"
        "for arg in \"$@\"; do case \"$arg\" in --output=*) out=$(printf '%s' \"$arg\" | sed 's/^--output=//');; esac; done\n"
        "printf '#: ../anura/sample.py:1\\nmsgid \"\"\\nmsgstr \"\"\\n' > \"$out\"\n",
        encoding="utf-8",
    )
    (fakebin / "msgcat").write_text(
        "#!/bin/sh\n"
        "if [ \"$FAIL_MSGCAT\" = 1 ]; then exit 24; fi\n"
        "shift\ncat \"$@\"\n",
        encoding="utf-8",
    )
    (fakebin / "msgfmt").write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    for executable in fakebin.iterdir():
        executable.chmod(0o755)
    return po, fakebin


def _run(
    po: Path, fakebin: Path, **extra_env: str
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.update(
        {"PATH": f"{fakebin}:{env['PATH']}", "FAIL_XGETTEXT": "0", "FAIL_MSGCAT": "0"}
    )
    env.update(extra_env)
    return subprocess.run(
        ["bash", "update_potfiles.sh"], cwd=po, env=env, capture_output=True, text=True
    )


def test_xgettext_failure_preserves_existing_outputs(tmp_path: Path) -> None:
    po, fakebin = _fixture(tmp_path)
    result = _run(po, fakebin, FAIL_XGETTEXT="1")
    assert result.returncode != 0
    assert (
        (po / "io.github.d3msudo.anura.pot").read_text(encoding="utf-8")
        == "PREVIOUS VALID POT\n"
    )
    assert (po / "POTFILES").read_text(encoding="utf-8") == "previous.py\n"


def test_msgcat_failure_preserves_existing_outputs(tmp_path: Path) -> None:
    po, fakebin = _fixture(tmp_path)
    result = _run(po, fakebin, FAIL_MSGCAT="1")
    assert result.returncode != 0
    assert (
        (po / "io.github.d3msudo.anura.pot").read_text(encoding="utf-8")
        == "PREVIOUS VALID POT\n"
    )
    assert (po / "POTFILES").read_text(encoding="utf-8") == "previous.py\n"
