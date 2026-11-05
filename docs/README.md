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

## Active planning

Only plans with unfinished, currently relevant scope belong here. Completed plans are archived under `audit/legacy/reports/`.

| Document | Status | Purpose |
| --- | --- | --- |

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
| [../data/io.github.d3msudo.anura.metainfo.xml.in](../data/io.github.d3msudo.anura.metainfo.xml.in) | Flathub user-facing description and release notes |

## Structure

```text
docs/
├── README.md              ← this index
├── reference/             ← current (normative) references
│   ├── history-v1.md
│   ├── history-v2.md
│   ├── dependencies.md
│   └── tessdata-integrity.md
├── planning/              ← planning records (including historical snapshots)
│   └── flathub-readiness-m2.md
└── audit/                 ← QA/security audit material
    ├── README.md          ← audit root guide (root = active audits)
    └── legacy/            ← historical archive (append-only, see legacy/README.md)
        └── reports/       Human-readable reports (bug hunts, diagnoses,
                           superseded plans) + bugs-observed.json / bugs-summary.md
                           (per-report index in reports/README.md)
```

## Conventions

- Filenames use `kebab-case-lowercase.md`.
- Current/normative feature references live under `reference/`.
- Active (not yet implemented) plans belong in `planning/`, recreated when
  needed; once implemented they move to `audit/legacy/reports/` and are marked
  historical.
- Historical audit material belongs in `audit/legacy/` (append-only: add dated
  reports, never rewrite or delete).
- Resolved/closed audit reports are archived into `audit/legacy/reports/`;
  `audit/` root is reserved for *active* (unresolved) audits — see
  `audit/README.md`.
- Agent tooling rules (`CLAUDE.md` is a thin pointer to `AGENTS.md`) are NOT
  documentation and are not indexed here.
