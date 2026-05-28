from __future__ import annotations

# tests/test_host_screenshot_fallback.py
#
# Pure-Python tests for the host screenshot fallback command builders.
# These tests cover the deterministic argv-construction logic that is
# safe to run under `uv run pytest tests/ -m "not gtk"`. The actual
# Gio.Subprocess execution that consumes these argvs lives in
# screenshot_service.py and is exercised via integration tests.
import pytest

pytest.importorskip("gi")


import pytest

from anura.services.host_screenshot_fallback import (
    HOST_SCREENSHOT_TOOLS,
    HostScreenshotTool,
    _validate_tool_name,
    build_detection_argv,
    build_screenshot_argv,
    find_tool_by_name,
    parse_detection_output,
)


def test_default_tool_chain_starts_with_gnome_screenshot() -> None:
    """gnome-screenshot is the most reliable fallback on most X11 desktops
    (handles selection, has a sensible UI). Putting it first means LXQt /
    Xfce / Cinnamon users get a working tool out-of-the-box."""
    assert HOST_SCREENSHOT_TOOLS[0].name == "gnome-screenshot"


def test_default_tool_chain_includes_x11_classics() -> None:
    """The chain must include scrot, maim and ImageMagick's import — these
    are the historical X11 fallbacks installed on minimal desktops."""
    names = {tool.name for tool in HOST_SCREENSHOT_TOOLS}
    assert {"scrot", "maim", "import"} <= names


def test_build_screenshot_argv_for_gnome_screenshot() -> None:
    tool = HostScreenshotTool(name="gnome-screenshot", flags=("-a", "-f"))
    argv = build_screenshot_argv(tool, "/home/u/Downloads/.anura-shot.png")
    assert argv == [
        "flatpak-spawn",
        "--host",
        "gnome-screenshot",
        "-a",
        "-f",
        "/home/u/Downloads/.anura-shot.png",
    ]


def test_build_screenshot_argv_for_import_has_path_positional() -> None:
    """ImageMagick's `import` puts the output path positionally with no
    preceding flag. Regression test against accidentally inserting a stray
    flag before the path."""
    tool = HostScreenshotTool(name="import", flags=())
    argv = build_screenshot_argv(tool, "/tmp/out.png")
    assert argv == ["flatpak-spawn", "--host", "import", "/tmp/out.png"]


def test_build_screenshot_argv_for_scrot_uses_selection_flag() -> None:
    tool = HostScreenshotTool(name="scrot", flags=("-s",))
    argv = build_screenshot_argv(tool, "/tmp/out.png")
    assert argv == ["flatpak-spawn", "--host", "scrot", "-s", "/tmp/out.png"]


def test_build_screenshot_argv_for_spectacle() -> None:
    tool = HostScreenshotTool(name="spectacle", flags=("-r", "-b", "-n", "-o"))
    argv = build_screenshot_argv(tool, "/tmp/out.png")
    # -b (background), -n (no notify), -r (rectangular region), -o (output) — no
    # flag should swallow the output path.
    assert argv[-1] == "/tmp/out.png"
    assert argv[:6] == ["flatpak-spawn", "--host", "spectacle", "-r", "-b", "-n"]


def test_build_detection_argv_starts_with_flatpak_spawn() -> None:
    argv = build_detection_argv()
    assert argv[:2] == ["flatpak-spawn", "--host"]
    assert argv[2] == "sh"
    assert argv[3] == "-c"


def test_build_detection_argv_lists_all_tools_in_order() -> None:
    """The detection script must check tools in the same order as
    HOST_SCREENSHOT_TOOLS so the user gets the highest-priority tool that
    is actually installed."""
    argv = build_detection_argv()
    script = argv[4]
    # Walk the tool names in order and confirm each appears in the script
    # in that order (no shuffling by hash / dict iteration).
    last = -1
    for tool in HOST_SCREENSHOT_TOOLS:
        idx = script.find(tool.name)
        assert idx > last, f"{tool.name} appears out of order in script: {script}"
        last = idx


def test_build_detection_argv_uses_command_v_not_which() -> None:
    """`command -v` is POSIX and works in /bin/sh; `which` is not POSIX
    and is missing on minimal systems. Detection must use `command -v`."""
    script = build_detection_argv()[4]
    assert "command -v" in script
    assert "which " not in script


def test_validate_tool_name_rejects_shell_injection() -> None:
    """Defense-in-depth: even though tool names are hard-coded, a future
    refactor must not allow shell metacharacters into the detection script."""
    for bad in ["foo;rm -rf /", "ls$IFS", "tool|cat", "tool&pwd", "tool name", ""]:
        with pytest.raises(ValueError, match="unsafe tool name"):
            _validate_tool_name(bad)


def test_validate_tool_name_accepts_real_names() -> None:
    """Tool names with hyphens and underscores must pass."""
    for good in ["gnome-screenshot", "xfce4-screenshooter", "scrot", "maim", "x_tool"]:
        _validate_tool_name(good)


def test_build_detection_argv_rejects_unsafe_tool_name() -> None:
    bad_tools = [HostScreenshotTool(name="tool; pwd", flags=())]
    with pytest.raises(ValueError, match="unsafe tool name"):
        build_detection_argv(bad_tools)


@pytest.mark.parametrize(
    ("stdout", "expected"),
    [
        ("gnome-screenshot\n", "gnome-screenshot"),
        ("scrot", "scrot"),
        ("  maim  \n", "maim"),
        ("import\nstray-junk\n", "import"),
    ],
)
def test_parse_detection_output_recognises_known_tools(stdout: str, expected: str) -> None:
    assert parse_detection_output(stdout) == expected


@pytest.mark.parametrize("stdout", ["", "   \n", "totally-unknown-tool\n", "rm\n"])
def test_parse_detection_output_rejects_unknown_or_empty(stdout: str) -> None:
    assert parse_detection_output(stdout) is None


def test_find_tool_by_name_returns_known_tool() -> None:
    tool = find_tool_by_name("scrot")
    assert tool is not None
    assert tool.name == "scrot"
    assert tool.flags == ("-s",)


def test_find_tool_by_name_returns_none_for_unknown() -> None:
    assert find_tool_by_name("not-a-real-tool") is None


def test_tools_are_immutable_dataclasses() -> None:
    """HostScreenshotTool is frozen — guards against accidental mutation
    of the global HOST_SCREENSHOT_TOOLS tuple via attribute access."""
    from dataclasses import FrozenInstanceError

    tool = HOST_SCREENSHOT_TOOLS[0]
    with pytest.raises(FrozenInstanceError):
        tool.name = "evil"  # type: ignore[misc]
