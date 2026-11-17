# Anura — audit (QA/security audit material)

This directory holds QA, security and debugging audit material for Anura,
split by lifecycle stage.

## Layout

- `legacy/` — **archived, append-only** historical audits whose findings are
  already resolved and merged. Rules in `legacy/README.md`.
  - `legacy/reports/` — human-readable reports (bug hunts, diagnoses,
    superseded plans) plus `bugs-observed.json` / `bugs-summary.md`
    (per-report index in `legacy/reports/README.md`).
- *(this root)* — reserved for **active** (not yet resolved) audit reports.
  Once a report's findings are resolved and merged, move it into
  `legacy/reports/` with a dated, kebab-case name.

## Conventions

- New reports use kebab-case names with an ISO date, e.g.
  `diagnosis-<topic>-YYYY-MM-DD.md`.
- `legacy/` is append-only: add new dated reports, never rewrite or delete
  existing files.
