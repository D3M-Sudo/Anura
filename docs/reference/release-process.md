# Release process and release-notes standard

**Status:** Current / normative  
**Applies to:** Maintainers preparing tagged GitHub Releases from the protected release branch  
**Canonical content source:** `CHANGELOG.md`  
**Automation:** `.github/workflows/main.yml`

This document defines the release-note format and the operational sequence for preparing, publishing and verifying an Anura release. The GitHub Release body is generated from the version section in `CHANGELOG.md`; it must not become a separately maintained copy.

## 1. Sources of truth

Keep these responsibilities separate:

| Source | Responsibility |
| --- | --- |
| `CHANGELOG.md` | Human-reviewed release content and canonical release date |
| `build-aux/release.sh` | Version bump, manifest generation, AppStream metadata, local commit and annotated tag |
| `build-aux/generate_release_notes.py` | Converts the selected changelog section into GitHub Markdown and AppStream release notes |
| `.github/workflows/main.yml` | Tag-triggered builds, artifact validation, checksums and GitHub Release publication |
| This document | Maintainer procedure and editorial standard |
| `.github/release_template.md` | Reusable fallback when drafting a Release manually in the GitHub UI |

Do not write a second, independently maintained set of release notes in the GitHub UI. The publication workflow supplies `release-notes.md` through `body_path`, so the generated body is authoritative and supersedes any UI draft text.

## 2. Version and changelog preparation

1. Select the next project version using the repository's existing versioning policy. The release tooling accepts `X.Y.Z` and `X.Y.Z.W`.
2. Review all changes since the previous release tag. Include user-visible features, fixes, behaviour changes, security changes and material maintenance changes. Do not treat the PR title list as a substitute for reviewing the actual changes.
3. Update the `Unreleased` section in `CHANGELOG.md` as work is merged. Before cutting a release, move the intended entries into a dated version section:
   
   ```markdown
   ## [X.Y.Z] - YYYY-MM-DD

   ### Added
   - ...

   ### Changed
   - ...

   ### Fixed
   - ...
   ```

4. Keep the release date in the heading as the canonical date. The generated GitHub Release heading takes this date from `CHANGELOG.md`, not from the time zone or clock of the GitHub Actions runner.
5. Keep `[Unreleased]` for changes that are not part of this tag. Do not include unreleased entries in the versioned section.
6. Use only relevant category headings, in the same order used by the changelog. The standard Keep a Changelog categories are `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed` and `Security`. An empty category should be omitted.
7. Preserve issue/PR references where they help readers trace a change. Use backticks for identifiers, commands, paths and configuration keys. Explain the effect of a change rather than listing an unexplained internal commit message.
8. Avoid duplicate bullets, vague entries such as “various fixes”, temporary audit jargon and implementation details that do not help users or maintainers understand the release. Retain technical detail when it explains compatibility, security, reliability, migration or operational impact.
9. Review spelling, grammar, Markdown rendering and links. Keep the prose concise but sufficiently specific to distinguish the change from other entries.

The release generator copies the selected version section into the GitHub Release body. It does not invent a summary, reorder categories or silently curate the entries. Editorial quality must therefore be established in `CHANGELOG.md` before tagging.

## 3. Prepare the release commit and tag

The release script defaults to `main` as its release branch. This is intentional: normal promotion into the release branch must happen through the repository's protected-branch workflow. Do not bypass that promotion process by using `RELEASE_BRANCH` as a shortcut.

From a clean checkout of the approved release branch:

```bash
./build-aux/release.sh X.Y.Z
```

An optional second argument overrides the default tessdata reference:

```bash
./build-aux/release.sh X.Y.Z 4.1.0
```

The script refuses a dirty working tree, an existing `vX.Y.Z` tag or an unexpected branch. It updates the project version in the relevant metadata, pins the tessdata reference, regenerates the release Flatpak manifest, validates the manifests and creates a release commit plus an annotated `vX.Y.Z` tag.

Before pushing:

- [ ] Confirm the changelog section exists, is dated correctly and contains the complete approved notes.
- [ ] Confirm the script's version changes and generated manifest are correct.
- [ ] Inspect the release commit with `git show HEAD`.
- [ ] Confirm the annotated tag points to the intended release commit.
- [ ] Confirm the required branch CI is green and no unresolved release blocker remains.

Then push the branch and tag. With the default branch setting:

```bash
git push origin main --tags
```

If an explicitly approved release process uses a different branch, set `RELEASE_BRANCH` when running the script and push that same branch. Do not change the default casually.

## 4. Automated GitHub Release publication

Pushing a `v*` tag triggers `.github/workflows/main.yml`. Merging a PR alone does not publish a release.

The workflow builds and validates the release assets for both supported architectures. The publication job runs only after the Flatpak and AppImage build matrices and their artifact-validation jobs succeed. It generates the GitHub Release body with:

```bash
python3 build-aux/generate_release_notes.py --markdown CHANGELOG.md X.Y.Z
```

The action publishes the generated body and attaches the validated assets. The expected asset set is:

| Asset | Purpose |
| --- | --- |
| `io.github.d3m_sudo.anura-x86_64.flatpak` | x86_64 Flatpak bundle |
| `io.github.d3m_sudo.anura-aarch64.flatpak` | aarch64 Flatpak bundle |
| `SHA256SUMS` | SHA-256 inventory for the Flatpak bundles |
| `Anura-X.Y.Z-x86_64.AppImage` | x86_64 AppImage |
| `Anura-X.Y.Z-x86_64.AppImage.zsync` | x86_64 incremental-update control file |
| `Anura-X.Y.Z-aarch64.AppImage` | aarch64 AppImage |
| `Anura-X.Y.Z-aarch64.AppImage.zsync` | aarch64 incremental-update control file |
| `SHA256SUMS-appimage` | SHA-256 inventory for the AppImage and zsync assets |

The exact filenames are validated by the artifact-validation scripts. Do not rename assets manually or upload CI debug artifacts to the public release.

## 5. Post-publication verification

A green tag workflow is necessary but not sufficient. Open the actual GitHub Release and verify:

- [ ] Release title, tag and target commit are correct.
- [ ] The body is non-empty and matches the corresponding version section in `CHANGELOG.md`, including its date and headings.
- [ ] Both Flatpak bundles are present exactly once and are non-empty.
- [ ] `SHA256SUMS` is present and verifies the downloaded Flatpak bundles.
- [ ] Both architecture-specific AppImages and both matching `.zsync` files are present exactly once.
- [ ] `SHA256SUMS-appimage` is present and verifies the downloaded AppImage and zsync assets.
- [ ] No temporary, debug, duplicate or wrong-architecture artifact is attached.
- [ ] The AppImage update metadata and first-release acceptance checks are handled as described in [AppImage multi-architecture builds and updates](appimage-multiarch-release.md).
- [ ] The results are consistent with [tagged release verification](tagged-release-verification.md).

Keep the first real tag-triggered publication and the first end-to-end Gear Lever update as explicit acceptance gates. CI artifact validation does not prove that a real desktop update has succeeded.

## 6. Corrections and failure handling

- If the notes are wrong, fix the version section in `CHANGELOG.md`; do not patch the generated body as an independent source.
- If a tag workflow fails, retain the run and logs, identify the failing build/validation/publication stage, and correct the cause through the normal reviewed branch/PR process.
- Re-running a tag workflow or replacing an already published asset is a release operation. Verify the intended tag and commit and obtain maintainer approval before doing so.
- Do not describe a release as complete until the actual GitHub Release page and its downloadable assets have passed verification.

## 7. Manual GitHub Release template

The repository includes `.github/release_template.md` as a reusable fallback for a manually drafted Release. Keep it aligned with the generated body structure. The automated workflow uses `body_path` and generates its own body from `CHANGELOG.md`; editing the UI template does not override that automation.
