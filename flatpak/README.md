# flatpak/

Two manifests live here. Only one of them should ever be edited by hand.

## `io.github.d3msudo.anura.local.json` — edit this one

The single source of truth, maintained by hand and by dependency-sync
tooling. Used for local builds/tests and by all dependency automation
(`build-aux/sync_dependencies.py`, `.github/workflows/dependency-sync.yml`,
FEDC via `.github/workflows/flatpak-dependencies.yml`). Its `anura` module
builds from the working tree (`"type": "dir", "path": ".."`), so it always
reflects local changes, including uncommitted ones.

Build/test locally with:

```bash
flatpak-builder --force-clean builddir flatpak/io.github.d3msudo.anura.local.json
flatpak-builder --run builddir flatpak/io.github.d3msudo.anura.local.json anura
```

## `io.github.d3msudo.anura.json` — never edit this one

The Flathub/release manifest. **Generated automatically by
`build-aux/release.sh`** from `io.github.d3msudo.anura.local.json` at every
release: every module is copied verbatim except the `anura` module's source,
which is rewritten from `dir` to `git` pinned at the release tag, and the
local-only top-level `branch` / `separate-locales` keys, which are dropped.

Do not hand-edit it, and do not add it back to `sync_dependencies.py`'s
`MANIFESTS` list or to any Dependabot/CI step that edits manifests directly —
that defeats the point of generating it. `build-aux/release.sh` runs
`check_manifest_consistency.py`, `check_tessdata_consistency.py`, and
`check_runtime_dependency_coverage.py --manifest both` as a self-check right
after generating it, so a bad generation fails the release rather than
shipping silently.

See `docs/reference/dependencies.md` for the full dependency pipeline and the
release-time vs continuous-CI split of the checks above.
