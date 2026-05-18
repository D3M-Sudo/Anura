---
name: testing-anura
description: Verify changes to the Anura GTK4 OCR app. Use when running lint, pytest, and end-to-end checks on this repo, especially when the host machine lacks GTK4 / libadwaita 1.6 / blueprint-compiler 0.16 / GNOME 49 dev packages.
---

# Testing Anura

Anura is a GTK4 + Libadwaita app distributed as a Flatpak against the GNOME 49 runtime. The full GUI test stack is heavy (meson, ninja, pkg-config, libadwaita-1-dev ≥ 1.6, libportal-1-dev, blueprint-compiler 0.16, GNOME 49 runtime). Most generic Ubuntu / Devin VMs **do not** have all of these, and the system `blueprint-compiler` is usually too old to parse this project's `.blp` syntax. This skill describes what to do in that situation.

## Always run first (works on every VM)

```bash
# Lint
uv run ruff check .

# Pure-Python pytest subset
uv run pytest tests/ -m "not gtk" -v
```

Expected: `All checks passed!` and `148 passed, 29 deselected` (counts will drift over time — the important part is zero failures and the GTK-marked subset being deselected, not skipped). Note: the "deselected" count is lower now because some tests originally marked `@pytest.mark.gtk` now skip gracefully via `pytest.importorskip("gi")` instead. These skipped tests no longer appear in the "deselected" category.

## When you can run the gtk-marked tests

The `@pytest.mark.gtk` tests need:

- system PyGObject (`/usr/lib/python3/dist-packages/gi`)
- typelibs for Gtk-4.0, Adw-1, Gio, GLib, GObject, GdkPixbuf, plus optionally Notify-0.7, Xdp-1.0, Gst-1.0

Incantation (per the repo's `.windsurf/rules/testing.md`):

```bash
uv run env \
  PYTHONPATH="/usr/lib/python3/dist-packages:$PYTHONPATH" \
  GI_TYPELIB_PATH="/usr/lib/x86_64-linux-gnu/girepository-1.0:/usr/lib/girepository-1.0" \
  GSETTINGS_SCHEMA_DIR="builddir" \
  pytest tests/ -m gtk -v
```

`builddir/` is produced by `meson setup builddir`. If meson is not available, you cannot generate the gschema either — skip this and use the AST trick below.

**Caveat (uv venv vs apt python3-gi ABI):** the `uv run env PYTHONPATH=...` recipe only works if the uv venv Python *matches* the system Python that apt's `python3-gi` was built for. On current Devin Ubuntu jammy VMs the project's uv venv is **Python 3.12** but apt's `python3-gi` only ships `_gi.cpython-310-x86_64-linux-gnu.so` (3.10). In that case the import fails with `ImportError: cannot import name '_gi' from partially initialized module 'gi'`. Two ways out:

1. Run gi-touching test code via `subprocess.run(["/usr/bin/python3", "-c", probe, ...])` from inside the harness — system python3 is 3.10 and has working `gi` natively. This is the fast path for runtime probes that don't need any project Python deps.
2. `uv pip install pygobject` to compile a 3.12-compatible PyGObject into the venv — but this needs `pkg-config`, `libcairo2-dev`, `libgirepository1.0-dev` apt packages first; usually not worth it.

## System-py3 GTK harness recipe (use when the test must construct real GTK widgets)

For bugs that require *actual* GTK semantics — e.g. action dispatch, signal connection, template binding — stand up a small one-shot harness on `/usr/bin/python3`. This is what to do when AST-level reasoning isn't enough and a Flatpak GUI run isn't possible.

**One-time apt deps (idempotent on the Devin env):**

```bash
sudo apt-get install -y \
  gir1.2-gtk-4.0 gir1.2-adw-1 gir1.2-xdp-1.0 \
  libgirepository1.0-dev libzbar0 tesseract-ocr
sudo ldconfig            # so pyzbar's ctypes loader sees libzbar.so.0
```

**System-py3 user-site project deps** (so `/usr/bin/python3` can `import anura.services.*` without crashing on third-party imports):

```bash
/usr/bin/python3 -m pip install --user \
  loguru pytesseract pillow pyzbar requests gtts
```

**Run the harness** with `DISPLAY=:0` so `Adw.ApplicationWindow.present()` doesn't crash the X bridge:

```bash
DISPLAY=:0 /usr/bin/python3 /tmp/harness.py
```

Proven harness shape for action-dispatch / wiring bugs (verified against PR #29 ShareRow bug):

```python
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gio, GLib, Gtk

calls = []
def on_share(_a, p): calls.append(p.get_string())

app = Adw.Application(application_id="com.example.AnuraTest")

def on_activate(_app):
    win = Adw.ApplicationWindow(application=app)
    a = Gio.SimpleAction.new("share", GLib.VariantType.new("s"))
    a.connect("activate", on_share)
    win.add_action(a)
    row = Gtk.ListBoxRow(); box = Gtk.ListBox(); box.append(row)
    win.set_content(box); win.present()
    print("win.share   :", row.activate_action("win.share",    GLib.Variant.new_string("X")))
    print("window.share:", row.activate_action("window.share", GLib.Variant.new_string("X")))
    print("calls       :", calls)
    GLib.idle_add(app.quit)

app.connect("activate", on_activate)
app.run([])
```

For service methods that don't need GTK at all but are gated behind a heavy `__init__` (e.g. `ScreenshotService._log_portal_environment()` depends only on `os.environ` + loguru, but `__init__` brings up GSettings), bypass `__init__` entirely with `__new__` + manual slot init:

```python
from unittest.mock import patch
from loguru import logger
from anura.services import screenshot_service as ss_mod

svc = ss_mod.ScreenshotService.__new__(ss_mod.ScreenshotService)
svc._env_diagnostics_logged = False

captured = []
sink = logger.add(lambda m: captured.append(m.record["message"]), level="INFO")
try:
    with patch.dict("anura.services.screenshot_service.os.environ",
                    {"XDG_CURRENT_DESKTOP": "GNOME", ...}, clear=False), \
         patch.object(ss_mod, "_is_flatpak_environment", return_value=True):
        svc._log_portal_environment()
        svc._log_portal_environment()  # must be no-op (one-shot)
finally:
    logger.remove(sink)
```

This is the canonical pattern for service-method-in-isolation tests in this repo.

## When you can't run the gtk-marked tests (common)

If any of these are true, a *live* GUI pass on this VM is not realistic:

- `pkg-config`, `meson`, `ninja-build`, or `flatpak` not installed
- `libadwaita-1-dev` missing or < 1.6
- `libportal-1-dev` missing
- `blueprint-compiler --help | head` says version `0~20220302-3` (or anything that can't parse `template $Name : Type` — you'll see an error on line 4 of any `.blp`)
- no GNOME 49 runtime

In that case:

1. **Trust the live `flatpak-builder` CI on the PR.** It builds against `ghcr.io/flathub-infra/flatpak-github-actions:gnome-49`, which is the real production target. If it's green, the `.blp` files compiled, the `.ui` resources bundled, the `@Gtk.Template` widgets bind, and the app launches. Always quote the CI status in your test report.
2. **For changed Python production code paths, use AST extraction to bypass gi.** Most of the interesting bits in `anura/services/share_service.py`, `anura/main.py`, `anura/utils/text_preprocessor.py`, `anura/window.py` are pure functions (URL builders, signal-handler helpers, text cleanup) that don't actually touch GTK at runtime — they just live inside a class that inherits from `GObject.Object`. Extract them with `ast.parse`, drop the `@staticmethod` / type-annotation decorations, and `exec` them in a clean namespace. Pattern:

```python
import ast, types

src = open("anura/services/share_service.py").read()
tree = ast.parse(src)
cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "ShareService")

fns = []
for node in cls.body:
    if isinstance(node, ast.FunctionDef) and node.name.startswith("get_link_"):
        node.decorator_list = []                       # drop @staticmethod
        for arg in node.args.args + node.args.kwonlyargs:
            arg.annotation = None                      # drop annotations
        node.returns = None
        fns.append(node)

mod = ast.Module(body=fns, type_ignores=[])
ast.fix_missing_locations(mod)
ns = {"quote": __import__("urllib.parse", fromlist=["quote"]).quote}
exec(compile(mod, "<extract>", "exec"), ns)

print(ns["get_link_x"]("Hello world"))
```

For methods that do touch self / non-static helpers, bind them to a stub:

```python
stub = type("Stub", (), {})()
stub._setup_signal_handlers   = types.MethodType(ns["_setup_signal_handlers"],   stub)
stub._restore_signal_handlers = types.MethodType(ns["_restore_signal_handlers"], stub)
```

3. **For `.blp` / `.py` template wiring (e.g. ShortcutsOverlay), do code-grounded static verification.** Read both files, confirm:
   - `Adw.Window` templates use `[content]`, never `[child]`. Every other `.blp` in this repo uses `[content]`; `[child]` will silently break the Blueprint compile.
   - `@Gtk.Template(resource_path=f"{RESOURCE_PREFIX}/<name>.ui")` matches the gresource entry in `data/io.github.d3msudo.anura.gresource.xml` and the `.ui` filename produced by `data/meson.build`.
   - `Gtk.Template.Child()` declarations match the IDs declared in the `.blp`.
   - Any `EventControllerKey`-based shortcut handler is constructed AND added with `self.add_controller(...)`. A handler defined but never attached is the BUG-6 shape.
4. **For spinner / async error-handling regressions (BUG-9 shape), trace every `return` and `except` inside the relevant `_on_*_loaded` / async-callback method** and verify a `self.welcome_page.spinner.set_visible(False)` (or equivalent) precedes each. The success path is fine because `on_shot_done` / `on_shot_error` hide the spinner later — only error early-returns are at risk.

## Verifying gresource-bundled icons (e.g. share-*-symbolic.svg) outside Meson

When a PR adds new files to `data/io.github.d3msudo.anura.gresource.xml`, the strongest *non-Meson* test is to actually compile the bundle and look up each new path through `Gio.resources_lookup_data`. Two pitfalls:

1. `glib-compile-resources` is **not** in `libglib2.0-bin` (only `gresource`, `gio`, `gsettings` are). Install `libglib2.0-dev-bin`:

   ```bash
   sudo apt-get install -y libglib2.0-dev-bin
   ```

2. The full `data/io.github.d3msudo.anura.gresource.xml` references Meson-generated `.ui` files (compiled from `.blp` at build time) which are **absent from the source tree**, so compiling the manifest verbatim fails with `Failed to locate "window.ui" in any source directory.`. Build a **subset manifest** on the fly that includes only the files that actually exist on disk:

   ```python
   import xml.etree.ElementTree as ET, subprocess
   tree = ET.parse("data/io.github.d3msudo.anura.gresource.xml")
   svg_only = [(f.text, f.attrib) for f in tree.getroot().findall(".//file") if f.text.endswith(".svg")]
   prefix = tree.getroot().find("gresource").attrib["prefix"]
   with open("/tmp/svg_only.gresource.xml", "w") as fh:
       fh.write(f'<?xml version="1.0" encoding="UTF-8"?><gresources>'
                f'<gresource prefix="{prefix}">')
       for t, _ in svg_only:
           fh.write(f"<file>{t}</file>")
       fh.write("</gresource></gresources>")
   subprocess.run(["glib-compile-resources", "/tmp/svg_only.gresource.xml",
                   "--target=/tmp/anura.gresource", "--sourcedir=data"], check=True)
   ```

   Then load + look up via `/usr/bin/python3` (see ABI caveat above):

   ```python
   import gi; gi.require_version("Gio", "2.0")
   from gi.repository import Gio
   res = Gio.Resource.load("/tmp/anura.gresource")
   Gio.resources_register(res)
   payload = Gio.resources_lookup_data("/com/github/d3msudo/anura/icons/scalable/actions/share-bluesky-symbolic.svg",
                                       Gio.ResourceLookupFlags.NONE)
   # Older PyGObject returns Bytes directly; newer returns (Bytes, flags). Handle both.
   data = bytes((payload[0] if isinstance(payload, tuple) else payload).get_data())
   ```

## Things that bite

- **`win.` prefix vs `window.` prefix on `Adw.ApplicationWindow`.** Actions added via `Adw.ApplicationWindow.add_action()` (inherited from `Gio.ActionMap` via `Gtk.ApplicationWindow`) are exposed as `win.<name>`, **never** `window.<name>`. Calling `widget.activate_action("window.share", ...)` returns `False` and the handler never runs — with **no log line, no warning, no error**. This was the Bug #2 shape on PR #29 (every share-popover row was a silent no-op). General rule: when a click "does nothing" and there's nothing in the debug log, the first thing to check is whether the action prefix matches the registrar (`win.` for windows, `app.` for `Gio.Application`-level actions, `<custom>.` only with `widget.insert_action_group(...)`).
- `Gtk.MenuButton` does **not** implement `Gtk.Actionable`. `action-name: "win.share";` on a `MenuButton` will fail to compile against a current blueprint-compiler. If you see that on a `MenuButton`, remove it and let the inner widget (e.g. `ShareRow` / `Gtk.Button`) carry the action instead.
- `Adw.Window` exposes a `content` property, not a raw `child` slot. Use `[content]`, not `[child]`. Same for `Adw.ApplicationWindow`.
- A `try: return ... except: ... else: ...` block has an **unreachable** `else` because the `return` exits the `try` without falling through. Use `finally` for cleanup that must run on every exit including `return`.
- `quote(text)` is not idempotent. Encoding twice turns `Hello world` into `Hello%2520world`. If a function is meant to be a URL builder, it should accept *raw* text and call `quote` exactly once.
- `pytest.mark.gtk` tests that look like "unit tests" still need PyGObject — collection alone imports the module under test.
- Don't try to install `python3-pytesseract` from apt; it's not packaged. Install via `uv add pytesseract` for the project, or skip the harness if you don't need it.
- `glib-compile-resources` is in **`libglib2.0-dev-bin`**, not `libglib2.0-bin`. The latter ships only the runtime CLI helpers (`gresource`, `gio`, `gsettings`). Forgetting this wastes a debug cycle.
- After installing `libzbar0`, run `sudo ldconfig` once — `pyzbar.zbar_library.load()` uses ctypes / `find_library` and a missing ldconfig refresh produces `ImportError: Unable to find zbar shared library` even though the file is right there in `/usr/lib/x86_64-linux-gnu/libzbar.so.0`.

## Testing Drag-and-Drop Functionality

### GTK Drop Target Testing

When testing drag-and-drop functionality in Anura, follow this workflow:

#### 1. Build Project First
```bash
# Always build before testing UI components
PATH=$PWD/.venv/bin:$PATH .venv/bin/meson setup builddir --reconfigure
PATH=$PWD/.venv/bin:$PATH .venv/bin/meson compile -C builddir
```

#### 2. Register GTK Resources
```python
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
gi.require_version('Gio', '2.0')
from gi.repository import Gio, Gtk, Adw, Gdk, GLib

# Register the resource file before importing Anura modules
resource = Gio.Resource.load('builddir/data/io.github.d3msudo.anura.gresource')
resource._register()
```

#### 3. Test Drop Target Implementation
```python
# Test that all drag-and-drop methods exist
from anura.window import AnuraWindow
required_methods = ['on_dnd_enter', 'on_dnd_leave', 'on_dnd_motion', 'on_dnd_drop']

for method in required_methods:
    assert method in dir(AnuraWindow), f"Missing method: {method}"
```

#### 4. Common Drag-and-Drop Issues

**GTK Assertion Errors:**
- **Problem**: `gtk_drop_target_handle_event: assertion 'self->drop == gdk_dnd_event_get_drop (event)' failed`
- **Root Cause**: Drop target attached to wrong widget (e.g., `split_view` instead of specific widget)
- **Fix**: Attach drop target to `welcome_page.welcome` instead of `split_view`

**Drop Target Lifecycle:**
- **Problem**: Missing event handlers cause state mismatches
- **Solution**: Implement all four handlers: `enter`, `leave`, `motion`, `drop`
- **Pattern**: Always add visual feedback in `enter`, cleanup in `leave`/`drop`

#### 5. CSS for Drag Feedback
```css
.drag-hover {
    background: alpha(@accent_color, 0.1);
    border: 2px dashed @accent_color;
    border-radius: 12px;
    transition: all 200ms ease;
}
```

#### 6. Testing Workflow
1. **Build project** (meson compile)
2. **Register resources** (Gio.Resource.load)
3. **Test method existence** (dir() check)
4. **Verify drop target attachment** (welcome_page.welcome.add_controller)
5. **Test CSS syntax** (GTK theme variables with @ prefix)

#### 7. Debugging Tips
- **Use proper PYTHONPATH**: `PYTHONPATH="/usr/lib/python3/dist-packages:$PYTHONPATH"`
- **Set GSETTINGS_SCHEMA_DIR**: `GSETTINGS_SCHEMA_DIR="builddir"`
- **Check resource registration**: Ensure `.gresource` file is loaded before importing modules
- **GTK CSS syntax**: Use `@variable` syntax for theme variables, not standard CSS variables

#### 8. Common Pitfalls
- **Wrong widget target**: Don't attach drop targets to container widgets that span multiple navigation contexts
- **Missing cleanup**: Always remove CSS classes in `leave` and `drop` handlers
- **Thread safety**: Never modify GTK widgets from background threads (use `GLib.idle_add`)
- **Resource timing**: Register resources before importing any Anura modules that use `@Gtk.Template`
