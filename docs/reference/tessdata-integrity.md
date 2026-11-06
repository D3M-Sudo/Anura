# Tessdata Model Integrity (Security Reference)

Status: **Current / normative** (defensive audit remediation F1–F2, issue #577)

This document describes how Anura guarantees the integrity of Tesseract
language models (`*.traineddata`) downloaded at runtime from the three
upstream tessdata repositories pinned in `anura/config.py`:

| Repository | Profile | Pinned ref |
|------------|---------|------------|
| `tessdata` | standard (legacy + LSTM) | `4.1.0` |
| `tessdata_best` | highest-accuracy LSTM | `4.1.0` |
| `tessdata_fast` | fastest integerized LSTM | `4.1.0` |

## Why SHA-256 over raw content

Language models are downloaded over HTTPS from `raw.githubusercontent.com`.
HTTPS protects the transport, not the content: a compromised CDN node,
upstream repository tampering, or a malicious repin of the tag would all
deliver arbitrary bytes that the app would install and feed to Tesseract.

To bound this risk, every pinned model is identified by its **raw-content
SHA-256 digest** and byte size, recorded in
`anura/data/tessdata_checksums.json` (manifest format v2). At runtime the
downloaded bytes are hashed incrementally and compared against the pinned
digest **before** the model is installed. Any mismatch fails closed.

## Integrity pipeline

1. **Manifest generation (build-time).**
   `build-aux/generate_tessdata_checksums.py` queries the GitHub REST API
   tree of each pinned ref to enumerate every `*.traineddata` file, then
   downloads each model's *raw* bytes over streaming HTTP and computes the
   raw-content SHA-256 incrementally in bounded 64 KiB chunks. The bytes
   are hashed on the fly and discarded; no model is stored permanently.
   The actual downloaded byte count is verified against the advertised
   size (oversized and truncated streams are rejected). The result is
   written to a temporary file and atomically replaced into
   `anura/data/tessdata_checksums.json` (`os.replace`) only once every
   repository has been fully validated; on any failure the previous
   manifest is left untouched.

   The SHA-1 values published by the GitHub tree API are *git-blob*
   digests (`sha1("blob <size>\\0<data>")`), not raw-content SHA-256, and
   are never used as integrity values.

   The manifest declares its format explicitly:

   ```json
   {
     "version": 2,
     "algorithm": "sha256",
     "repositories": {
       "tessdata": {
         "url": "https://github.com/tesseract-ocr/tessdata/raw/4.1.0/",
         "tag": "4.1.0",
         "files": {
           "eng.traineddata": {
             "size": 23466654,
             "sha256": "..."
           }
         }
       }
     }
   }
   ```

2. **Verification (runtime).** Before any downloaded model is installed,
   `anura/utils/tessdata_integrity.py`:
   - loads and validates the manifest: only version 2 with `algorithm:
     "sha256"` is accepted; version 1 and any other algorithm are
     rejected (fail closed);
   - looks up the expected `TessdataChecksum` (filename, size, sha256)
     for the repository/model, rejecting malformed entries, missing
     fields, unknown languages, and legacy SHA-1 fields;
   - streams the download through `Sha256Hasher`, computing the digest
     incrementally while tracking the received byte count (no full-file
     memory load);
   - rejects oversized streams (more bytes than pinned), truncated
     downloads (fewer bytes than pinned), and any digest mismatch;
   - only on an exact size + SHA-256 match does the install proceed.

3. **Atomic install (F2).** The download is written to a `*.tmp` sibling
   inside the target quality directory, `fsync`'d, and promoted with
   `os.replace()`, so a crash mid-install can never leave a truncated
   model in place of a good one. A failed integrity verification never
   replaces an existing final model and leaves no partially downloaded
   file behind.

4. **Anti-drift (release-time).**
   `build-aux/check_tessdata_consistency.py` verifies that the committed
   manifest is format v2, uses `sha256`, lists all repositories pinned in
   `anura/config.py` with matching URLs/tags, and that every entry carries
   a valid positive size and raw SHA-256 digest (no legacy SHA-1 fields).
   A stale manifest fails the release so runtime downloads cannot silently
   start failing closed.

## Failure behaviour

All verification failures are fail-closed: the model is discarded, the
temp file removed, and the download reported as failed to the UI. There is
no "install anyway" path.

## Operational notes

- Regenerating checksums: after changing a pinned ref in
  `anura/config.py`, run
  `build-aux/generate_tessdata_checksums.py` to regenerate the manifest,
  then run `build-aux/check_tessdata_consistency.py`. The generator
  downloads every upstream model (roughly 3.9 GB across the three
  repositories at 4.1.0) and should be run in an environment with
  sufficient network, disk and time (e.g. CI), not on a constrained
  developer workstation.
- Tests: `tests/test_tessdata_checksums.py` (data model, manifest v2 /
  fail-closed semantics, headless), `tests/test_tessdata_consistency.py`
  (anti-drift checker, headless) and
  `tests/test_language_download_integrity.py` (atomic install and digest
  verification, GTK-marked). The latter also exercises the complete mocked
  download, checksum-verification and installation path for all three
  quality profiles: `fast` (`tessdata_fast/`), `standard` (`tessdata/`) and
  `best` (`tessdata_best/`). Each case asserts the selected upstream
  repository URL and confirms that the model is installed only in its
  matching quality directory. Synthetic response bodies are used, so the
  tests never fetch real upstream model files.
