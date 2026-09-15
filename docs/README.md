# Anura — Documentation Index

This directory contains permanent project documentation. Repository-level
documentation lives in the root (`README.md`, `AGENTS.md`, `CONTRIBUTING.md`,
`SECURITY.md`, `CHANGELOG.md`).

## Current documentation

| Document | Status | Purpose |
| --- | --- | --- |
| [history-v1.md](history-v1.md) | **Current / normative** | Extraction History V1: behaviour, storage, settings, UI, limits |
| [dependencies.md](dependencies.md) | **Current / normative** | Python/Flatpak dependency workflow: uv.lock, sync, FEDC/certifi ownership, headless GTK testing |
| [tessdata-integrity.md](tessdata-integrity.md) | **Current / normative** | Tessdata model integrity: checksum manifest, fail-closed verification, atomic install, anti-drift |
| [audit/legacy/reports/history-v1-plan.md](audit/legacy/reports/history-v1-plan.md) | **Historical** | Pre-implementation History V1 plan (baseline `testing @ a52f4563`); superseded by the merged History V1 integration |

Other normative references outside `docs/`:

| Document | Purpose |
| --- | --- |
| [../flatpak/README.md](../flatpak/README.md) | Flatpak manifests: local (edit) vs release (generated) |
| [../data/io.github.d3msudo.anura.metainfo.xml.in](../data/io.github.d3msudo.anura.metainfo.xml.in) | Flathub user-facing description and release notes |

## Structure

```text
docs/
├── README.md              ← this index
├── history-v1.md          ← current History V1 reference (normative)
├── dependencies.md        ← current dependency/CI workflow reference (normative)
└── audit/
    └── legacy/        Historical QA/security audit reports and raw
                       tool outputs (append-only, see audit/legacy/README.md).
                       ├── reports/   Human-readable reports (bug hunts, QA
                       │              summaries) + superseded implementation plans
                       └── raw/       Unprocessed tool outputs
                                      (bandit/mypy/ruff/vulture .txt/.json)
```

## Conventions

- Filenames use `kebab-case-lowercase.md`.
- Current/normative feature references live directly under `docs/`.
- Active (not yet implemented) plans belong in a top-level `planning/`
  directory, recreated when needed; once implemented they move to
  `audit/legacy/reports/` and are marked historical.
- Historical audit material belongs in `audit/legacy/` (append-only:
  add dated reports, never rewrite or delete).
- Agent tooling rules (`CLAUDE.md` is a thin pointer to `AGENTS.md`) are NOT
  documentation and are not indexed here.
