# Anura — Documentation Index

This directory contains permanent project documentation. Repository-level
documentation lives in the root (`README.md`, `AGENTS.md`, `CONTRIBUTING.md`,
`SECURITY.md`, `CHANGELOG.md`).

## Current documentation (normative)

| Document | Status | Purpose |
| --- | --- | --- |
| [reference/history-v1.md](reference/history-v1.md) | **Current / normative** | Extraction History V1: behaviour, storage, settings, UI, limits |
| [reference/history-v2.md](reference/history-v2.md) | **Current / normative** | History V2 minimal cut: expandable rows, copy action, lifecycle, tests |
| [reference/dependencies.md](reference/dependencies.md) | **Current / normative** | Python/Flatpak dependency workflow: uv.lock, sync, FEDC/certifi ownership, headless GTK testing |
| [reference/tessdata-integrity.md](reference/tessdata-integrity.md) | **Current / normative** | Tessdata model integrity: checksum manifest, fail-closed verification, atomic install, anti-drift |
| [reference/flatpak-multiarch-release.md](reference/flatpak-multiarch-release.md) | **Current / normative** | GNOME 51 Flatpak manifests, native x86_64/aarch64 CI, runtime checks, release artifacts and SHA-256 verification |
| [reference/appimage-multiarch-release.md](reference/appimage-multiarch-release.md) | **Current / normative** | Self-contained native x86_64/aarch64 AppImages, bundled GTK/GI/OCR runtime, zsync metadata, CI validation and host integration boundaries |
| [reference/flathub-submission-checklist.md](reference/flathub-submission-checklist.md) | **Current / operational** | Maintainer checklist for Flathub policy, manifest, architecture, licensing, permissions, validation and manual submission (#494) |
| [reference/tagged-release-verification.md](reference/tagged-release-verification.md) | **Current / operational** | First real tag-triggered verification of pinned download-artifact, native Flatpak artifacts, SHA-256 checksums and GitHub Release publication (#592) |
| [reference/code-commenting.md](reference/code-commenting.md) | **Current / normative** | Technical comment policy and Google-style Python docstring conventions |

## Active planning

Only plans with unfinished, currently relevant scope belong here. Completed plans are archived under `audit/legacy/reports/`.

| Document | Status | Purpose |
| --- | --- | --- |
| [planning/appimage-zsync-release-plan.md](planning/appimage-zsync-release-plan.md) | **Active / planning** | AppImage implementation record and remaining first-release, Gear Lever update and desktop-integration acceptance gates (#555) |
| [planning/math-ocr-evaluation.md](planning/math-ocr-evaluation.md) | **Active / research** | Mathematical OCR engine evaluation, licensing/provenance gates, resource benchmarks and proposed LaTeX-first integration plan (#570) |

## Historical material (audit/legacy)

| Document | Status | Purpose |
| --- | --- | --- |
| [audit/legacy/reports/history-v1-plan.md](audit/legacy/reports/history-v1-plan.md) | **Historical** | Pre-implementation History V1 plan (baseline `testing @ a52f4563`); superseded by the merged History V1 integration |
| [audit/legacy/reports/history-v2-interactive-rows-plan.md](audit/legacy/reports/history-v2-interactive-rows-plan.md) | **Historical** | Completed History V2 design and implementation plan; current behaviour is in `reference/history-v2.md` |
| [audit/legacy/reports/runtime-fixes-m1-plan.md](audit/legacy/reports/runtime-fixes-m1-plan.md) | **Historical** | Completed runtime-fixes Milestone 1 plan (36/36 scoped issues resolved) |
| [planning/flathub-readiness-m2.md](planning/flathub-readiness-m2.md) | **Historical** | Original Milestone 2 sequencing; implementation status is superseded by current CI and GitHub issues |
| [audit/legacy/reports/diagnosis-vm-followup-2026-09-17.md](audit/legacy/reports/diagnosis-vm-followup-2026-09-17.md) | **Historical** | VM follow-up diagnosis (findings resolved at HEAD, re-verified by the 2026-09-20 audit) |
| [audit/legacy/reports/diagnosis-full-test-tiers-2026-09-20.md](audit/legacy/reports/diagnosis-full-test-tiers-2026-09-20.md) | **Historical** | Full diagnostics and test-tier audit (`HEAD: aba2884`) |
| [audit/legacy/reports/](audit/legacy/reports/) | **Historical** | Bug-hunt/QA/diagnosis reports, append-only (per-report index in `reports/README.md`) |

Other normative references outside `docs/`:

| Document | Purpose |
| --- | --- |
| [../flatpak/README.md](../flatpak/README.md) | Flatpak manifests: local (edit) vs release (generated) |
| [../data/io.github.d3m_sudo.anura.metainfo.xml.in](../data/io.github.d3m_sudo.anura.metainfo.xml.in) | Flathub user-facing description and release notes |

## Structure

```text
docs/
├── README.md              ← this index
├── reference/             ← current and operational references
│   ├── history-v1.md
│   ├── history-v2.md
│   ├── dependencies.md
│   ├── tessdata-integrity.md
│   ├── flatpak-multiarch-release.md
│   ├── appimage-multiarch-release.md
│   ├── flathub-submission-checklist.md
│   └── tagged-release-verification.md
├── planning/              ← active and historical planning records
│   ├── appimage-zsync-release-plan.md
│   ├── math-ocr-evaluation.md
│   └── flathub-readiness-m2.md (historical)
└── audit/                 ← QA/security audit material
    ├── README.md          ← audit root guide (root = active audits)
    └── legacy/            ← historical archive (append-only)
        ├── README.md
        └── reports/       Human-readable reports and per-report index
```

## Conventions

- Filenames use `kebab-case-lowercase.md`.
- Current/normative feature references live under `reference/`.
- Active plans with unfinished scope or post-implementation acceptance gates
  belong in `planning/`. Archive a plan only when all of its tracked work and
  acceptance criteria are complete; do not archive it merely because the main
  implementation has merged.
- Historical audit material belongs in `audit/legacy/` (append-only: add dated
  reports, never rewrite or delete).
- Resolved/closed audit reports are archived into `audit/legacy/reports/`;
  `audit/` root is reserved for *active* (unresolved) audits — see
  `audit/README.md`.
- Agent tooling rules (`CLAUDE.md` is a thin pointer to `AGENTS.md`) are NOT
  documentation and are not indexed here.
