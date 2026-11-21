# M0-C — Global backlog consolidation design

**Date:** 2026-11-16  
**Repository:** `D3M-Sudo/Anura`  
**Working branch:** `fix/ui-modernization-aligned`  
**Scope:** documentation-only consolidation of the application-wide UI/UX modernization programme.

## 1. Purpose

Make the global M0–M7 roadmap an accurate operational snapshot while preserving the detailed historical evidence already recorded in the repository. The global roadmap is authoritative for scope, phase status, dependencies and global prioritization. The PR #648 roadmap remains subordinate and records only that workstream's task history and evidence. `HANDOVER.md` supplies the current continuation context and technical history.

## 2. In-scope files

- `docs/superpowers/plans/2026-11-16-anura-ui-modernization-global-roadmap.md`
- `docs/superpowers/plans/2026-11-16-anura-ui-modernization-roadmap.md`
- `HANDOVER.md`
- This design record and its execution plan.

No application source, tests, workflows, packaging manifests, CHANGELOG, PR metadata or protected branches are in scope.

## 3. Status model and current snapshot

Use **Completed**, **Partial**, **In progress**, **Not started**, **Blocked**, and **Deferred / excluded** consistently. A bounded task can be complete while its containing global phase remains Partial.

| Phase | Current status | Evidence-based interpretation |
|---|---|---|
| M0 | Completed after this consolidation | M0-A inventory and M0-B traceability/evidence reconciliation were completed earlier; M0-C formalizes the prioritized dependency-ordered backlog and reconciles the records. |
| M1 | Partial | M1-02 conventions, M1-03 semantic-color audit and M1-04 scanner/color-class/theme-transition work are complete within their recorded scopes. Cross-surface Design System coverage remains. |
| M2 | Partial | Targeted Welcome, navigation, Extracted/History lifecycle work and audits exist; application-wide Welcome/main-shell exit criteria are not all established. |
| M3 | Partial | Selected Extracted and History protections/lifecycle work exist; full surface audit and modernization are not established. |
| M4 | Partial | Preferences split and selected lifecycle work exist; complete page and language-selector coverage is outstanding. |
| M5 | Not started as a complete phase | Limited Shortcuts resizing exists; remaining windows, dialogs and transient components lack complete app-wide audit evidence. |
| M6 | Partial | Selected automated responsive/accessibility coverage exists; cross-window coverage remains. |
| M7 | Partial | Strong PR-level CI and packaging evidence exists; global integration, translation review and final traceability remain. |

## 4. Prioritized dependency-ordered backlog

| ID | Priority | Task and boundary | Depends on | Acceptance / exit criteria |
|---|---|---|---|---|
| M1-05 | P1 | Audit Design System adoption across all in-scope UI surfaces. Read-only first; map tokens, typography, spacing, radii, semantic colors, component patterns and theme behavior. | M1-04 | Surface-by-surface matrix; evidence-backed findings; classify acceptable/gap/deferred; identify concrete implementation candidates without implementing them. |
| M1-06 | P1, conditional | Consolidate only demonstrable Design System gaps. Implementation task; scope and affected files must be proposed and separately approved. | M1-05 and explicit approval | Approved findings addressed; regression tests and exact-SHA CI recorded; no gratuitous restyling. If M1-05 finds no justified gap, mark not required with rationale. |
| M2-01 | P1 | Close the remaining Welcome/main-shell audit, including navigation, states and focus affordances. Audit first. | M2-E, M2-F | Requirement-to-surface matrix and findings; distinguish existing automated evidence from unverified manual checks. |
| M3-01 | P1 | Full Extracted and History audit, including OCR-visible states, actions, list/row/empty/confirmation behavior. | M1-05 | Complete surface/state inventory, behavior preservation map, findings and test gaps; no OCR internals or mockup-only features. |
| M4-01 | P1 | Full Preferences and language-selector audit across General, Editor, Voice, Languages and asynchronous states. | M1-05 | Page/state matrix, lifecycle and accessibility findings, test gaps; preserve settings and existing semantics. |
| M5-01 | P2 | Inventory and audit Shortcuts, About, dialogs, popovers, menus, banners, toasts and notifications. | M1-05 | Component/state inventory and evidence-backed disposition; already coherent surfaces may remain unchanged. |
| M6-01 | P2 | Build cross-window responsive/accessibility coverage matrix and close only approved automated-test gaps. | M2-01, M3-01, M4-01, M5-01 | Reference viewport matrix, focus/naming/announcement/contrast/reduced-motion evidence; explicitly list excluded manual checks. |
| M7-01 | P2 | Define integration and final validation plan across accepted requirements, CI and packaging. | M1-05 through M6-01; conditional M1-06 disposition | Traceability and validation plan with exact evidence requirements, translations review and deferred screenshot timing. |
| M7-02 | P3 | Execute approved global integration, documentation and distribution validation. | M7-01 and explicit approval | Full regression/packaging evidence, CHANGELOG and docs where relevant, translation review, final dispositions and release-readiness recommendation. |

P1 means foundational audit or justified gap closure; P2 means cross-surface validation and integration planning; P3 means final integration execution. The ordering is dependency-driven, not a blanket authorization to implement.

## 5. Mandatory task boundaries

- Every task receives a bounded proposal covering scope, affected surfaces/files, acceptance criteria and verification before implementation.
- Audits are read-only unless a separate change is explicitly approved.
- No implementation authorization is inferred from backlog inclusion or task completion.
- No new OCR engines, models, pipelines, image-processing behavior, dependencies, architecture, portals or OS integration.
- No mockup-only History search, photo previews, Save or formatting tools without separate approval.
- Manual GNOME/GTK visual checks, real Orca/AT-SPI checks and manual keyboard-navigation checks remain excluded; do not report them as passed or as blockers.
- Live multi-monitor geometry verification remains excluded.
- Screenshot capture remains deferred to the next release cycle.
- Use GitHub Actions for project tests and attribute every result to the exact tested SHA. Never claim local tests were run.
- PR #648 remains Open, Draft, unmerged, targeting `feature`; no PR metadata/state changes or protected-branch writes.

## 6. Evidence and documentation rules

- The global roadmap owns current phase status, backlog, dependencies and global requirement disposition.
- The PR #648 roadmap owns detailed workstream history and evidence; it must not imply global phase completion.
- `HANDOVER.md` points to both roadmaps and states the current next task without allowing historical next-step notes to override the current snapshot.
- Preserve prior task records and exact-SHA CI history. Mark stale continuation instructions as superseded rather than deleting historical evidence.
- A CI result on one SHA must never be attributed to a later documentation-only SHA unless that SHA was actually tested.

## 7. Completion criteria for M0-C

1. The three operational documents agree on hierarchy, current phase status and next recommended task.
2. The global backlog is prioritized, dependency ordered and has task boundaries and exit criteria.
3. Historical implementation and CI records remain intact and clearly historical where superseded.
4. Deferred/excluded verification is explicit and never represented as passed.
5. PR #648 is rechecked and remains Open/Draft/unmerged with base `feature` and head branch `fix/ui-modernization-aligned`.
6. No application code, tests, workflows, CHANGELOG, PR metadata or protected branch is changed.
7. The documentation diff is reviewed for internal consistency and exact-SHA accuracy.
