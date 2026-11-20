# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""Read the active GDK text clipboard from inside the installed Flatpak."""

import gi

gi.require_version("Gdk", "4.0")
gi.require_version("Gtk", "4.0")
from gi.repository import Gdk, GLib, Gtk


def main() -> int:
    Gtk.init()
    display = Gdk.Display.get_default()
    if display is None:
        raise RuntimeError("Flatpak clipboard reader could not open the GDK display")

    loop = GLib.MainLoop()
    result: dict[str, str | None] = {"text": None, "error": None}

    def on_text_read(clipboard: Gdk.Clipboard, async_result) -> None:
        try:
            result["text"] = clipboard.read_text_finish(async_result)
        except GLib.Error as exc:
            result["error"] = exc.message
        loop.quit()

    def on_timeout() -> bool:
        result["error"] = "clipboard read timed out"
        loop.quit()
        return GLib.SOURCE_REMOVE

    clipboard = display.get_clipboard()
    clipboard.read_text_async(None, on_text_read)
    GLib.timeout_add_seconds(5, on_timeout)
    loop.run()

    if result["error"] is not None:
        raise RuntimeError(f"Flatpak clipboard read failed: {result['error']}")
    if not result["text"]:
        raise RuntimeError("Flatpak clipboard read returned no text")
    print(f"CLIPBOARD_READ_OK: {result['text'][:80]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
