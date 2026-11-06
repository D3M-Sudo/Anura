from __future__ import annotations

from pathlib import Path
import runpy

SCRIPT = Path(__file__).resolve().parents[1] / "build-aux" / "appimage" / "stage_runtime_libraries.sh"


def test_staging_script_requires_both_runtime_sonames() -> None:
    import subprocess

    result = subprocess.run(["bash", str(SCRIPT)], capture_output=True, text=True)
    assert result.returncode != 0
    assert "usage:" in result.stderr


def test_stage_runtime_libraries_script_is_architecture_scoped() -> None:
    content = SCRIPT.read_text(encoding="utf-8")
    assert "x86_64-linux-gnu|aarch64-linux-gnu" in content
    assert "liblzo2.so.2 libEGL.so.1" in content
    assert "readlink -f" in content
    assert "install -m 0644" in content
