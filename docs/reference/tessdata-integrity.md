# Tessdata Model Integrity (Security Reference)

Status: **Current / normative** (defensive audit remediation F1–F2)

This document describes how Anura guarantees the integrity of Tesseract
language models (`*.traineddata`) downloaded from the upstream
`tessdata_fast` repository at runtime.

## Threat model

Language models are downloaded over HTTPS from `raw.githubusercontent.com`
(pinned to a release tag in `anura/config.py`). HTTPS alone is not a
complete integrity guarantee because it protects the transport, not the
content: compromised CDN nodes, upstream repository tampering, or a
malicious repin of the tag would all deliver arbitrary bytes that the app
would happily install into `~/.local/share/anura/tessdata` and later feed
to Tesseract.

## Integrity pipeline

1. **Manifest (build-time).** `build-aux/generate_tessdata_checksums.py`
   queries the GitHub API for the pinned `tessdata_fast` tree and records
   the **git-blob SHA-1** of every supported `*.traineddata` file into
   `anura/data/tessdata_checksums.json`. Git-blob hashes are content
   addresses (SHA-1 over `blob <len>\0<data>`), so they are computed from
   repository metadata alone — the ~1–2 GB of models never need to be
   downloaded at release time.

2. **Verification (runtime).** Before any downloaded model is installed,
   `anura/utils/tessdata_integrity.py`:
   - computes the local file's git-blob hash (streaming, chunked, no
     full-file memory load);
   - looks up the expected hash in the manifest **fail-closed**: an
     unknown language, missing manifest, or malformed entry aborts the
     install — never a best-effort pass;
   - only on an exact match does the install proceed.

3. **Atomic install (F2).** The download is written to a `*.tmp` sibling
   and promoted with `os.replace()`, so a crash mid-install can never
   leave a truncated model in place of a good one.

4. **Anti-drift (release-time).** `build-aux/check_tessdata_consistency.py`
   additionally verifies that the manifest's pinned repository/tag matches
   `anura/config.py` and both Flatpak manifests, so the integrity
   guarantee cannot silently rot when the tessdata reference is repinned.

## Failure behaviour

All verification failures are fail-closed: the model is discarded, the
temp file removed, and the download reported as failed to the UI. There is
no "install anyway" path.

## Operational notes

- Adding a new tessdata tag: update the pin in `anura/config.py`, run
  `build-aux/generate_tessdata_checksums.py` to regenerate the manifest,
  then run `build-aux/check_tessdata_consistency.py` (both manifests and
  config must agree).
- Tests: `tests/test_tessdata_checksums.py` (manifest/lookup/fail-closed
  semantics, headless) and `tests/test_tessdata_consistency.py`
  (anti-drift checker, headless).
