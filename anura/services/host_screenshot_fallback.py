# host_screenshot_fallback.py
#
# Copyright 2026 D3M-Sudo (Anura fork and modifications)
#
# MIT License
"""Sandboxed X11 screenshot fallback for environments where xdg-desktop-portal
does not expose the Screenshot interface.

Some desktop sessions (e.g., LXQt, Openbox) ship a portal frontend but no backend
that exposes ``org.freedesktop.impl.portal.Screenshot``. In such cases, if the
environment is X11, Anura falls back to a bundled ``scrot`` utility.

Since these minimal desktop environments typically run on X11, granting the
``--socket=x11`` permission allows the sandboxed ``scrot`` to read the root
window directly without escaping the container via ``flatpak-spawn``.
"""

from __future__ import annotations


def build_scrot_argv(output_path: str) -> list[str]:
    """Build the argv for the bundled ``scrot`` tool to capture a region.

    Uses ``-s`` (select) to allow the user to pick an area, similar to the
    standard portal experience.
    """
    return ["scrot", "-s", output_path]
