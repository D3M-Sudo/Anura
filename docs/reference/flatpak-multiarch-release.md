# Flatpak multi-architecture builds and releases

**Status:** Current / normative  
**Applies to:** `feature` and the GitHub Actions release workflow

## Supported architectures and runtime

Anura's GitHub Release bundles are built independently for:

| Flatpak architecture | Native runner |
| --- | --- |
| `x86_64` | `ubuntu-24.04` |
| `aarch64` | `ubuntu-24.04-arm` |

Both the local manifest (`flatpak/io.github.d3m_sudo.anura.local.json`) and
the generated release manifest use `org.gnome.Platform` and
`org.gnome.Sdk` runtime version `51`. The release manifest is generated
from the local manifest; do not edit the generated manifest by hand. See
[`flatpak/README.md`](../../flatpak/README.md) for the source-of-truth rules.

## Per-architecture CI contract

The `flatpak-builder` matrix in `.github/workflows/main.yml` performs the
following work independently on each native runner:

1. Verify that the runner's `uname -m` matches the requested Flatpak
   architecture.
2. Remove stale build directories and caches before building.
3. Generate the release-style manifest and a source-pinned CI build manifest.
4. Validate the local and generated release manifests, including Flathub
   manifest lint and shared-field consistency.
5. Build the Flatpak, including an offline build.
6. Install and smoke-test the application inside the sandbox.
7. Load the required GI namespaces and exercise native runtime bindings,
   including Pillow, psutil, zxing-cpp and `libtesseract.so.5`.
8. Run positive and negative OCR checks.
9. Validate Desktop/AppStream metadata and the installed license inventory.

A successful matrix run therefore demonstrates native build and the listed
sandbox checks for both architectures. It does not replace a manual test in a
real GNOME, Cinnamon, Wayland or X11 desktop session; see issues #498 and #500
for the remaining interactive permission/functional test scope.

## Release artifact contract

The matrix produces separate bundles:

- `io.github.d3m_sudo.anura-x86_64.flatpak`
- `io.github.d3m_sudo.anura-aarch64.flatpak`

The `validate-release-artifacts` job downloads the per-architecture artifacts
from the same workflow run. It requires exactly the two expected bundle
filenames and rejects missing, unexpected, empty, non-regular or symlinked
entries. It computes SHA-256 digests and uploads `SHA256SUMS` as a separate
workflow artifact.

The `publish-release` job:

- runs only for refs matching `refs/tags/*`;
- depends on both the architecture matrix and successful artifact validation;
- downloads both bundles and the validated checksum file;
- attaches the two `.flatpak` files and `SHA256SUMS` to the GitHub Release.

Pull-request and branch CI runs exercise the artifact download, exact-set
validation and checksum generation. They intentionally skip publication.
No release is created merely by merging a pull request.

## Download and verification

Download the bundle matching the host architecture and the `SHA256SUMS` file
from the same GitHub Release. If both bundles and the checksum file are
downloaded into one directory, verify all entries with:

```bash
sha256sum -c SHA256SUMS
```

If only one architecture bundle is downloaded, verify its matching line from
the checksum file or download both bundles before running the command above.
Install the matching bundle with:

```bash
flatpak install --user ./io.github.d3m_sudo.anura-x86_64.flatpak
```

Use the `aarch64` filename on ARM64 systems.

## GitHub Releases versus Flathub

These are distinct distribution/verification paths:

- **GitHub Releases:** the repository CI builds, tests, checksums and publishes
  two architecture-specific Flatpak bundles.
- **Flathub:** Flathub builds the submission manifest according to its own
  architecture support and review process. The repository's native GitHub
  runner matrix and release bundles do not, by themselves, prove that a
  Flathub submission has passed Flathub's build pipeline.

The generated release manifest is validated and built in CI, but Flathub
submission status must be tracked separately. Do not describe GitHub Release
artifacts as a single multi-architecture bundle: each file targets one
architecture.

## Verification evidence and limits

The M3 native multi-architecture build and M5 runtime-validation changes were
merged into `feature`; M6 artifact validation was merged in commit
`7c5186da8069b0a1c402df1699a652ad1d1de6d7`. CI run #1811 passed on the PR
head and verified both architecture artifact downloads and SHA-256 generation.
The release-publication job was skipped on that pull-request event, as
intended. A future tag-triggered release is still required to exercise the
actual GitHub Release upload end to end.

The manifest runtime, native builds and CI validation satisfy the repository
campaign's GNOME 51 and GitHub artifact requirements. They do not claim that a
new version has been published or that Flathub has accepted a submission.
