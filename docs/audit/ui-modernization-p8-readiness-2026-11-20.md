# Anura UI Modernization — P8 Readiness and Traceability Report

**Date:** 2026-11-20  
**Repository:** `D3M-Sudo/Anura`  
**Workstream branch:** `fix/ui-modernization-aligned`  
**Active PR:** [#648](https://github.com/D3M-Sudo/Anura/pull/648), base `feature`, Open / Draft / unmerged  
**Report type:** documentation-only requirement/evidence reconciliation; not a native validation report.

## 1. Executive disposition

**P8 documentation consolidation: ready for final consistency verification, not yet evidence of native release readiness.** P1–P6 deterministic CI-testable scopes are complete within their explicit approvals. Global M6 remains Partial. P9 native-host validation is deferred. Translation quality review is separate and non-blocking for P8/P9 and UI Modernization closure.

No application-wide WCAG/accessibility-conformance claim is supported. CI success must be interpreted at the exact implementation or documentation SHA stated below; earlier CI runs do not validate later commits.

## 2. Requirement → delivery → evidence → disposition

| Requirement family | Delivery / source of truth | Evidence | Disposition | Remaining gap / owner gate |
|---|---|---|---|---|
| R01/R02 — coherent visual system, palette and themes | `data/style.css`; design-system docs; `tests/test_ui_palette.py`; production color scanner and scanner tests | P6 SHA `8d9a6a54219f868116d7ba839e85db75f437b254`; CI [44667645110](https://github.com/D3M-Sudo/Anura/actions/runs/44667645110); CodeQL [44667645155](https://github.com/D3M-Sudo/Anura/actions/runs/44667645155) | **Partially verified at static/reference contract level** | No exhaustive rendered contrast/layout across all surfaces, states and themes. Native GTK rendering belongs to P9. |
| R03 — responsive geometry and control reachability | P1/P2/P3 test modules and M6-01 surface matrix; viewports 360×600, 640×480, 900×600, 1280×800 | P1–P3 exact SHAs and CI runs listed in §3 | **Verified for bounded test scopes; partial globally** | Not every window/state has every reference viewport. Native rendering/geometry remains P9. |
| R04 — focus order, restoration and keyboard operability | P3 Shortcuts focus tests; P4 navigation focus routes and approved Welcome→History focus correction; #655 | P3 CI 44636489764; P4 CI 44649664012; corresponding CodeQL passed | **Selected route contracts verified; physical keyboard behavior deferred** | Physical Tab/Shift+Tab, native WM focus and complete navigation graph remain unverified. #655/P9. |
| R05 — accessible names, roles, states and announcements | P5 `tests/test_m6_02_accessible_control_contracts.py`; existing announcement and LanguageRow tests | P5 SHA `84607da73acb1873bd96ae923b2c0e2307688187`; CI 44655379141; CodeQL 44655379181 | **Selected GTK API contracts verified** | CI has `NO_AT_BRIDGE=1` and `GTK_A11Y=none`; no Orca speech or AT-SPI bridge validation. |
| R06 — reduced motion | `anura/utils/accessibility.py`, `anura/window.py`, `anura/widgets/shortcuts_overlay.py`; P6 tests | P6 CI 44667645110; Python Quality 703 passed, 9 skipped, 300 deselected | **Verified for app-authored CSS and tested live preference contracts** | Toolkit-native spinner/revealer/stack animation behavior is not proven. |
| R07 — Preferences and language lifecycle | M4-01, M4-02 Tasks 1–5, M4-RR plans and integration tests | M4 exact-head evidence recorded in global/workstream plans | **Complete only within approved CI-testable scopes; M4 Partial globally** | Native visual, focus and assistive-technology checks remain. |
| R08 — secondary windows, menus, dialogs and transient UI | M5-01 audit, M5-02 selected contracts, M5-03 portal banner correction | Exact evidence in global roadmap historical task records | **Complete within agreed bounded M5 scope** | Toast lifecycle explicitly excluded; About/fatal-dialog/Portal/popover residuals are not claimed complete. |
| R09 — localization and user-facing strings | `po/LINGUAS`, 26 `.po` catalogues, source `.pot`, Weblate workflow | Inventory proves 26 configured catalogue names; POT extraction is a separate technical artifact | **Catalogue inventory verified; completion/review unverified** | Per-language technical status and human linguistic review must be recorded independently. Separate non-blocking activity. |
| R10 — Linux integration, packaging and regression stability | CI AppImage/Flatpak x86_64/aarch64 and artifact checks | P6 CI 44667645110 passed GTK/package/artifact validation | **CI build/artifact validation verified at P6 SHA** | No installed-package smoke test on maintainer host; P9. |
| R11 — integrated readiness and traceability | Global/workstream/master/M6-02 plans, M6-01 audit, this report | P1–P6 exact evidence table; docs-only P6 reconciliation CI 44672653258; CodeQL 44672653395 | **P8 documentation reconciliation in progress/completed by this record; native readiness open** | Final verify all six docs and PR body at resulting head. |
| R12/R13/R17 — scope and governance constraints | Global roadmap governance and PR invariants | PR #648 metadata recheck after writes | **Constraints retained** | No OCR/pipeline/dependency/OS scope expansion; no protected branch or merge without approval. |

## 3. P1–P6 exact implementation evidence

| Priority | Scope | Tested implementation SHA | CI | CodeQL | Key recorded result |
|---|---|---|---|---|---|
| P1 | Extracted/History responsive | `f3b502177efa32c741307fce020f24fb1d4d7558` | [44484731845](https://github.com/D3M-Sudo/Anura/actions/runs/44484731845) | [44484731918](https://github.com/D3M-Sudo/Anura/actions/runs/44484731918) | Success; focused module 8 passed. |
| P2 | Preferences responsive | `65e2b1597b1d02f7aa851cfdb4dfd7f17920c7a6` | [44607860024](https://github.com/D3M-Sudo/Anura/actions/runs/44607860024) | [44607859740](https://github.com/D3M-Sudo/Anura/actions/runs/44607859740) | Success; GTK 474 passed, 6 skipped, 707 deselected. |
| P3 | Shortcuts/Language Selector focus/geometry | `fb91b6b5ebd2de8f7f7834ab88942f1f5a214870` | [44636489764](https://github.com/D3M-Sudo/Anura/actions/runs/44636489764) | [44636489904](https://github.com/D3M-Sudo/Anura/actions/runs/44636489904) | Success; GTK 480 passed, 6 skipped, 707 deselected; six new tests passed. |
| P4 | Cross-window focus routes | `e4aae923b17c163ef3031a1afc06c3e6f7452edec` | [44649664012](https://github.com/D3M-Sudo/Anura/actions/runs/44649664012) | [44649663981](https://github.com/D3M-Sudo/Anura/actions/runs/44649663981) | Success; GTK 483 passed, 6 skipped, 707 deselected. |
| P5 | Accessible control contracts | `84607da73acb1873bd96ae923b2c0e2307688187` | [44655379141](https://github.com/D3M-Sudo/Anura/actions/runs/44655379141) | [44655379181](https://github.com/D3M-Sudo/Anura/actions/runs/44655379181) | Success; GTK 488 passed, 6 skipped, 707 deselected; Python Quality 701 passed, 9 skipped, 299 deselected. |
| P6 | Semantic color/reduced-motion contracts | `8d9a6a54219f868116d7ba839e85db75f437b254` | [44667645110](https://github.com/D3M-Sudo/Anura/actions/runs/44667645110) | [44667645155](https://github.com/D3M-Sudo/Anura/actions/runs/44667645155) | Success; Python Quality 703 passed, 9 skipped, 300 deselected; GTK/package/artifact validation passed. |

The P6 evidence documentation commit was `a195a4f82be1d48d75c5c345933e59d96d82f9bd`. Its docs-only required gates passed in [CI run 44672653258](https://github.com/D3M-Sudo/Anura/actions/runs/44672653258) (Python Quality and Changelog Integrity); CodeQL [44672653395](https://github.com/D3M-Sudo/Anura/actions/runs/44672653395) also passed. GTK and packaging jobs were not required for that docs-only change.

## 4. Localization: separate technical and human status

The repository's `po/LINGUAS` lists 26 catalogues: ar, be_Latn, bn, ca, cs, de, es, eu, fi, fr, hi, ie, it, ja, ko_KR, nb_NO, nl, oc, pt, pt_BR, ru, sv, ta, tr, uk and zh_Hans.

Maintainer-approved process (2026-11-20):

1. Weblate and volunteer translators remain the translation workflow.
2. Automated CI catalogue checks are preliminary technical validation, not linguistic approval.
3. Human linguistic/contextual review is tracked separately, with Italian and English prioritized and all 26 catalogues retained in scope.
4. A populated `msgstr` does not prove review; an empty translation is assessed against fallback/release policy rather than assumed defective.
5. Translation review is non-blocking for P8/P9 and UI Modernization closure. No language is marked reviewed without evidence.

Current status: **inventory known; per-catalogue completeness and human-review status not yet evidenced in this report**. Do not claim full localization readiness.

## 5. P9 native-host validation backlog

Not started; requires a supported native desktop session and explicit authorization. Capture the exact branch/commit and host/session details before testing. Minimum evidence set:

- Native GTK4/Libadwaita rendering, theme variants, responsive reflow and clipping at representative sizes.
- Physical Tab/Shift+Tab traversal, including History row suffix actions, expanded/collapsed states and focus recovery (#655).
- Orca/AT-SPI with accessibility bridge enabled; record names, roles, states and actual announcements.
- Native window-manager focus, monitor/work-area and multi-monitor behavior where supported.
- Installed AppImage/Flatpak host runtime smoke checks as authorized.
- Screenshots remain deferred to the next release cycle; do not capture them as part of this P8 task.

## 6. Explicit exclusions and non-claims

- No application-wide WCAG conformance or complete accessibility claim.
- No claim of native visual, Orca/AT-SPI, physical keyboard or live WM validation from virtual GTK CI.
- No claim of complete translation or human linguistic review.
- No claim that P1–P6 close all M6 requirements.
- No code, dependency, workflow, OCR/model/pipeline, portal or OS changes in this P8 documentation pass.
- No release publication, protected-branch update, PR merge or PR state/base transition.

## 7. Governance and final gate

- Branch: `fix/ui-modernization-aligned`; PR base: `feature`.
- PR #648 must remain Open / Draft / unmerged.
- P8 can be marked documentarily complete only after the global roadmap, workstream roadmap, master plan, M6-02 plan, HANDOVER and PR body are cross-checked at the resulting exact head and the docs-only CI gates are observed.
- P9 remains separately gated by native session availability and explicit authorization.
