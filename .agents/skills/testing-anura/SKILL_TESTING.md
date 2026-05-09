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

Expected: `All checks passed!` and `57 passed, 42 deselected` (counts will drift over time — the important part is zero failures and the GTK-marked subset being deselected, not skipped).

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
   - `@Gtk.Template(resource_path=f"{RESOURCE_PREFIX}/<name>.ui")` matches the gresource entry in `data/com.github.d3msudo.anura.gresource.xml` and the `.ui` filename produced by `data/meson.build`.
   - `Gtk.Template.Child()` declarations match the IDs declared in the `.blp`.
   - Any `EventControllerKey`-based shortcut handler is constructed AND added with `self.add_controller(...)`. A handler defined but never attached is the BUG-6 shape.
4. **For spinner / async error-handling regressions (BUG-9 shape), trace every `return` and `except` inside the relevant `_on_*_loaded` / async-callback method** and verify a `self.welcome_page.spinner.set_visible(False)` (or equivalent) precedes each. The success path is fine because `on_shot_done` / `on_shot_error` hide the spinner later — only error early-returns are at risk.

## Things that bite

- `Gtk.MenuButton` does **not** implement `Gtk.Actionable`. `action-name: "win.share";` on a `MenuButton` will fail to compile against a current blueprint-compiler. If you see that on a `MenuButton`, remove it and let the inner widget (e.g. `ShareRow` / `Gtk.Button`) carry the action instead.
- `Adw.Window` exposes a `content` property, not a raw `child` slot. Use `[content]`, not `[child]`. Same for `Adw.ApplicationWindow`.
- A `try: return ... except: ... else: ...` block has an **unreachable** `else` because the `return` exits the `try` without falling through. Use `finally` for cleanup that must run on every exit including `return`.
- `quote(text)` is not idempotent. Encoding twice turns `Hello world` into `Hello%2520world`. If a function is meant to be a URL builder, it should accept *raw* text and call `quote` exactly once.
- `pytest.mark.gtk` tests that look like "unit tests" still need PyGObject — collection alone imports the module under test.
- Don't try to install `python3-pytesseract` from apt; it's not packaged. Install via `uv add pytesseract` for the project, or skip the harness if you don't need it.

## Reporting

If the GUI pass is replaced by AST + static + CI, say so explicitly in the report. Quote the CI check status (5/5 green names) on the latest commit — that's the real GUI build evidence. Don't claim a desktop pass when there wasn't one.

## Devin Secrets Needed

None. The repo is public and tests are all local. CI on github.com works with the default `gh` auth.
