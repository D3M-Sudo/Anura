# Tagged release verification checklist

**Status:** operational checklist; first real tag-triggered publication still requires end-to-end evidence  
**Related issues:** [#592](https://github.com/D3M-Sudo/Anura/issues/592), [#555](https://github.com/D3M-Sudo/Anura/issues/555)  
**Workflow:** `.github/workflows/main.yml`  
**Normative process:** [release-process.md](release-process.md)

## 1. Purpose and evidence boundary

Pull-request CI verifies release builds, artifact hand-off and checksum generation, but the publication job runs only for `v*` tags. A green PR run does not prove that GitHub Release assets were uploaded successfully.

Issue #592's reviewed `actions/download-artifact` pin is:

```yaml
uses: actions/download-artifact@37930b1c2abaa49bbe596cd826c3c89aef350131 # v7.0.0
```

Keep third-party actions pinned to full 40-character commit SHAs with readable version comments.

## 2. Pre-release checks

Before creating or pushing a release tag:

- [ ] Confirm the approved release commit contains the complete, reviewed version section in `CHANGELOG.md`.
- [ ] Confirm the version heading uses `## [X.Y.Z] - YYYY-MM-DD`; this date is canonical for GitHub and AppStream release notes.
- [ ] Confirm `.github/workflows/main.yml` still triggers on `v*` tags.
- [ ] Confirm every third-party `uses:` reference is pinned to a full commit SHA and has a readable version comment.
- [ ] Confirm the architecture matrices use native `x86_64` and `aarch64` runners.
- [ ] Confirm Flatpak validation requires exactly the expected two bundles and generates `SHA256SUMS`.
- [ ] Confirm AppImage validation requires both architecture-specific AppImage/`.zsync` pairs and generates `SHA256SUMS-appimage`.
- [ ] Confirm the tag-only publication job depends on both build matrices and both artifact-validation jobs.
- [ ] Confirm the publication job has only the permissions needed to read artifacts and publish release contents.

Follow [release-process.md](release-process.md) for changelog editorial rules, release-script invocation and tag preparation.

## 3. Tag-triggered workflow checks

Inspect the workflow run associated with the exact tag and commit:

- [ ] The run ref is the expected `refs/tags/vX.Y.Z`.
- [ ] Python quality and all required test jobs complete successfully.
- [ ] Native `x86_64` and `aarch64` Flatpak builds complete successfully.
- [ ] Native `x86_64` and `aarch64` AppImage builds complete successfully.
- [ ] The two artifact-validation jobs download artifacts from the same workflow run.
- [ ] Flatpak validation accepts exactly the expected bundles and rejects missing, unexpected, empty or unsafe entries.
- [ ] AppImage validation accepts exactly the expected versioned AppImage/`.zsync` pairs and rejects missing, unexpected, empty or unsafe entries.
- [ ] `SHA256SUMS` and `SHA256SUMS-appimage` are generated from their respective validated asset sets.
- [ ] The tag-only publication job starts only after all required jobs succeed.
- [ ] The generated release body is non-empty and uses the date and entries from the matching `CHANGELOG.md` version section.
- [ ] The publication job uploads all validated assets without an API or asset-upload error.

Expected published assets:

| Asset | Expected purpose |
| --- | --- |
| `io.github.d3m_sudo.anura-x86_64.flatpak` | x86_64 Flatpak bundle |
| `io.github.d3m_sudo.anura-aarch64.flatpak` | aarch64 Flatpak bundle |
| `SHA256SUMS` | SHA-256 inventory for Flatpak bundles |
| `Anura-X.Y.Z-x86_64.AppImage` | x86_64 AppImage |
| `Anura-X.Y.Z-x86_64.AppImage.zsync` | x86_64 update control file |
| `Anura-X.Y.Z-aarch64.AppImage` | aarch64 AppImage |
| `Anura-X.Y.Z-aarch64.AppImage.zsync` | aarch64 update control file |
| `SHA256SUMS-appimage` | SHA-256 inventory for AppImage and zsync files |

Workflow artifact names may include run IDs and architecture suffixes. The table describes the filenames expected inside the public GitHub Release.

## 4. Verify the actual GitHub Release

Do not close #592 or #555 based only on a green workflow run. Inspect the actual release page/API:

- [ ] Release title, tag and target commit are correct.
- [ ] Release body is non-empty and matches the corresponding version section in `CHANGELOG.md`, including canonical date, headings and bullets.
- [ ] Both Flatpak assets are present exactly once and are non-empty.
- [ ] `SHA256SUMS` is present and verifies the downloaded Flatpak bundles.
- [ ] Both AppImage assets and both matching `.zsync` files are present exactly once.
- [ ] `SHA256SUMS-appimage` is present and verifies the downloaded AppImage and zsync files.
- [ ] No temporary/debug artifact, duplicate or wrong-architecture bundle was published.
- [ ] AppImage embedded update metadata is correct and a real Gear Lever differential update is tested from a previous public version before advertising that path as validated.
- [ ] Desktop integration acceptance checks are recorded separately from CI smoke-test evidence.

Record the release URL, tag, commit SHA, workflow run URL, asset filenames/sizes and checksum verification results in the relevant issue.

## 5. Failure handling

If a required build, validation or publication step fails:

1. Do not treat the release as complete.
2. Preserve the failed workflow run and relevant job logs.
3. Identify whether the failure is in architecture build, artifact transfer, exact-set validation, checksum generation or GitHub Release upload.
4. Correct the cause through the normal reviewed branch/PR process.
5. Re-run the appropriate checks and repeat tag-triggered publication verification under maintainer control.

Do not silently replace or delete release assets to make a partial release appear complete. Moving a tag, replacing a release or re-publishing assets requires explicit maintainer approval and a documented reason.

## 6. Completion rule

Close the release-publication acceptance issues only when a real tag-triggered release demonstrates the complete hand-off: both Flatpak bundles, both AppImage/`.zsync` pairs, both checksum inventories, correct release metadata and verified downloads. Keep desktop integration and real updater acceptance gates open until separately demonstrated.
