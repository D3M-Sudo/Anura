# Anura Roadmap

This roadmap describes the current direction and approved priorities for Anura, a privacy-focused OCR and text extraction application for the Linux desktop.

It communicates project priorities and areas of exploration. It is not a delivery schedule, a release commitment, or a guarantee that every proposed activity will be implemented.

## Near-term priorities

These priorities focus on consolidating the current application and its distribution.

### 1. Reliability and desktop integration

Improve and verify Anura's integration with Linux desktop environments.

- Validate filesystem access restrictions and XDG portal permissions in representative desktop environments.
- Investigate and verify runtime behaviour where CI cannot fully reproduce a real desktop session.

Related issue: #490.

### 2. Flatpak distribution

Consolidate the existing multi-architecture Flatpak distribution.

- Maintain independent native builds and validation for x86_64 and aarch64.
- Keep release manifests consistent with the local source-of-truth manifest.
- Complete the remaining Flathub submission and review activities.
- Clearly distinguish GitHub Release artifacts from Flathub distribution status.

Related issue: #494.

### 3. Release reliability

Strengthen the release process and its verification.

- Verify architecture-specific release artifacts.
- Validate SHA-256 checksums and published release assets.
- Exercise the complete tag-triggered publication workflow during a real release.

Related issue: #592.

## Longer-term direction

These activities represent planned technical directions. Their implementation remains subject to feasibility, validation and maintainer approval.

### 4. AppImage multi-architecture distribution

Evaluate and develop an AppImage distribution strategy for x86_64 and aarch64.

Areas of work include:

- Dependency bundling and runtime compatibility.
- Independent architecture-specific builds.
- Update distribution using zsync.
- Compatibility with supported AppImage update managers.
- Validation on representative Linux environments.

The packaging and update strategy must be validated before support is declared.

Related issue: #555.

### 5. Mathematical OCR research

Explore possible improvements to mathematical expression recognition.

The planned approach is staged:

1. Evaluate candidate technologies, provenance and licensing.
2. Conduct an isolated proof of concept.
3. Assess recognition quality, performance, dependencies and integration feasibility.
4. Decide separately whether any technology should be integrated into Anura.

No specific mathematical OCR engine or additional runtime dependency is approved by this roadmap.

Related issue: #570.

## Recently completed

- Completed the desktop menu/category review and removed the duplicate main-category declaration (#620).
- Migrated tessdata integrity verification to SHA-256 and documented the associated manifest maintenance workflow (#577, #634).
- Established native multi-architecture Flatpak build and artifact-validation coverage (#494; distribution follow-ups remain tracked separately).
- Completed static verification of the Flatpak `GI_TYPELIB_PATH` configuration for the GNOME 51 runtime: manifest entries, documentation and hygiene tests are consistent; `build-aux/flatpak_runtime_smoke.py` covers all required namespaces and native bindings on both x86_64 and aarch64 (#623). Runtime verification inside the sandbox follows the manual verification plan in the issue.

## Exploratory ideas

Additional technologies and features may be investigated as the project evolves.

Exploratory proposals are not approved implementation commitments. They must undergo technical, licensing, security and feasibility review before becoming roadmap priorities.

## Roadmap maintenance

This roadmap is reviewed after every project release.

During each review, maintainers should:

- Reassess the priority and relevance of ongoing activities.
- Move completed work into the completed section.
- Update references to issues and technical planning documents.
- Introduce new priorities only after explicit maintainer approval.
- Remove or revise outdated proposals.

Detailed implementation plans, technical evaluations, dependencies and acceptance criteria remain in `docs/planning/` and the relevant issue trackers.

The roadmap intentionally avoids fixed delivery dates and version-specific promises. Priorities may change as technical findings and project requirements evolve.
