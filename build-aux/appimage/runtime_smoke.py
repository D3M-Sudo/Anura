# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""Functional runtime checks executed from the extracted multi-architecture AppImage."""

from __future__ import annotations

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
    if font_cache is None or font_match is None:
        raise RuntimeError("Bundled Fontconfig tools are unavailable")

    font_dir = appdir / "usr/share/fonts"
    with tempfile.TemporaryDirectory(prefix="anura-fontconfig-cache-") as cache_dir:
        font_env = os.environ.copy()
        font_env["XDG_CACHE_HOME"] = cache_dir
        cache_result = subprocess.run(
            [font_cache, "-f", str(font_dir)],
            check=False,
            capture_output=True,
            text=True,
            env=font_env,
        )
        if cache_result.returncode != 0:
            raise RuntimeError(f"Fontconfig could not index bundled fonts: {cache_result.stderr.strip()!r}")
        font_list = subprocess.run(
            [font_match.replace("fc-match", "fc-list"), "--format", "%{file}\\n"],
            check=False,
            capture_output=True,
            text=True,
            env=font_env,
        )
        if font_list.returncode != 0 or not font_list.stdout.strip():
            raise RuntimeError(
                "Fontconfig did not index any bundled fonts: "
                f"returncode={font_list.returncode}, stderr={font_list.stderr.strip()!r}, "
                f"config={os.environ.get('FONTCONFIG_FILE')!r}"
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

    gi.require_version("Gtk", "4.0")
    gi.require_version("Gst", "1.0")
    from gi.repository import Gdk, Gst, Gtk

    Gtk.init()
    display = Gdk.Display.get_default()
    if display is None:
        raise RuntimeError("AppImage GTK runtime could not open the Xvfb display")
    theme = Gtk.IconTheme.get_for_display(display)
    required_icons = ("edit-copy-symbolic", "object-select-symbolic")
    missing_icons = [name for name in required_icons if not theme.has_icon(name)]
    if missing_icons:
        raise RuntimeError(f"AppImage icon theme is missing required icons: {missing_icons}")

    Gst.init(None)
    for factory_name in ("playbin3", "audiotestsrc", "fakesink"):
        if Gst.ElementFactory.find(factory_name) is None:
            raise RuntimeError(f"AppImage GStreamer plugin is missing element {factory_name}")

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

    from PIL import Image, ImageDraw, ImageFont

    font_path = appdir / "usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    if not font_path.is_file():
        raise RuntimeError("Bundled DejaVu test font is missing")
    image = Image.new("RGB", (1000, 180), "white")
    draw = ImageDraw.Draw(image)
    draw.text((30, 35), "ANURA OCR TEST", fill="black", font=ImageFont.truetype(str(font_path), 72))
    with tempfile.TemporaryDirectory(prefix="anura-appimage-smoke-") as temp_dir:
        image_path = os.path.join(temp_dir, "ocr.png")
        image.save(image_path)
        result = subprocess.run(
            ["tesseract", image_path, "stdout", "--psm", "6"],
            check=True,
            capture_output=True,
            text=True,
        )
    recognised = re.sub(r"[^A-Z]", "", result.stdout.upper())
    if "ANURA" not in recognised or "OCR" not in recognised:
        raise RuntimeError(f"Bundled Tesseract OCR returned unexpected text: {recognised!r}")

    print(
        "PASS: AppImage runtime",
        f"arch={os.uname().machine}",
        "fontconfig=resolved",
        "icons=available",
        "gstreamer=fakesink-playback",
        "tesseract=ANURA-OCR",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
