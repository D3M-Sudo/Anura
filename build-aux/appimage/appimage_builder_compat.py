#!/usr/bin/env python3
"""Run appimage-builder with Debian-native version ordering for Ubuntu packages.

appimage-builder 1.1.0 compares APT package versions with PEP 440. Ubuntu
versions such as 1.22.6ubuntu6 are valid Debian versions but invalid PEP 440
versions. apt_pkg.version_compare implements the same ordering as dpkg.
"""

from __future__ import annotations

import os
import sys

import apt_pkg

apt_pkg.init_system()

from appimagebuilder.modules.deploy.apt.package import Package  # noqa: E402


def _debian_version_greater_than(self: Package, other: object) -> bool:
    if not isinstance(other, Package):
        return NotImplemented
    return apt_pkg.version_compare(self.version, other.version) > 0


Package.__gt__ = _debian_version_greater_than


def _prepend_appdir_library_paths(
    process_env: dict[str, str], appdir_library_paths: list[str]
) -> dict[str, str]:
    """Make staged AppDir libraries visible to GStreamer build-time subprocesses."""
    paths = [str(path) for path in appdir_library_paths if path]
    inherited = process_env.get("LD_LIBRARY_PATH")
    if inherited:
        paths.extend(path for path in inherited.split(os.pathsep) if path)
    process_env["LD_LIBRARY_PATH"] = os.pathsep.join(dict.fromkeys(paths))
    return process_env


from appimagebuilder.modules.setup.helpers.gstreamer import GStreamer  # noqa: E402

_original_prepare_gst_launch_env = GStreamer._prepare_gst_launch_env


def _prepare_gst_launch_env(self: GStreamer, env) -> dict[str, str]:
    process_env = dict(_original_prepare_gst_launch_env(self, env))
    return _prepend_appdir_library_paths(
        process_env, env.get("APPDIR_LIBRARY_PATH")
    )


# appimage-builder 1.1.0 only forwards GST_* variables to gst-launch. Its
# scanner then cannot resolve the shared libraries already staged in AppDir.
# Keep this compatibility fix local to the GStreamer registry subprocess.
GStreamer._prepare_gst_launch_env = _prepare_gst_launch_env


def _self_test() -> None:
    cases = (
        ("1.22.6ubuntu6", "1.22.6", True),
        ("1.22.6ubuntu6.1", "1.22.6ubuntu6", True),
        ("1.22.6ubuntu6", "1.22.6ubuntu6", False),
        ("1.22.6ubuntu6", "1.22.6ubuntu6.1", False),
    )
    for left, right, expected in cases:
        actual = Package("test", left, "amd64") > Package("test", right, "amd64")
        if actual is not expected:
            raise SystemExit(
                f"Debian version comparison failed: {left!r} > {right!r} was {actual}, expected {expected}"
            )
    loader_env = _prepend_appdir_library_paths(
        {"LD_LIBRARY_PATH": "/host/lib"},
        ["/app/usr/lib/x86_64-linux-gnu", "/app/usr/lib"],
    )
    if loader_env["LD_LIBRARY_PATH"] != (
        "/app/usr/lib/x86_64-linux-gnu:/app/usr/lib:/host/lib"
    ):
        raise SystemExit(
            "AppDir GStreamer loader path self-test failed: "
            f"{loader_env['LD_LIBRARY_PATH']!r}"
        )
    print("AppImage builder Debian version compatibility: OK")
    print("AppImage builder GStreamer AppDir loader path: OK")


if __name__ == "__main__":
    if sys.argv[1:] == ["--self-test"]:
        _self_test()
    else:
        from appimagebuilder.__main__ import __main__

        __main__()
