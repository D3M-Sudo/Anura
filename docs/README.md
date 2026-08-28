# Anura — Documentation Index

This directory contains permanent project documentation. Repository-level
documentation lives in the root (`README.md`, `AGENTS.md`, `CONTRIBUTING.md`,
`SECURITY.md`, `CHANGELOG.md`).

## Structure

```text
docs/
├── README.md          ← this index
├── planning/
│   └── history-v1-plan.md   Implementation plan for History V1
│                            (baseline: testing @ a52f4563)
└── audit/
    └── legacy/        Historical QA/security audit reports and raw
                       tool outputs (bug hunts, bandit/mypy/ruff/vulture).
                       Kept for historical traceability — do not treat
                       findings as open issues.
```

## Conventions

- Filenames use `kebab-case-lowercase.md`.
- Feature implementation plans belong in `planning/`.
- Historical audit material belongs in `audit/legacy/` (append-only).
- Agent tooling rules (`.clinerules/`, `.agents/`, `CLAUDE.md`) are NOT
  documentation and are not indexed here.
