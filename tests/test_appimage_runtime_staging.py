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
        "ImageFont.truetype(str(font_path), 72)",
        "font.getname()",
        'font_family != "DejaVu Sans" or font_style != "Bold"',
        'appdir / "usr/share/anura/runtime-smoke.png"',
        'if "ANURA" not in recognised or "ESTRAI" not in recognised:',
        "Gst.parse_launch",
        "fc-cache",
        "fc-match",
        "fc-list",
        "IconTheme",
    ):
        assert feature in smoke

    clipboard_test = workflow.split("Functional test - clipboard lifetime in Flatpak sandbox", 1)[1].split(
        "Functional test - OCR negativo", 1
    )[0]
    assert "for attempt in $(seq 1 160)" in clipboard_test
    assert "Clipboard serving period ended" in clipboard_test
    assert "Clipboard content handed over to the clipboard manager" in clipboard_test
    assert "flatpak kill" not in clipboard_test
    assert 'kill -0 "$APP_PID"' in clipboard_test


def test_appimage_cli_wrapper_is_posix_and_pulseaudio_runtime_is_explicit() -> None:
    import re
    import subprocess

    root = Path(__file__).resolve().parents[1]
    builder = (root / "build-aux/appimage/build_appdir.sh").read_text(encoding="utf-8")
    app_run = (root / "build-aux/appimage/AppRun").read_text(encoding="utf-8")
    recipe = (root / "build-aux/appimage/AppImageBuilder.yml").read_text(encoding="utf-8")
    smoke = (root / "build-aux/appimage/runtime_smoke.py").read_text(encoding="utf-8")

    match = re.search(
        r'cat > "\$APPDIR/usr/bin/anura" <<\x27SH\x27\n(.*?)\nSH',
        builder,
        re.DOTALL,
    )
    assert match is not None
    wrapper = match.group(1) + "\n"
    assert wrapper.startswith("#!/bin/sh\n")
    assert "set -eu\n" in wrapper
    assert "pipefail" not in wrapper
    syntax = subprocess.run(["sh", "-n"], input=wrapper, capture_output=True, text=True, check=False)
    assert syntax.returncode == 0, syntax.stderr

    assert '"$LIBDIR/pulseaudio:$LIBDIR:$APPDIR/usr/lib' in app_run
    assert "libpulse0" in recipe
    assert 'appdir / "usr/lib" / libdir_name / "libpulse.so.0"' in smoke
    assert 'glob("libpulsecommon-*.so")' in smoke
    assert "ctypes.CDLL(str(pulse_client), mode=ctypes.RTLD_GLOBAL)" in smoke
    assert "ctypes.CDLL(str(pulse_helpers[0]))" in smoke
    assert '"pulsesink"' in smoke
    assert 'Gst.ElementFactory.make("pulsesink"' in smoke


def test_appimage_runtime_smoke_checks_gdk_pixbuf_png_and_jpeg() -> None:
    root = Path(__file__).resolve().parents[1]
    builder = (root / "build-aux/appimage/build_appdir.sh").read_text(encoding="utf-8")
    smoke = (root / "build-aux/appimage/runtime_smoke.py").read_text(encoding="utf-8")
    jpeg_fixture = root / "data/screenshots/anura-runtime-smoke.jpg"

    assert (
        'cp "$SOURCE_ROOT/data/screenshots/anura-runtime-smoke.jpg" "$APPDIR/usr/share/anura/runtime-smoke.jpg"'
        in builder
    )
    assert 'gi.require_version("GdkPixbuf", "2.0")' in smoke
    assert "from gi.repository import Gdk, GdkPixbuf, GLib, Gst, Gtk" in smoke
    assert '("png", appdir / "usr/share/anura/runtime-smoke.png")' in smoke
    assert '("jpeg", appdir / "usr/share/anura/runtime-smoke.jpg")' in smoke
    assert "GdkPixbuf.Pixbuf.new_from_file(str(image_path))" in smoke
    assert "GdkPixbuf.Pixbuf.get_file_info(str(image_path))" in smoke
    assert "except GLib.Error as error" in smoke
    assert '"gdk_pixbuf=png+jpeg"' in smoke
    assert jpeg_fixture.is_file()
    assert jpeg_fixture.read_bytes()[:3] == bytes((0xFF, 0xD8, 0xFF))


def test_appimage_runtime_smoke_pins_gdk_typelib_before_import() -> None:
    root = Path(__file__).resolve().parents[1]
    smoke = (root / "build-aux/appimage/runtime_smoke.py").read_text(encoding="utf-8")

    gdk_pixbuf_version = 'gi.require_version("GdkPixbuf", "2.0")'
    gdk_version = 'gi.require_version("Gdk", "4.0")'
    gtk_version = 'gi.require_version("Gtk", "4.0")'
    gst_version = 'gi.require_version("Gst", "1.0")'
    repository_import = "from gi.repository import Gdk, GdkPixbuf, GLib, Gst, Gtk"

    assert gdk_pixbuf_version in smoke
    assert gdk_version in smoke
    assert gtk_version in smoke
    assert gst_version in smoke
    assert max(
        smoke.index(gdk_pixbuf_version), smoke.index(gdk_version), smoke.index(gtk_version), smoke.index(gst_version)
    ) < smoke.index(repository_import)


def test_appimage_builder_gstreamer_scanner_receives_appdir_library_paths() -> None:
    root = Path(__file__).resolve().parents[1]
    compatibility = (root / "build-aux/appimage/appimage_builder_compat.py").read_text(encoding="utf-8")

    assert "GStreamer._prepare_gst_launch_env = _prepare_gst_launch_env" in compatibility
    assert "process_env = dict(_original_prepare_gst_launch_env(self, env))" in compatibility
    assert 'env.get("APPDIR_LIBRARY_PATH")' in compatibility
    assert 'process_env.get("LD_LIBRARY_PATH")' in compatibility
    assert 'process_env["LD_LIBRARY_PATH"] = os.pathsep.join' in compatibility
    assert "AppImage builder GStreamer AppDir loader path: OK" in compatibility
