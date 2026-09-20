# Anura — Documentation Index

This directory contains permanent project documentation. Repository-level
documentation lives in the root (`README.md`, `AGENTS.md`, `CONTRIBUTING.md`,
`SECURITY.md`, `CHANGELOG.md`).

## Current documentation (normative)

| Document | Status | Purpose |
| --- | --- | --- |
| [reference/history-v1.md](reference/history-v1.md) | **Current / normative** | Extraction History V1: behaviour, storage, settings, UI, limits |
| [reference/dependencies.md](reference/dependencies.md) | **Current / normative** | Python/Flatpak dependency workflow: uv.lock, sync, FEDC/certifi ownership, headless GTK testing |
| [reference/tessdata-integrity.md](reference/tessdata-integrity.md) | **Current / normative** | Tessdata model integrity: checksum manifest, fail-closed verification, atomic install, anti-drift |

## Active planning

| Document | Status | Purpose |
| --- | --- | --- |
| [planning/history-v2-interactive-rows.md](planning/history-v2-interactive-rows.md) | **Active — not yet implemented** | History V2: interactive history rows (copy, external editor, optional re-OCR/TTS) |

## Historical material (audit/legacy)

| Document | Status | Purpose |
| --- | --- | --- |
| [audit/legacy/reports/history-v1-plan.md](audit/legacy/reports/history-v1-plan.md) | **Historical** | Pre-implementation History V1 plan (baseline `testing @ a52f4563`); superseded by the merged History V1 integration |
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
│   ├── dependencies.md
│   └── tessdata-integrity.md
├── planning/              ← active (not yet implemented) plans
│   └── history-v2-interactive-rows.md
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
