from __future__ import annotations

from pathlib import Path

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


def test_appimage_runtime_smoke_is_bundled_and_exercises_native_features() -> None:
    root = Path(__file__).resolve().parents[1]
    builder = (root / "build-aux/appimage/build_appdir.sh").read_text(encoding="utf-8")
    entrypoint = (root / "build-aux/appimage/AppRun").read_text(encoding="utf-8")
    smoke = (root / "build-aux/appimage/runtime_smoke.py").read_text(encoding="utf-8")
    recipe = (root / "build-aux/appimage/AppImageBuilder.yml").read_text(encoding="utf-8")

    assert 'runtime_smoke.py" "$APPDIR/usr/lib/anura/"' in builder
    assert "--runtime-smoke" in builder
    assert "FONTCONFIG_FILE" in entrypoint
    assert "gstreamer1.0-tools" in recipe
    assert "fontconfig-config" in recipe
    workflow = (root / ".github/workflows/main.yml").read_text(encoding="utf-8")
    assert "gstreamer1.0-tools fontconfig-config" in workflow
    assert 'prefix="relative"' in builder
    assert "../../usr/share/fonts" in builder
    assert 'FONTCONFIG_DTD="/usr/share/xml/fontconfig/fonts.dtd"' in builder
    assert 'cp "$FONTCONFIG_DTD" "$APPDIR/etc/fonts/fonts.dtd"' in builder
    for feature in ('["tesseract", image_path, "stdout"', "Gst.parse_launch", "fc-cache", "fc-match", "IconTheme"):
        assert feature in smoke
