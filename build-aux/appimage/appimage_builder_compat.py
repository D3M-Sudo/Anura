#!/usr/bin/env python3
"""Run appimage-builder with Debian-native version ordering for Ubuntu packages.

appimage-builder 1.1.0 compares APT package versions with PEP 440. Ubuntu
versions such as 1.22.6ubuntu6 are valid Debian versions but invalid PEP 440
versions. apt_pkg.version_compare implements the same ordering as dpkg.
"""

from __future__ import annotations

import sys

import apt_pkg

apt_pkg.init_system()

from appimagebuilder.modules.deploy.apt.package import Package  # noqa: E402


def _debian_version_greater_than(self: Package, other: object) -> bool:
    if not isinstance(other, Package):
        return NotImplemented
    return apt_pkg.version_compare(self.version, other.version) > 0


Package.__gt__ = _debian_version_greater_than


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
    print("AppImage builder Debian version compatibility: OK")


if __name__ == "__main__":
    if sys.argv[1:] == ["--self-test"]:
        _self_test()
    else:
        from appimagebuilder.__main__ import __main__

        __main__()
