# Anura — Dependency and Flatpak workflow (current behaviour on `testing`)

This document is the **normative** reference for how Python dependencies flow
from declaration to Flatpak manifests and how automated dependency tooling is
split between workflows. Source of truth: `pyproject.toml`, `uv.lock`,
`build-aux/sync_dependencies.py`,
`build-aux/check_runtime_dependency_coverage.py`,
`build-aux/check_manifest_consistency.py`,
`build-aux/check_tessdata_consistency.py`, `build-aux/release.sh`,
`.github/workflows/dependency-sync.yml`,
`.github/workflows/flatpak-dependencies.yml`, `.github/workflows/main.yml`,
`.github/dependabot.yml`, and `.github/scripts/fedc_certifi.py`.

## Pipeline

```text
pyproject.toml (direct deps)
      |
      v
uv.lock (resolved versions + dependency graph)
      |
      +---> build-aux/sync_dependencies.py --update/--check
      |         synchronises URL + sha256 of python3-* modules in
      |         flatpak/io.github.d3msudo.anura.local.json only — the sole
      |         hand/bot-maintained manifest (anura module: dir source)
      |
      +---> build-aux/check_runtime_dependency_coverage.py (F-005)
                --manifest local (default in CI: main.yml, dependency-sync.yml)
                  every runtime package in the uv.lock closure must have a
                  python3-* module in the local manifest
                --manifest both (release.sh self-check only)
                  same check against both manifests; passes by construction
                  since the release manifest was just generated from the
                  local one

flatpak/io.github.d3msudo.anura.local.json
      |
      v   build-aux/release.sh, at release time only
flatpak/io.github.d3msudo.anura.json  (release / Flathub manifest)
```

**Only `flatpak/io.github.d3msudo.anura.local.json` is hand/bot-maintained.**
`flatpak/io.github.d3msudo.anura.json` (the release/Flathub manifest) is
**generated automatically by `build-aux/release.sh`** at every release and
must never be hand-edited, added to `sync_dependencies.py`'s `MANIFESTS`, or
targeted by any Dependabot/FEDC step directly. Generation copies every module
verbatim from the local manifest, except:

- the `anura` application module's source (`dir` in the local manifest ->
  `git` pinned at the release tag in the generated one), and
- the local-only top-level `branch` / `separate-locales` keys, which are
  dropped.

`build-aux/check_manifest_consistency.py` and
`build-aux/check_tessdata_consistency.py` verify this **as release-time
self-checks inside `build-aux/release.sh`**, right after generation — not as
continuous CI gates. The two manifests are only guaranteed to match
immediately after a release; treating that as an invariant on every push
would fail CI as soon as any dependency changed on `.local.json` before the
next release.

## Ownership boundaries

| Owner | Responsibility |
| --- | --- |
| `sync_dependencies.py` (+ `dependency-sync.yml`) | Version/URL/hash synchronisation of `python3-*` modules from `uv.lock`, against the **local manifest only**. **certifi is excluded here.** |
| FEDC (`flatpak-dependencies.yml` + `fedc_certifi.py`) | **Exclusive owner of `certifi`.** Discovers upstream certifi updates and applies them to the **local manifest** (the release manifest inherits it at the next release). Build-only modules (`pybind11`, `scikit-build-core`) are FEDC/`x-checker-data`-managed, not `uv.lock`-managed. |
| `check_runtime_dependency_coverage.py` (F-005) | Presence check. `--manifest local` (default in CI — `main.yml`, `dependency-sync.yml`): every runtime dependency must be represented in the local manifest. `--manifest both` (release-time self-check inside `build-aux/release.sh` only): same check against both manifests, expected to pass by construction right after generation. For FEDC-owned `certifi`, presence is enforced but the version is never compared. |
| `check_manifest_consistency.py` | Release-time self-check inside `build-aux/release.sh`: confirms the just-generated release manifest matches the local one module-for-module (the `anura` source and the local-only top-level keys excepted). Not a continuous CI gate. |
| `check_tessdata_consistency.py` | Tessdata ref (tag or commit SHA) consistency between `anura/config.py` and both manifests. Runs as a release-time self-check inside `build-aux/release.sh`, for the same reason as `check_manifest_consistency.py`. |
| `build-aux/release.sh` | **Sole generator of the release manifest**, derived from the local one, at release time only. |
| Dependabot (`.github/dependabot.yml`) | Opens PRs against `testing` for `pip` and `github-actions` ecosystems. |

## FEDC / certifi workflow

1. The weekly `flatpak-dependencies.yml` run first checks upstream Flatpak
   versions for the **local manifest only** with flatpak-external-data-checker
   (FEDC) and reports general updates as a `dependencies`-labelled issue (no
   automatic manifest edits for general dependencies).
2. It then restores the local manifest and runs an isolated certifi-only FEDC
   pass: `fedc_certifi.py isolate` builds a temporary manifest containing only
   the certifi source from the local manifest (adding the temporary
   `x-checker-data` FEDC metadata), FEDC updates it, and `fedc_certifi.py
   replace` copies the updated URL/checksum back into the **local manifest**
   (stripping the temporary `x-checker-data`). The release manifest is never
   touched here — it inherits the update automatically the next time
   `build-aux/release.sh` runs.
3. If the certifi update produces a diff, a `chore(deps): update certifi via
   FEDC` PR is opened against `testing` (branch `update-certifi`).

Consequences:

- `uv.lock` and Flatpak certifi versions may intentionally diverge; this is not
  drift.
- Never add certifi version management to `sync_dependencies.py`.
- The production manifests must never contain `x-checker-data` on the certifi
  source; that metadata exists only in the temporary FEDC manifest.

## Dependency-sync workflow (Dependabot PRs)

`dependency-sync.yml` triggers on PRs touching `pyproject.toml` (branches
`testing`, `development`) and on manual dispatch:

1. Regenerates `uv.lock` (`uv lock`).
2. Runs `sync_dependencies.py --update`, `--check`, and the F-005 coverage
   check (`--manifest local`).
3. Commits `uv.lock` + the local manifest back to the Dependabot PR branch.
   The release manifest is never touched here.

## Local verification

Day-to-day (matches what `main.yml` and `dependency-sync.yml` run on every
push/PR/sync — none of this touches the release manifest):

```bash
python3 build-aux/sync_dependencies.py --check
python3 build-aux/check_runtime_dependency_coverage.py --manifest local
```

Release self-checks (what `build-aux/release.sh` runs automatically right
after generating the release manifest; only useful to run manually when
debugging the release script itself, e.g. against a dry-run worktree):

```bash
python3 build-aux/check_manifest_consistency.py
python3 build-aux/check_tessdata_consistency.py
python3 build-aux/check_runtime_dependency_coverage.py --manifest both
```

## GTK (PyGObject) and the development venv

**Status: known environment constraint (documented 2026-09-12).**

PyGObject (`gi`) is **not installable in the project venv** and this is not
expected to change:

- PyGObject publishes **no binary wheels** on PyPI; it must always be compiled.
- Local build environments typically lack the required toolchain
  (`gcc`/`clang`, `pkg-config`, `gobject-introspection`/`girepository` dev
  headers, pycairo build deps), so `uv pip install pygobject` fails at the
  meson/pycairo build stage.
- Anura therefore relies on the **system-provided** `python3-gi` package (GTK
  typelibs come from the host or the Flatpak runtime) — the same model used by
  Flatpak builds, where `gi` is provided by the GNOME runtime.

### Testing GTK-dependent code without a display or venv `gi`

Headless verification of GTK-touching logic (accelerators, GAction
registration, template data) must run with the **system Python interpreter**:

```bash
SP=$(ls -d .venv/lib/python3.*/site-packages)
PYTHONPATH=".:$SP" /usr/bin/python3 script.py
```

- `PYTHONPATH` merges the repo root and the venv site-packages so that
  `anura` imports and pure-Python dependencies (e.g. `loguru`) resolve, while
  `gi` resolves from the system `python3-gi`.
- When importing `Gtk.Template`-based widgets headlessly, **register the
  compiled GResource first**:

  ```python
  with open("builddir/data/io.github.d3msudo.anura.gresource", "rb") as f:
      Gio.Resource.new_from_data(GLib.Bytes.new(f.read()))._register()
  ```

- GObject classes cannot be created via `object.__new__()`; to inspect
  instance methods without a display, call them unbound against a plain
  `types.SimpleNamespace()` stub (e.g.
  `ShortcutsOverlay._setup_shortcuts_data(SimpleNamespace())`).
- Note for PyGObject >= 3.48: `Gtk.accelerator_parse()` returns
  `(success, keyval, mods)` — three values, not two.
- `blueprint-compiler` on the host may lack runtime typelibs (e.g.
  `GtkSource-5`); point it at the Flatpak runtime GIR directory when needed:

  ```bash
  blueprint-compiler compile \
    --typelib-path /var/lib/flatpak/runtime/org.gnome.Platform/x86_64/<ver>/active/files/lib/x86_64-linux-gnu/girepository-1.0 \
    data/ui/<page>.blp
  ```

Reference implementation: the shortcuts-overlay vs `ActionRegistry`
accelerator consistency check (2026-09-12) validated this approach end to end.
