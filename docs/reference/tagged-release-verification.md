# Tagged release verification checklist

**Status:** operational checklist; the first real tag-triggered publication is still pending  
**Related issue:** [#592](https://github.com/D3M-Sudo/Anura/issues/592)  
**Workflow:** `.github/workflows/main.yml`  
**Scope:** verify the existing pinned-action and multi-architecture artifact hand-off; this document does not create tags or publish releases.

## 1. Purpose and evidence boundary

Pull-request CI verifies the release-artifact hand-off and checksum generation, but the publication job is intentionally skipped unless the workflow ref is a `v*` tag. A green PR run therefore does not prove that GitHub Release assets were uploaded successfully.

Issue #592's action-pinning requirement is implemented on `feature`:

```yaml
uses: actions/download-artifact@37930b1c2abaa49bbe596cd826c3c89aef350131 # v7.0.0
```

The SHA must remain a full 40-character commit reference with a version comment. Do not replace it with a moving major-version tag.

## 2. Pre-release checks

Before a maintainer creates or pushes a release tag:

- [ ] Confirm the intended release commit contains the approved changes and release notes in `CHANGELOG.md`.
- [ ] Confirm `.github/workflows/main.yml` still triggers on `v*` tags.
- [ ] Confirm every third-party `uses:` reference is pinned to a full commit SHA and has a readable version comment.
- [ ] Confirm the `actions/download-artifact` pin is still the reviewed v7.0.0 commit above, or review and document any deliberate upgrade.
- [ ] Confirm the architecture matrix declares the expected native runners for `x86_64` and `aarch64`.
- [ ] Confirm the artifact validation job requires exactly the expected two Flatpak bundle files and generates `SHA256SUMS`.
- [ ] Confirm the tag-only publication job depends on both the architecture build matrix and artifact validation.
- [ ] Confirm the workflow has the minimum permissions needed to read artifacts and publish release contents.

A pull-request run can validate the build and artifact hand-off, but cannot replace the tag-triggered publication check below.

## 3. Tag-triggered workflow checks

After the maintainer creates/pushes the approved version tag, inspect the workflow run associated with that exact tag and commit.

- [ ] The run's ref is the expected `refs/tags/vX.Y.Z`.
- [ ] Python quality and all required test jobs complete successfully.
- [ ] The native `x86_64` Flatpak build completes successfully.
- [ ] The native `aarch64` Flatpak build completes successfully.
- [ ] The artifact validation job downloads artifacts from the same workflow run.
- [ ] Validation accepts exactly the expected architecture-specific bundles and rejects missing, unexpected, empty or unsafe entries.
- [ ] `SHA256SUMS` is generated from the validated release bundle set.
- [ ] The tag-only publication job starts only after all required jobs succeed.
- [ ] The publication job uploads both bundles and the checksum file without an API or asset-upload error.

Expected published assets:

| Asset | Expected purpose |
| --- | --- |
| `io.github.d3m_sudo.anura-x86_64.flatpak` | x86_64 Flatpak bundle |
| `io.github.d3m_sudo.anura-aarch64.flatpak` | aarch64 Flatpak bundle |
| `SHA256SUMS` | Checksums for the published bundles |

The workflow artifact names may include the run ID and architecture; the table above describes the filenames expected inside the release, not the temporary CI artifact names.

## 4. Verify the actual GitHub Release

Do not close #592 based only on a green workflow run. Inspect the release page/API after publication and verify:

- [ ] The release tag and target commit match the workflow run.
- [ ] Both expected Flatpak assets are present exactly once.
- [ ] `SHA256SUMS` is present exactly once.
- [ ] Asset sizes are non-zero and downloads complete.
- [ ] The checksum file contains the expected filenames and valid SHA-256 values.
- [ ] Downloaded assets pass checksum verification.
- [ ] Release notes are non-empty and correspond to the version's changelog section.
- [ ] No temporary/debug artifact or wrong-architecture bundle was published.

Record the release URL, tag, commit SHA, workflow run URL, asset filenames/sizes and checksum verification result in the issue.

## 5. Failure handling

If a required build, validation or publication step fails:

1. Do not treat the release as complete.
2. Preserve the failed workflow run and relevant job logs as evidence.
3. Determine whether the failure is in architecture build, artifact transfer, exact-set validation, checksum generation or GitHub Release upload.
4. Correct the cause through the normal reviewed branch/PR workflow.
5. Re-run the appropriate checks and repeat the tag-triggered publication verification under maintainer control.

Do not silently replace or delete release assets to make a partial release appear complete. Any tag movement, release replacement or re-publication must follow the repository's release policy and be explicitly approved by the maintainer.

## 6. Completion rule for issue #592

Issue #592 can be closed only after one real tag-triggered release demonstrates the complete hand-off:

- pinned action is used by the release workflow;
- both architecture bundles are validated and published;
- `SHA256SUMS` is published and verifies the downloaded assets;
- the release page contains the expected assets and correct version metadata.

Until that evidence exists, keep the issue open and report the PR/branch CI result separately from the real release result.
