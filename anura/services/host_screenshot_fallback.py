# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class HostScreenshotTool:
    """Represents a screenshot tool available on the host system."""

    name: str
    flags: tuple[str, ...]


# Priority-ordered list of known host screenshot tools.
# gnome-screenshot is preferred as it's the most common and feature-rich.
HOST_SCREENSHOT_TOOLS: tuple[HostScreenshotTool, ...] = (
    HostScreenshotTool("gnome-screenshot", ("-a", "-f")),
    HostScreenshotTool("xfce4-screenshooter", ("-r", "-s")),
    HostScreenshotTool("spectacle", ("-r", "-b", "-n", "-o")),
    HostScreenshotTool("maim", ("-s",)),
    HostScreenshotTool("scrot", ("-s",)),
    HostScreenshotTool("import", ()),
)


def _validate_tool_name(name: str) -> None:
    """Verify that a tool name is safe to be used in a shell command."""
    if not name or not re.match(r"^[a-z0-9_-]+$", name):
        raise ValueError("unsafe tool name")


def build_screenshot_argv(tool: HostScreenshotTool, output_path: str) -> list[str]:
    """Build the argv list for executing a screenshot command on the host."""
    _validate_tool_name(tool.name)
    argv = ["flatpak-spawn", "--host", tool.name]
    argv.extend(tool.flags)
    argv.append(output_path)
    return argv


def build_detection_argv(
    tools: tuple[HostScreenshotTool, ...] = HOST_SCREENSHOT_TOOLS,
) -> list[str]:
    """Build the argv list for a host-side shell script that detects installed tools."""
    # Defense-in-depth: validate all tool names before building the script
    for tool in tools:
        _validate_tool_name(tool.name)

    # Build a compact shell script that echoes the first available tool name
    # We use command -v which is POSIX-compliant and available in most shells.
    checks = [f"command -v {t.name} >/dev/null && echo {t.name}" for t in tools]
    script = " || ".join(checks)

    return ["flatpak-spawn", "--host", "sh", "-c", script]


def parse_detection_output(stdout: str) -> str | None:
    """Parse the output of the detection script to identify the best tool."""
    if not stdout or not stdout.strip():
        return None

    # Take the first line and trim whitespace
    lines = stdout.strip().splitlines()
    if not lines:
        return None
    name = lines[0].strip()

    # Verify it's one of our known tools to prevent surprises
    if any(tool.name == name for tool in HOST_SCREENSHOT_TOOLS):
        return name

    return None


def find_tool_by_name(name: str) -> HostScreenshotTool | None:
    """Retrieve a HostScreenshotTool configuration by its name."""
    for tool in HOST_SCREENSHOT_TOOLS:
        if tool.name == name:
            return tool
    return None
