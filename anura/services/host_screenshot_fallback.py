# host_screenshot_fallback.py
#
# Copyright 2026 D3M-Sudo (Anura fork and modifications)
#
# MIT License
"""Host-side screenshot fallback for environments where xdg-desktop-portal
does not expose the Screenshot interface.

Some desktop sessions ship a portal frontend but no backend that exposes
``org.freedesktop.impl.portal.Screenshot``. The most common case in the wild
is **LXQt / Xfce / Openbox on Ubuntu 24.04+**, where ``xdg-desktop-portal``,
``xdg-desktop-portal-gtk`` and ``xdg-desktop-portal-kde`` are all installed,
but the kde backend only registers Screenshot when KWin is the active
window manager. In that case Anura previously had no recourse — the user
saw "Screenshot failed" and the feature was effectively broken on their
desktop.

This module describes how to invoke common host-side screenshot tools
(gnome-screenshot, xfce4-screenshooter, spectacle, scrot, maim, ImageMagick
``import``) via ``flatpak-spawn --host``. The actual subprocess execution
lives in ``screenshot_service.py`` (using ``Gio.Subprocess`` per project
rules); this module is intentionally pure-Python so command construction
and tool ordering can be unit-tested without GTK / GLib.

Note: the Flatpak manifest needs ``--talk-name=org.freedesktop.Flatpak`` for
``flatpak-spawn`` to reach the host. The fallback only runs inside the
sandbox; on a host install of Anura the portal pathway is the only one used.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class HostScreenshotTool:
    """A host-side X11 screenshot CLI.

    The ``argv`` is built as ``[name, *flags, output_path]``. Tools whose
    output flag is positional (e.g. ``import out.png``) can use empty
    ``flags``. Tools whose output flag takes a separate argument
    (e.g. ``gnome-screenshot -f out.png``) put the flag last in ``flags``
    so the path follows it.
    """

    name: str
    flags: tuple[str, ...]


# Order matters: tools with the best UX on a generic X11 desktop come
# first. Every tool here supports a region/area selection mode so the
# user can pick the same area they would have selected through the
# native portal screenshot dialog.
HOST_SCREENSHOT_TOOLS: tuple[HostScreenshotTool, ...] = (
    HostScreenshotTool(name="gnome-screenshot", flags=("-a", "-f")),
    HostScreenshotTool(name="xfce4-screenshooter", flags=("-r", "-s")),
    HostScreenshotTool(name="spectacle", flags=("-r", "-b", "-n", "-o")),
    HostScreenshotTool(name="scrot", flags=("-s",)),
    HostScreenshotTool(name="maim", flags=("-s",)),
    # ImageMagick's ``import`` puts the output path positionally with no
    # preceding flag.
    HostScreenshotTool(name="import", flags=()),
)


def build_screenshot_argv(tool: HostScreenshotTool, output_path: str, in_flatpak: bool = True) -> list[str]:
    """Build the argv that captures into ``output_path``.

    If ``in_flatpak`` is True, uses ``flatpak-spawn --host`` to reach the host.
    """
    argv = [tool.name, *tool.flags, output_path]
    if in_flatpak:
        argv = ["flatpak-spawn", "--host"] + argv
    return argv


def build_detection_argv(
    tools: Sequence[HostScreenshotTool] = HOST_SCREENSHOT_TOOLS,
    in_flatpak: bool = True,
) -> list[str]:
    """Build an argv that prints the first available tool.

    If ``in_flatpak`` is True, uses ``flatpak-spawn --host``.
    """
    for tool in tools:
        _validate_tool_name(tool.name)
    tool_names = " ".join(tool.name for tool in tools)
    script = f'for t in {tool_names}; do if command -v "$t" >/dev/null 2>&1; then echo "$t"; exit 0; fi; done; exit 1'

    if in_flatpak:
        return ["flatpak-spawn", "--host", "sh", "-c", script]
    return ["sh", "-c", script]


def _validate_tool_name(name: str) -> None:
    """Reject anything that isn't a plain executable name.

    Defense-in-depth: ``HOST_SCREENSHOT_TOOLS`` is hard-coded so this should
    never trigger, but it guards against a future caller passing untrusted
    input into ``build_detection_argv``.
    """
    if not name or not all(ch.isalnum() or ch in "-_" for ch in name):
        msg = f"unsafe tool name: {name!r}"
        raise ValueError(msg)


def parse_detection_output(stdout: str) -> str | None:
    """Extract the chosen tool name from the detection script's stdout.

    Returns ``None`` if no tool was detected (empty output / unrecognised
    name). The detection script prints the tool name on a single line.
    """
    if not stdout:
        return None
    name = stdout.strip().splitlines()[0].strip() if stdout.strip() else ""
    if not name:
        return None
    if not any(tool.name == name for tool in HOST_SCREENSHOT_TOOLS):
        return None
    return name


def find_tool_by_name(name: str) -> HostScreenshotTool | None:
    """Return the ``HostScreenshotTool`` with the given name, or ``None``."""
    for tool in HOST_SCREENSHOT_TOOLS:
        if tool.name == name:
            return tool
    return None
