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

## Pinning the source in the submission manifest (#501)

The release manifest pins the `anura` module to the release tag. A tag can be
moved, so the manifest copied to the Flathub submission repository also carries
the commit the tag resolved to when the release was cut:

```bash
build-aux/pin_source_commit.py --tag v0.2.1          # writes "commit" next to "tag"
build-aux/pin_source_commit.py --tag v0.2.1 --check  # verifies it (CI/review)
```

Run it **after** tagging (the commit must exist) and before copying the manifest
to the submission repository. `release.sh` prints the same reminder with the
resolved SHA at the end of a release.

## Licenses in the bundle

Every license ends up under `share/licenses/io.github.d3msudo.anura/`:

| Owner | Where it comes from | Path |
| --- | --- | --- |
| Anura (MIT) | `install_data('LICENSE', …)` in `meson.build` | `LICENSE` |
| Python modules | `build-commands` in the local manifest (fail-closed: the build stops when no license file is found) | `<package>/LICENSE` |
| Native modules | `post-install` or flatpak-builder's automatic source-license recording (`imlib2`, `scrot`, `libportal` use `COPYING*`) | `<module>/` |
| OCR models | `data/meson.build` | `tessdata_fast/LICENSE` |

Two rules to keep in mind when editing the manifest:

1. **Never make a license install best-effort.** `|| true` and similar make a
   missing notice a silent success; the commands abort instead (`set -e` +
   `test -n "$f"`). Do not print `FATAL: …` inside the command either:
   flatpak-builder echoes every command, and that text reads like a build
   error in the log (this is what made a *present* nanobind license look
   missing).
2. **Build-only modules ship nothing.** `scikit-build-core`, `pybind11` and
   `nanobind` are removed from the runtime after the native extensions are
   built, and their license copies are removed with them, because they are not
   distributed. The app-level `cleanup` covers both the package name and the
   module name used by flatpak-builder's automatic license recording.

The inventory can be verified against a built prefix with
`build-aux/check_license_inventory.py --root <prefix>` (see #493).

## Permissions (`finish-args`)

Every static permission is mapped to the feature that needs it.
`tests/test_flatpak_manifest_hygiene.py` fails when the manifest and this table
drift apart, so a new permission has to be justified here first (#498).

| Flag | Why Anura needs it |
| --- | --- |
| `--share=network` | Downloads Tesseract language models from GitHub; when the user asks for speech, sends the selected text to Google TTS |
| `--share=ipc` | Shared memory with X11 and the portals (screenshot buffers) |
| `--socket=wayland` | Native Wayland window; required on Wayland sessions |
| `--socket=x11` | X11 window plus the `scrot` screenshot fallback, which is X11-only |
| `--socket=pulseaudio` | Playback of the generated speech through GStreamer |
| `--device=dri` | GPU rendering for GTK4 |
| `--filesystem=xdg-pictures:ro` | Open an image from Pictures and accept drag-and-drop from it |
| `--filesystem=xdg-download:ro` | Same, for Downloads |
| `--filesystem=xdg-desktop:ro` | Same, for Desktop |
| `--filesystem=xdg-documents:ro` | Same, for Documents |
| `--talk-name=org.a11y.Bus` | Screen-reader support (AT-SPI) |
| `--talk-name=org.freedesktop.portal.Desktop` | Screenshot portal, file chooser, notifications, external-editor handoff |
| `--talk-name=org.freedesktop.Notifications` | libnotify fallback when no notification portal is available |
| `--env=TESSDATA_PREFIX=/app/share/tessdata` | Tells Tesseract where the bundled models live |

Notes:

- The four read-only XDG folders are under review in #490: they let the file
  chooser and drag-and-drop hand over images from the standard folders without
  extra portal round-trips.
- Wayland and X11 (including the `scrot` fallback) still need a manual runtime
  test on a desktop session. The CI only runs `anura --help` inside the sandbox
  (#498, #500).
