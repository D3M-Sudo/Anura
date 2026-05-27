# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""Sandboxed X11 screenshot fallback for environments where xdg-desktop-portal
does not expose the Screenshot interface.

Some desktop sessions (e.g., LXQt, Openbox) ship a portal frontend but no backend
that exposes ``org.freedesktop.impl.portal.Screenshot``. In such cases, if the
environment is X11, Anura falls back to host-side tools via flatpak-spawn.
"""

from __future__ import annotations

import os
import re
import shutil

# Allowed screenshot tools for security validation
ALLOWED_TOOLS = {
    "gnome-screenshot",
    "maim",
    "import",
    "scrot",
    "xfce4-screenshooter",
    "spectacle",
}


def _is_flatpak() -> bool:
    """Detect if running in Flatpak sandbox."""
    return os.path.exists("/.flatpak-info") or "FLATPAK_ID" in os.environ


def _validate_tool_name(name: str) -> bool:
    """Validate tool name to prevent shell injection or unauthorized execution."""
    # Check against allowed tools
    if name not in ALLOWED_TOOLS:
        return False
    # Extra check for dangerous characters just in case
    return bool(re.match(r"^[a-z0-9\-]+$", name))


def build_fallback_argv(tool: str, output_path: str) -> list[str]:
    """Build the argv for the specified host tool.

    Wraps the command in flatpak-spawn --host if running inside a sandbox.
    """
    if not _validate_tool_name(tool):
        raise ValueError(f"Unsupported or invalid screenshot tool: {tool}")

    cmd = []

    if tool == "gnome-screenshot":
        cmd = [tool, "-a", "-f", output_path]
    elif tool == "maim" or tool == "scrot":
        cmd = [tool, "-s", output_path]
    elif tool == "import":
        # ImageMagick import
        cmd = [tool, output_path]
    elif tool == "xfce4-screenshooter":
        cmd = [tool, "-r", "-s", output_path]
    elif tool == "spectacle":
        cmd = [tool, "-r", "-b", "-o", output_path]
    else:
        # Generic fallback for other tools
        cmd = [tool, output_path]

    if _is_flatpak():
        return ["flatpak-spawn", "--host", *cmd]

    return cmd


def detect_host_tools() -> list[str]:
    """Detect which allowed screenshot tools are available on the host.

    In Flatpak, this check is limited by the sandbox, but we can assume
    common tools if running on the host.
    """
    available = []
    # If not in flatpak, we can check directly
    if not _is_flatpak():
        for tool in ALLOWED_TOOLS:
            if shutil.which(tool):
                available.append(tool)
    else:
        # In flatpak, we can't easily check host binaries, so we rely on
        # a prioritized list that we try via flatpak-spawn.
        available = [
            "gnome-screenshot",
            "maim",
            "scrot",
            "import",
            "xfce4-screenshooter",
            "spectacle",
        ]
    return available
