# Flathub submission readiness checklist

**Status:** maintainer-operated submission checklist; no Flathub submission has been made  
**Related issue:** [#494](https://github.com/D3M-Sudo/Anura/issues/494)  
**Application ID:** `io.github.d3m_sudo.anura`  
**Repository baseline:** `feature`  
**Policy references reviewed:** 2026-11-06

## 1. Purpose and scope

This checklist prepares the maintainer for Anura's first submission to Flathub. It separates evidence produced by Anura's GitHub Actions from the independent build, policy review and acceptance process operated by Flathub.

A successful GitHub Actions Flatpak matrix is useful project evidence, but it is not a Flathub build result and does not imply that a submission has been accepted. Keep issue #494 open until the maintainer has completed the submission and the relevant Flathub review/build steps.

This document is an upstream preparation aid. It does not submit the application, create a Flathub pull request, or authorize any change to the Flathub repository.

## 2. Current repository baseline

Before preparing a submission, re-check these facts on the exact release commit:

- The editable source-of-truth manifest is `flatpak/io.github.d3m_sudo.anura.local.json`.
- The Flathub/release manifest is generated as `flatpak/io.github.d3m_sudo.anura.json`; never edit the generated manifest by hand.
- The generated manifest must be copied to the root of the Flathub submission branch and named `io.github.d3m_sudo.anura.json`.
- The app ID and manifest filename must match exactly.
- The manifest currently targets `org.gnome.Platform` / `org.gnome.Sdk` runtime 51. Confirm that this is still a supported and latest eligible runtime version at the time of submission; update the source-of-truth manifest and regenerate if Flathub's current requirements demand it.
- The source is pinned to the release tag and resolved commit. Run `build-aux/pin_source_commit.py --tag vX.Y.Z` after the tag exists, then run `build-aux/pin_source_commit.py --tag vX.Y.Z --check`.
- The project has native GitHub Actions Flatpak build and sandbox-smoke coverage for `x86_64` and `aarch64`, plus architecture-specific release bundles and SHA-256 validation. Record the exact successful run and commit; do not present this as Flathub's own build evidence.

See [Flatpak manifests and ownership](../../flatpak/README.md) and [multi-architecture builds and releases](flatpak-multiarch-release.md).

## 3. Architecture policy and manifest configuration

The Flathub requirements and maintenance documentation reviewed on 2026-11-06 state that current Flathub builders build applications for `x86_64` and `aarch64` by default. When an application supports both, a `flathub.json` architecture override is not required.

For Anura:

- [ ] Re-check the current Flathub architecture policy immediately before submission.
- [ ] Confirm that both `x86_64` and `aarch64` remain intended and supported targets.
- [ ] Review the native CI evidence for both architectures and record the exact commit/run.
- [ ] Confirm there is no stale `only-arches` or `skip-arches` restriction in the submission.
- [ ] Do not add `flathub.json` unless a documented, evidence-based exception is required.
- [ ] If either architecture is not actually supported, stop and obtain a maintainer decision before restricting the submission; removing an architecture can leave existing users stuck on an older build.

Flathub's own build results remain authoritative for the submission. A green GitHub Actions matrix cannot replace them.

## 4. Source, build and manifest checks

- [ ] Start from a clean, tagged release commit that the maintainer has approved.
- [ ] Generate the release manifest from the local source-of-truth manifest using the repository release tooling.
- [ ] Pin the source commit for the release tag and verify the pin with `pin_source_commit.py --check`.
- [ ] Confirm every module is built from source and every source is declared in the manifest with a stable, publicly accessible URL and an integrity pin where supported.
- [ ] Confirm the build does not depend on network access during the build phase; dependencies must be available as declared sources before the offline build.
- [ ] Confirm there are no local paths, untracked files, prebuilt binaries, CI artifacts, caches or machine-specific files in the submission.
- [ ] Validate JSON syntax, required manifest fields, key ordering, indentation, UTF-8 encoding and trailing newline against the current Flathub manifest style guide.
- [ ] Confirm the manifest is at the repository root and named `io.github.d3m_sudo.anura.json`.
- [ ] Check that the selected runtime and SDK are hosted by Flathub and satisfy the current runtime policy.

## 5. Metadata and desktop integration

- [ ] Validate `data/io.github.d3m_sudo.anura.metainfo.xml.in` and the generated/installed AppStream metadata with the current AppStream validator.
- [ ] Confirm the app ID, project license, metadata license, developer/project identity, summary and description are accurate.
- [ ] Confirm screenshots use reachable, version-pinned URLs and accurately depict the submitted release.
- [ ] Confirm the release metadata contains real release notes and no placeholders.
- [ ] Confirm the desktop entry is installed, uses the correct app ID and has valid categories.
- [ ] Confirm the application icon is correctly named, installed and meets current Flathub graphical-app requirements.
- [ ] Confirm the complete English user-facing localization is present and that no machine-generated or low-quality translation is included.

## 6. Dependency and licensing evidence

- [ ] Review the complete runtime dependency graph, including Python packages, native modules, GI typelibs, Tesseract/Leptonica, zxing-cpp and GStreamer components.
- [ ] Confirm all dependencies are built from source under Flathub's policy and all required sources are declared.
- [ ] Review the installed license inventory produced by CI for both architectures.
- [ ] Confirm Anura's MIT license and every distributed dependency/model notice are present and correctly attributed.
- [ ] Confirm build-only dependencies are not accidentally shipped in the runtime.
- [ ] Check that no model or other asset has unresolved provenance or redistribution terms.
- [ ] Record any exception request explicitly; do not assume that a package's upstream license label resolves the licensing of its bundled assets or training data.

## 7. Sandbox permissions and desktop behaviour

Flathub reviews static permissions separately and expects them to be minimized. Prefer XDG Portals where they cover the use case.

For every `finish-arg`:

- [ ] Map the permission to a concrete user-facing feature.
- [ ] Confirm that a suitable portal is used where required.
- [ ] Explain why any remaining static permission is necessary.
- [ ] Confirm there are no `--talk-name=org.freedesktop.portal.*` permissions.
- [ ] Reconcile the manifest with `flatpak/README.md` and `tests/test_flatpak_manifest_hygiene.py`.
- [ ] Include the permission rationale in the maintainer-authored Flathub submission description.

The four read-only XDG directory permissions still have separate local/runtime verification work tracked by #490. The GI runtime path (`GI_TYPELIB_PATH`) has been statically verified: the manifest entries, documentation and hygiene tests are consistent, and `build-aux/flatpak_runtime_smoke.py` covers all required namespaces (Gtk 4.0, Adw 1, Notify 0.7, Xdp 1.0, Gst 1.0, GtkSource 5) plus native bindings (Pillow, psutil, zxing-cpp, libtesseract) on both x86_64 and aarch64. Runtime verification inside the GNOME 51 sandbox is tracked by the manual verification plan in the issue; do not claim it complete until the smoke test evidence is recorded. Explain the remaining test boundary honestly in the submission materials if it is still relevant at submission time.

## 8. Required validation before submission

Run these checks on a representative environment and record their versions/results:

- [ ] Build and install the generated release manifest with the currently recommended Flathub Builder workflow.
- [ ] Run `flatpak-builder-lint manifest <manifest>`.
- [ ] Run `flatpak-builder-lint repo <repo>` against the built repository where applicable.
- [ ] Complete an offline build from the declared sources.
- [ ] Launch Anura in the sandbox and exercise its essential user-visible functionality.
- [ ] Verify OCR with known test images and the expected language/model setup.
- [ ] Verify screenshot capture through the supported XDG Portal path in a real desktop session.
- [ ] Verify desktop entry, icon, AppStream metadata and application ID.
- [ ] Inspect the installed runtime and license inventory.
- [ ] Preserve logs and exact commit/runtime/architecture details as review evidence.

The repository's CI already covers native x86_64/aarch64 builds, sandbox smoke checks, selected GI/native imports, OCR checks, metadata validation and license inventory. The checklist above intentionally calls out the additional Flathub-specific and interactive evidence rather than duplicating CI claims.

## 9. Generative AI policy — maintainer action required

Re-read Flathub's current Generative AI policy before submission. The policy reviewed on 2026-11-06 states, among other things, that:

- Flathub manifests must not contain AI-generated or AI-assisted content.
- Submitters must disclose AI-generated material they know or reasonably believe is included in the application or its Flathub packaging, identifying the affected parts and approximate extent.
- AI agents must not open or automate Flathub submission pull requests, or generate their commit messages, descriptions, review comments or replies.
- Submitters must not request AI-agent reviews.

The Anura maintainer must personally inspect and author/maintain the Flathub manifest and all Flathub submission interactions. Do not use this upstream checklist or an AI assistant to generate the Flathub manifest, submit the Flathub pull request, compose its description/commit message, or respond to reviewer comments. Determine whether any AI-assisted material is actually included in the submitted application or packaging and make any required disclosure through the maintainer's own submission process.

## 10. Maintainer-operated submission sequence

The submission is a manual maintainer action. The current official Flathub submission guide instructs submitters to:

1. Review the current requirements and complete the local build, install, test and lint checks.
2. Fork `flathub/flathub` with the `new-pr` branch included.
3. Create a submission branch from `new-pr`.
4. Add only the required application manifest and any required supporting submission files; do not add source code or build artifacts.
5. Push the branch to the maintainer's fork.
6. Open the submission pull request against `flathub/flathub:new-pr`, not `master`.
7. Respond personally to reviewer requests and, when asked, trigger a test build using the current Flathub procedure.
8. Install and test the Flathub-produced test build before approval/merge.
9. After acceptance, follow the Flathub app-maintenance process and keep the application/runtime maintained.

This repository task does not perform any of those actions. No Flathub fork, branch, pull request, account invitation or publication is created by this checklist.

## 11. Completion evidence for issue #494

Keep #494 open until the maintainer has recorded:

- the submission pull request URL and target branch;
- the exact application release tag and pinned source commit;
- the Flathub review outcome and any requested changes;
- successful Flathub build/test evidence for the required architectures;
- the final accepted Flathub application repository/reference;
- any architecture or permission exceptions and their rationale.

GitHub Actions multi-architecture CI and GitHub Release bundles are necessary project evidence, but do not by themselves satisfy these Flathub-specific completion criteria.

## Official references

Policy and procedures can change. Re-open these sources immediately before submission:

- [Flathub requirements](https://docs.flathub.org/docs/for-app-authors/requirements)
- [Flathub submission guide](https://docs.flathub.org/docs/for-app-authors/submission)
- [Flathub maintenance guide](https://docs.flathub.org/docs/for-app-authors/maintenance)
- [Flatpak Builder documentation](https://docs.flatpak.org/en/latest/flatpak-builder.html)
