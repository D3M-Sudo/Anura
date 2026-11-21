# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""Functional runtime checks executed from the extracted multi-architecture AppImage."""

from __future__ import annotations

import ctypes
import os
import pathlib
import re
import shutil
import subprocess
import tempfile


def main() -> int:
    appdir = pathlib.Path(os.environ["APPDIR"])
    font_cache = shutil.which("fc-cache")
    font_match = shutil.which("fc-match")
    font_list_tool = shutil.which("fc-list")
    if font_cache is None or font_match is None or font_list_tool is None:
        raise RuntimeError("Bundled Fontconfig tools are unavailable")

    font_dir = appdir / "usr/share/fonts"
    if not font_dir.is_dir():
        raise RuntimeError(
            "AppImage bundled font directory is missing: "
            f"path={font_dir}, appdir_exists={appdir.is_dir()}, "
            f"share_exists={(appdir / 'usr/share').is_dir()}"
        )
    bundled_font_samples = sorted(
        str(path.relative_to(appdir)) for suffix in ("*.ttf", "*.otf", "*.ttc") for path in font_dir.rglob(suffix)
    )[:10]
    with tempfile.TemporaryDirectory(prefix="anura-fontconfig-cache-") as cache_dir:
        font_env = os.environ.copy()
        font_env["XDG_CACHE_HOME"] = cache_dir
        cache_result = subprocess.run(
            [font_cache, "-f", "-v", str(font_dir)],
            check=False,
            capture_output=True,
            text=True,
            env=font_env,
        )
        if cache_result.returncode != 0:
            raise RuntimeError(
                "Fontconfig could not index bundled fonts: "
                f"returncode={cache_result.returncode}, stdout={cache_result.stdout[-4000:]!r}, "
                f"stderr={cache_result.stderr[-4000:]!r}, font_dir={str(font_dir)!r}, "
                f"font_samples={bundled_font_samples!r}"
            )
        font_list = subprocess.run(
            [font_list_tool, "--format", "%{file}\\n"],
            check=False,
            capture_output=True,
            text=True,
            env=font_env,
        )
        if font_list.returncode != 0 or not font_list.stdout.strip():
            raise RuntimeError(
                "Fontconfig did not index any bundled fonts: "
                f"returncode={font_list.returncode}, stdout={font_list.stdout[-4000:]!r}, "
                f"stderr={font_list.stderr[-4000:]!r}, font_dir={str(font_dir)!r}, "
                f"font_dir_entries={[path.name for path in list(font_dir.iterdir())[:20]]!r}, "
                f"font_samples={bundled_font_samples!r}, "
                f"cache_stdout={cache_result.stdout[-4000:]!r}, "
                f"cache_stderr={cache_result.stderr[-4000:]!r}, "
                f"config={os.environ.get('FONTCONFIG_FILE')!r}, "
                f"config_dir={os.environ.get('FONTCONFIG_PATH')!r}"
            )
        for family in ("sans-serif", "sans"):
            font_result = subprocess.run(
                [font_match, "-f", "%{file}\\n", family],
                check=False,
                capture_output=True,
                text=True,
                env=font_env,
            )
            matched_font = font_result.stdout.strip()
            try:
                resolved_font = pathlib.Path(matched_font).resolve(strict=True)
                resolved_font.relative_to(font_dir.resolve(strict=True))
            except (OSError, ValueError):
                resolved_font = None
            if font_result.returncode != 0 or resolved_font is None:
                available_fonts = [str(path.relative_to(appdir)) for path in font_dir.rglob("*.ttf")][:5]
                raise RuntimeError(
                    "Fontconfig failed to resolve a bundled default sans-serif font: "
                    f"family={family!r}, returncode={font_result.returncode}, "
                    f"stderr={font_result.stderr.strip()!r}, stdout={matched_font!r}, "
                    f"indexed={font_list.stdout.splitlines()[:5]!r}, "
                    f"config={os.environ.get('FONTCONFIG_FILE')!r}, "
                    f"dtd={(appdir / 'etc/fonts/fonts.dtd').is_file()}, fonts={available_fonts}"
                )

    import gi

    gi.require_version("GdkPixbuf", "2.0")
    gi.require_version("Gdk", "4.0")
    gi.require_version("Gtk", "4.0")
    gi.require_version("Gst", "1.0")
    from gi.repository import Gdk, GdkPixbuf, GLib, Gst, Gtk

    Gtk.init()
    display = Gdk.Display.get_default()
    if display is None:
        raise RuntimeError("AppImage GTK runtime could not open the Xvfb display")
    theme = Gtk.IconTheme.get_for_display(display)
    required_icons = ("edit-copy-symbolic", "object-select-symbolic")
    missing_icons = [name for name in required_icons if not theme.has_icon(name)]
    if missing_icons:
        raise RuntimeError(f"AppImage icon theme is missing required icons: {missing_icons}")

    pixbuf_fixtures = (
        ("png", appdir / "usr/share/anura/runtime-smoke.png"),
        ("jpeg", appdir / "usr/share/anura/runtime-smoke.jpg"),
    )
    registered_pixbuf_formats = sorted(
        image_format.get_name() for image_format in GdkPixbuf.Pixbuf.get_formats()
    )
    pixbuf_module_file = pathlib.Path(os.environ.get("GDK_PIXBUF_MODULE_FILE", ""))
    pixbuf_module_dir = pathlib.Path(os.environ.get("GDK_PIXBUF_MODULEDIR", ""))
    pixbuf_loader_files = (
        sorted(path.name for path in pixbuf_module_dir.glob("*.so"))
        if pixbuf_module_dir.is_dir()
        else []
    )
    pixbuf_cache_preview = (
        pixbuf_module_file.read_text(encoding="utf-8", errors="replace")[:6000]
        if pixbuf_module_file.is_file()
        else "<missing>"
    )
    pixbuf_failures = []
    for expected_format, image_path in pixbuf_fixtures:
        if not image_path.is_file():
            pixbuf_failures.append(f"{expected_format}: fixture is missing: {image_path}")
            continue
        try:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file(str(image_path))
        except GLib.Error as error:
            pixbuf_failures.append(f"{expected_format}: decode failed: {error}")
            continue
        detected_format, detected_width, detected_height = GdkPixbuf.Pixbuf.get_file_info(str(image_path))
        actual_format = detected_format.get_name() if detected_format is not None else None
        if actual_format != expected_format:
            pixbuf_failures.append(f"{expected_format}: detected format={actual_format!r}, path={image_path}")
            continue
        if (
            detected_width <= 0
            or detected_height <= 0
            or pixbuf.get_width() != detected_width
            or pixbuf.get_height() != detected_height
        ):
            pixbuf_failures.append(
                f"{expected_format}: invalid dimensions detected={detected_width}x{detected_height}, "
                f"decoded={pixbuf.get_width()}x{pixbuf.get_height()}"
            )
    if pixbuf_failures:
        raise RuntimeError(
            "AppImage GdkPixbuf validation failed: "
            + "; ".join(pixbuf_failures)
            + f"; registered_formats={registered_pixbuf_formats!r}"
            + f"; module_dir={str(pixbuf_module_dir)!r}"
            + f"; loader_files={pixbuf_loader_files!r}"
            + f"; module_file={str(pixbuf_module_file)!r}"
            + f"; cache_preview={pixbuf_cache_preview!r}"
        )

    Gst.init(None)
    machine = os.uname().machine
    libdir_name = {
        "x86_64": "x86_64-linux-gnu",
        "aarch64": "aarch64-linux-gnu",
    }.get(machine)
    if libdir_name is None:
        raise RuntimeError(f"Unsupported AppImage architecture for PulseAudio check: {machine}")
    pulse_lib_dir = appdir / "usr/lib" / libdir_name / "pulseaudio"
    pulse_client = appdir / "usr/lib" / libdir_name / "libpulse.so.0"
    if not pulse_client.is_file():
        raise RuntimeError(f"AppImage PulseAudio client library is missing: {pulse_client}")
    pulse_helpers = sorted(pulse_lib_dir.glob("libpulsecommon-*.so"))
    if not pulse_helpers:
        raise RuntimeError(f"AppImage PulseAudio private helper is missing: {pulse_lib_dir}")
    try:
        # libpulse exports symbols consumed by its private helper; load it
        # globally first, then explicitly validate the helper itself.
        ctypes.CDLL(str(pulse_client), mode=ctypes.RTLD_GLOBAL)
        ctypes.CDLL(str(pulse_helpers[0]))
    except OSError as error:
        raise RuntimeError(
            f"AppImage PulseAudio client/helper cannot be loaded: {pulse_client}, {pulse_helpers[0]}: {error}"
        ) from error

    for factory_name in ("playbin3", "audiotestsrc", "fakesink", "pulsesink"):
        if Gst.ElementFactory.find(factory_name) is None:
            raise RuntimeError(f"AppImage GStreamer plugin is missing element {factory_name}")
    pulse_sink = Gst.ElementFactory.make("pulsesink", "runtime-smoke-pulsesink")
    if pulse_sink is None:
        raise RuntimeError("AppImage GStreamer PulseAudio sink could not be instantiated")
    pulse_sink.set_state(Gst.State.NULL)

    pipeline = Gst.parse_launch("audiotestsrc num-buffers=1 ! fakesink")
    if pipeline.set_state(Gst.State.PLAYING) == Gst.StateChangeReturn.FAILURE:
        raise RuntimeError("AppImage GStreamer test pipeline could not start")
    message = pipeline.get_bus().timed_pop_filtered(
        5 * Gst.SECOND,
        Gst.MessageType.EOS | Gst.MessageType.ERROR,
    )
    pipeline.set_state(Gst.State.NULL)
    if message is None or message.type == Gst.MessageType.ERROR:
        detail = message.parse_error()[0].message if message is not None else "EOS timeout"
        raise RuntimeError(f"AppImage GStreamer playback smoke failed: {detail}")

    from PIL import Image, ImageFont

    font_path = appdir / "usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    if not font_path.is_file():
        raise RuntimeError("Bundled DejaVu test font is missing")
    # Inspect face metadata only: Pillow/Freetype returns invalid glyph extents
    # for this font in clean CI images. Fontconfig resolution and fixture OCR
    # separately exercise the installed font and actual OCR runtime.
    font = ImageFont.truetype(str(font_path), 72)
    font_family, font_style = font.getname()
    if font_family != "DejaVu Sans" or font_style != "Bold":
        raise RuntimeError(f"Unexpected bundled font face: family={font_family!r}, style={font_style!r}")

    image_path = appdir / "usr/share/anura/runtime-smoke.png"
    if not image_path.is_file():
        raise RuntimeError("Bundled AppImage OCR fixture is missing")
    with Image.open(image_path) as image:
        image.verify()
    result = subprocess.run(
        ["tesseract", str(image_path), "stdout", "--psm", "6"],
        check=True,
        capture_output=True,
        text=True,
    )
    recognised = re.sub(r"[^A-Z]", "", result.stdout.upper())
    if "ANURA" not in recognised or "ESTRAI" not in recognised:
        raise RuntimeError(f"Bundled Tesseract OCR returned unexpected text: {recognised!r}")

    print(
        "PASS: AppImage runtime",
        f"arch={os.uname().machine}",
        "fontconfig=resolved",
        "icons=available",
        "gdk_pixbuf=png+jpeg",
        "gstreamer=fakesink-playback+pulsesink",
        "tesseract=ANURA-OCR",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
