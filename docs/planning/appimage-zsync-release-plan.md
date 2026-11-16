# AppImage multi-architecture and zsync release plan

**Status:** implementation merged via PR [#643](https://github.com/D3M-Sudo/Anura/pull/643); native x86_64/aarch64 AppImage builds, Type 2 repackaging, GitHub Releases `gh-releases-zsync` metadata, companion `.zsync` generation and release-artifact validation are implemented in CI. First public release, real differential-update and representative desktop-integration acceptance remain pending.  
**Scope:** issue [#555](https://github.com/D3M-Sudo/Anura/issues/555)  
**Baseline:** `feature`  
**Relationship to Flatpak:** complementary distribution path; does not replace or duplicate issue #494

> **Document status:** This file preserves the original feasibility and implementation plan. Sections describing proposed tool selection, packaging gates and release integration are historical design context where they conflict with the merged implementation. The current operational contract is [AppImage multi-architecture builds and updates](../reference/appimage-multiarch-release.md). Keep this plan active only for the post-implementation acceptance work tracked in #555.

## 1. Objective

Define a reproducible Linux AppImage distribution path for Anura, initially evaluating `x86_64` and `aarch64`, and publish differential-update metadata usable by compatible managers such as Gear Lever.

An architecture must not be advertised until its AppImage can be built, inspected, launched and tested on a representative target environment. A successful package job on one architecture is not evidence for another.

This document records the original plan and decision gates. The current implementation is tracked in [PR #643](https://github.com/D3M-Sudo/Anura/pull/643); successful CI artifacts are not a release authorization or evidence of a completed Gear Lever differential update.

## 2. Existing release boundary

The release workflow now has separate native Flatpak and AppImage build paths. Flatpak bundles and AppImage/zsync pairs are validated independently; tag publication is gated on the required architecture builds and artifact checks. The normative details are maintained in [Flatpak multi-architecture builds and releases](../reference/flatpak-multiarch-release.md) and [AppImage multi-architecture builds and updates](../reference/appimage-multiarch-release.md).

The two formats remain separate packaging paths with independent architecture-specific outputs and validation. Neither path may reuse a binary artifact across architectures.

The following existing work remains independently owned:

- #494: Flatpak and Flathub multi-architecture coverage;
- #480: removal of architecture-specific paths from packaging;
- #484: validation of the generated release manifest.

## 3. Packaging feasibility and dependency inventory

Before selecting tooling, produce an inventory of runtime requirements and decide whether each is bundled, provided by the host, or unsupported:

- GTK4, Libadwaita and GtkSourceView runtime libraries;
- GObject introspection typelibs and Python GI bindings;
- Tesseract, Leptonica, tessdata lookup and model download/cache paths;
- zxing-cpp and its native shared-library dependencies;
- GStreamer elements used by text-to-speech;
- XDG Desktop Portal integration and desktop-session services;
- GSettings schemas, GResources, translations, desktop entry, icon and MIME metadata.

For each dependency, record its ABI/runtime assumptions, licensing and redistribution obligations, architecture availability, plugin/data lookup requirements and expected host contract. Do not assume that copying ELF shared objects is sufficient: GI typelibs, GTK modules, GStreamer plugins, schemas and data files need explicit runtime-path validation.

The capture path depends on host desktop services. An AppImage cannot bundle the host's portal service or guarantee a portal backend. Document the host requirements and test the portal hand-off in supported desktop sessions. Do not claim that an AppImage is fully self-contained where host services remain necessary.

## 4. Toolchain selection

Evaluate a maintained AppImage toolchain (for example, linuxdeploy with appimagetool, or a demonstrably maintained alternative) against these criteria:

1. Native build support for each proposed architecture.
2. Pinned, auditable tool versions or commit SHAs.
3. Compatibility with the project's Python/GTK/GI packaging model.
4. Explicit dependency collection and AppDir inspection.
5. Reproducibility, licensing and provenance of the packaging tools.
6. Availability of CI runners and ability to execute architecture-native smoke tests.

Do not select a tool solely because it can produce an AppImage from a simple GTK example. A small throwaway packaging spike should establish whether Anura's GI, GStreamer, Tesseract and portal integration can be represented correctly before the toolchain is adopted.

## 5. Architecture-specific build design

Use one isolated build job per supported architecture. Each job must:

- run on a native runner where available, or clearly identify and validate any emulation;
- build dependencies for the target architecture rather than copying host binaries;
- generate a complete AppDir from a clean workspace;
- inspect ELF architecture and dynamic dependencies;
- validate typelib, GTK, GStreamer, GSettings, GResource, translation and icon paths;
- reject accidental references to the runner's source tree, home directory or build prefix;
- produce a uniquely named artifact containing the architecture and version;
- publish diagnostic metadata and checksums.

A candidate matrix is `x86_64` and `aarch64`; this is not a support commitment. If a native runner or reliable test environment is unavailable for an architecture, defer that architecture rather than publishing an unverified image.

## 6. zsync and update-manager contract

**Maintainer decision:** use GitHub Releases as the sole initial publication and update-discovery infrastructure. Prefer the AppImage GitHub Releases update transport `gh-releases-zsync` over a manually constructed direct `zsync|URL` endpoint. This keeps update discovery tied to the project's own GitHub Releases and avoids introducing a separate hosting service.

Use architecture-specific, versioned asset names with a stable filename pattern, for example:

- `Anura-<version>-x86_64.AppImage` and `Anura-<version>-x86_64.AppImage.zsync`;
- `Anura-<version>-aarch64.AppImage` and `Anura-<version>-aarch64.AppImage.zsync`.

Embed an architecture-specific update-information value in each image, following the AppImage GitHub Releases transport contract:

```text
gh-releases-zsync|D3M-Sudo|Anura|latest|Anura-*-x86_64.AppImage.zsync
gh-releases-zsync|D3M-Sudo|Anura|latest|Anura-*-aarch64.AppImage.zsync
```

The `latest` selector follows the latest stable GitHub Release (not a prerelease). Keep the filename patterns distinct by architecture and ensure each release contains exactly one matching AppImage and one matching `.zsync` asset per supported architecture. The AppImageSpec defines this transport and its filename-pattern contract; verify compatibility with the actual updater/client versions selected for Anura.

Generate each `.zsync` file from its final AppImage and publish both assets in the same GitHub Release. Do not embed a direct URL to a version-specific release asset: the embedded update information must remain valid across releases.

Validation must establish that:

- the embedded update information is correct for the image's architecture and project repository;
- the updater resolves the latest stable release and selects only the matching architecture asset;
- the `.zsync` metadata describes the exact published AppImage and its download URL;
- no x86_64 update can be offered to an aarch64 installation, or vice versa;
- a client can update from a previous release using block reuse;
- prereleases do not unexpectedly become the stable update target;
- an interrupted, unavailable or incompatible differential update has a documented safe fallback.

Gear Lever compatibility must be tested with a real supported version. Record the Gear Lever and updater versions, update flow, selected release assets and observed result. A successful GitHub asset upload or the mere presence of a `.zsync` file is not sufficient evidence of a working update path.

Official format reference: [AppImage specification — update information](https://github.com/AppImage/AppImageSpec/blob/master/draft.md#update-information).

## 7. Release workflow and publication gate

The AppImage jobs should be integrated into the existing tag-triggered release workflow only after the packaging spike and per-architecture checks pass. Pull-request CI may build and validate artifacts, but must not publish release assets.

The publication job should depend on all required architecture builds and artifact validations. It must reject a partial release when a required AppImage, matching zsync file, checksum or metadata is missing. Flatpak and AppImage assets should be clearly distinguished by format and architecture.

Keep the existing Flatpak publication gate intact. Publish a single release only after all required assets are present and validated; do not let parallel jobs race while attaching files to the same GitHub Release.

## 8. Acceptance and evidence

For every architecture claimed as supported, retain CI evidence for:

- native build (or explicitly documented emulation);
- AppImage ELF architecture and dynamic dependency inspection;
- clean-host or representative-host launch;
- GTK startup and essential UI flow;
- GI typelib and native binding loading;
- OCR with a known image and expected output;
- Tesseract model lookup/download behaviour;
- portal capture hand-off in a supported desktop session;
- desktop integration metadata;
- checksum verification;
- zsync metadata consistency and a real update from the previous release.

The release-level test must inspect the actual published GitHub Release assets, not only workflow artifacts. Record the AppImage and zsync filenames, architecture, sizes, checksums and update-test result.

## 9. Original proposed sequence and decision gates (superseded by implementation)

1. **Runtime inventory:** document bundled versus host-provided dependencies and identify unresolved packaging constraints.
2. **Toolchain spike:** build a minimal Anura AppDir on x86_64; do not yet publish it.
3. **Runtime validation:** prove GTK/GI, GStreamer, Tesseract, resources and portal integration on a clean representative host.
4. **ARM64 feasibility:** repeat the packaging and runtime checks independently on aarch64.
5. **Update prototype:** embed update metadata, generate zsync and test Gear Lever against two versioned test artifacts.
6. **Release integration:** add tag-only publication after both architecture gates and update validation are repeatable.
7. **Documentation and release evidence:** publish installation/update instructions and validate the actual release assets.

At each gate, report blockers and measured results before proceeding. Decisions still required include the final toolchain, exact host-library boundary, supported desktop/session matrix, architecture support commitment and Gear Lever/updater versions. The update-discovery transport is set to GitHub Releases using `gh-releases-zsync`.

## 10. Explicit non-goals

- Replacing or changing the existing Flatpak distribution path.
- Treating a single AppImage as multi-architecture.
- Bundling or replacing host portal services.
- Claiming compatibility with every Linux distribution or desktop session.
- Publishing AppImages before native build, clean-host and update tests pass.
- Changing application runtime dependencies as part of this planning document.


## 11. Implementation status (PR #643, merged)

The current branch implements native builds on `ubuntu-24.04` and `ubuntu-24.04-arm`, stages the dependency-complete AppDir with the pinned appimage-builder recipe, replaces the generated AppRun2 with the project's shell entrypoint, and repackages the extracted filesystem using the pinned AppImageKit appimagetool and architecture-specific type2-runtime. The intermediate AppRun2 launcher is not shipped. Each build generates the `.zsync` control file from the final repackaged AppImage using `zsyncmake`, with a relative URL to the sibling release asset and exact-file reconstruction enabled. Each build checks the resulting ELF architecture, custom AppRun, embedded GitHub Releases update metadata and matching zsync file; CI then runs a headless smoke test in a clean Ubuntu 24.04 container.

The implementation has been merged. CI validation is performed by the current workflow; clean-host runtime review remains outstanding. The AppImage uses the host glibc rather than AppRun2's compatibility layer, so Ubuntu 24.04 is the current build baseline and the minimum supported glibc must be documented from the actual binary/runtime dependency audit. A real Gear Lever update from an earlier published AppImage and desktop-session integration checks remain release acceptance gates.
