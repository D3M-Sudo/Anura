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
    assert 'data/screenshots/anura-welcome-page.png" "$APPDIR/usr/share/anura/runtime-smoke.png"' in builder
    assert "--runtime-smoke" in builder
    assert "FONTCONFIG_FILE" not in entrypoint
    assert 'os.environ["FONTCONFIG_FILE"] = str(runtime_config)' in builder
    assert 'font_dir = appdir / "usr/share/fonts"' in builder
    assert "runtime_config.write_text(" in builder
    assert 'appdir / "etc/fonts/fonts.conf"' not in builder
    assert builder.count('os.environ["FONTCONFIG_FILE"] = str(runtime_config)') == 1
    assert "gstreamer1.0-tools" in recipe
    assert "fontconfig-config" in recipe
    workflow = (root / ".github/workflows/main.yml").read_text(encoding="utf-8")
    assert "gstreamer1.0-tools fontconfig-config" in workflow
    assert 'FONTCONFIG_DTD="/usr/share/xml/fontconfig/fonts.dtd"' in builder
    assert 'cp "$FONTCONFIG_DTD" "$APPDIR/etc/fonts/fonts.dtd"' in builder
    assert "<family>sans-serif</family>" in builder
    assert "<family>DejaVu Sans</family>" in builder
    assert "<string>sans</string>" in builder
    assert '"sans-serif", "sans"' in smoke
    assert '"fc-list"' in smoke
    assert "font_dir.is_dir()" in smoke
    assert "font_dir.rglob(suffix)" in smoke
    assert '[font_cache, "-f", "-v", str(font_dir)]' in smoke
    assert "cache_stdout=" in smoke
    assert "font_samples=" in smoke
    for feature in (
        '["tesseract", str(image_path), "stdout"',
        'ImageFont.truetype(str(font_path), 72)',
        'font.getbbox("ANURA")',
        'appdir / "usr/share/anura/runtime-smoke.png"',
        '"ESTRAI" in recognised or "TESTO" in recognised',
        "Gst.parse_launch",
        "fc-cache",
        "fc-match",
        "fc-list",
        "IconTheme",
    ):
        assert feature in smoke
