#!/usr/bin/env python3
# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""Validate the installed Flatpak's GI namespaces and native Python bindings."""

from __future__ import annotations

import ctypes
import ctypes.util
import os
import platform
import sys


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: flatpak_runtime_smoke.py EXPECTED_ARCH", file=sys.stderr)
        return 2

    expected_arch = sys.argv[1]
    actual_arch = platform.machine()
    if actual_arch != expected_arch:
        raise RuntimeError(f"runtime architecture mismatch: expected {expected_arch}, got {actual_arch}")

    # These paths are configured by the Flatpak manifest. Verify that the
    # architecture-neutral locations exist inside the installed sandbox.
    for variable, required in (
        ("GI_TYPELIB_PATH", ("/app/lib/girepository-1.0", "/usr/lib/girepository-1.0")),
        ("LD_LIBRARY_PATH", ("/app/lib",)),
    ):
        configured = os.environ.get(variable, "").split(os.pathsep)
        for path in required:
            if path not in configured:
                raise RuntimeError(f"{variable} does not include {path}")
            if not os.path.isdir(path):
                raise RuntimeError(f"{variable} entry does not exist in sandbox: {path}")

    import gi

    for namespace, version in (
        ("Gtk", "4.0"),
        ("Adw", "1"),
        ("Notify", "0.7"),
        ("Xdp", "1.0"),
        ("Gst", "1.0"),
    ):
        gi.require_version(namespace, version)

    from gi.repository import Adw, Gst, Gtk, Notify, Xdp

    Gtk.init()
    Adw.init()
    Gst.init(None)

    # Touch representative types so a typelib that imports but is incomplete
    # cannot pass this smoke test.
    for namespace, symbol in (
        (Gtk, "Application"),
        (Adw, "Application"),
        (Notify, "Notification"),
        (Xdp, "Portal"),
        (Gst, "ElementFactory"),
    ):
        if not hasattr(namespace, symbol):
            raise RuntimeError(f"GI namespace is missing {symbol}")

    # Exercise the native extensions shipped in the app prefix.
    from PIL import Image
    import psutil
    import zxingcpp

    image = Image.new("RGB", (2, 2), "white")
    if image.size != (2, 2):
        raise RuntimeError("Pillow native image backend failed")

    if not psutil.cpu_count():
        raise RuntimeError("psutil could not query the sandbox CPU topology")

    if not hasattr(zxingcpp, "read_barcodes"):
        raise RuntimeError("zxing-cpp native binding is incomplete")

    tesseract = ctypes.util.find_library("tesseract")
    if not tesseract:
        raise RuntimeError("libtesseract was not found in the Flatpak runtime")
    ctypes.CDLL(tesseract)

    print(
        "PASS: Flatpak runtime",
        f"arch={actual_arch}",
        "GI=Gtk4,Adw1,Notify0.7,Xdp1.0,Gst1.0",
        "native=Pillow,psutil,zxing-cpp,libtesseract",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
