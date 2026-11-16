# Anura M1-04 — Semantic color consolidation and automated theme coverage

**Date:** 2026-11-16  
**Status:** Design proposal — awaiting maintainer approval  
**Repository:** `D3M-Sudo/Anura`  
**Working branch:** `fix/ui-modernization-aligned`  
**Parent phase:** M1 — Design System and themes  
**Selected approach:** B — semantic consolidation plus automated coverage

## 1. Context

The M1-03 read-only audit found that the approved green/teal palette and the existing theme-mode architecture are coherent. No Critical or High severity defect was demonstrated.

The audit identified three bounded improvement areas:

1. Downloaded-language success feedback uses explicit light/dark green literals rather than a Libadwaita semantic success style.
2. The same standalone green values are repeated in more than one CSS rule.
3. Existing tests do not provide an exhaustive guard against unclassified color literals or runtime coverage of all three supported theme modes across the affected UI surfaces.

The application already maps GSettings modes `default`, `force-light` and `force-dark` to `Adw.StyleManager`, listens for color-scheme changes, and uses theme-managed colors for surfaces, borders and warning states. This design preserves that architecture.

## 2. Goals

- Preserve the existing green/teal brand identity and the current meaning of all UI states.
- Determine, through implementation-level tests, whether Libadwaita `.success` is a suitable replacement for the downloaded-language success treatment.
- Consolidate repeated application-owned color values only where doing so improves semantic clarity or reduces drift.
- Add an automated guard that detects unclassified hardcoded color literals in production UI source.
- Add automated coverage for `default`, `force-light` and `force-dark` transitions on the UI surfaces affected by custom theme rules.
- Keep test evidence reproducible in GitHub Actions and attributable to an exact commit SHA.

## 3. Non-goals and constraints

This task must not:

- change the approved green/teal palette or reintroduce the rejected blue direction;
- change OCR engines, models, OCR behavior, image processing or processing pipelines;
- add dependencies or introduce a CSS preprocessor;
- change application architecture, portals, packaging contracts or OS integration;
- replace theme-managed GTK/Libadwaita colors with application-owned literals;
- redesign unrelated windows or components;
- introduce new user-visible states or alter download behavior;
- require manual GNOME/GTK visual inspection, real Orca/AT-SPI verification or manual keyboard navigation;
- claim that automated GTK tests establish pixel-level visual conformance or real assistive-technology behavior.

The existing `default`, `force-light` and `force-dark` settings and their persistence semantics must remain unchanged.

## 4. Proposed design

### 4.1 Downloaded-language success semantics

Evaluate Libadwaita's `.success` style class on the existing downloaded-language success indicator.

The implementation decision is conditional:

- Adopt `.success` if automated GTK tests demonstrate that it preserves the intended success semantics, readable text contrast in light and dark schemes, and the established green/teal identity.
- If the native class does not satisfy those conditions, retain an application-owned semantic success token with explicit light/dark values. Do not force a native style merely to eliminate literals.
- Do not add an explicit error color role unless an existing production UI state demonstrates a concrete need.

The audit's representative contrast calculations are useful baselines, not runtime measurements. Tests must distinguish application-owned text from graphical accents and evaluate the actual style mechanism available to the test environment.

### 4.2 Consolidation of repeated colors

Centralize repeated standalone green values only when the resulting token has a clear semantic role and does not obscure the distinction between brand accent, suggested-action colors, success feedback and focus indication.

Keep these roles distinct:

- brand/graphical accent: `#16A36A`;
- suggested-action background and light standalone green: `#0F7650`;
- suggested-action foreground: `#FFFFFF`;
- dark-scheme standalone green: `#21B77A`;
- warning and theme-managed surface/text/border roles: GTK/Libadwaita-provided values.

Do not collapse values solely because they are all green. In particular, the accent color is not a general normal-text color.

### 4.3 Hardcoded-color classification guard

Add a deterministic test or test helper that scans production UI source for color literals and fails on any literal that has not been explicitly classified.

Initial scan scope:

- application stylesheet(s) under `data/`;
- Blueprint UI definitions under `data/ui/`;
- Python application/widget source under `anura/` where UI styling or color values can be authored.

Recognize the color-literal forms actually used or reasonably supported by these source formats, including hexadecimal colors and CSS `rgb()`/`rgba()` forms. The scanner must report path and literal for actionable failures.

Use a small explicit allowlist/classification map for approved literals, with a short semantic rationale for each entry. Avoid line-number-based allowlisting. Theme variables such as `@theme_*`, `@accent_*` and `@warning_color` are semantic references, not hardcoded literals, and must not be reported. Avoid scanning generated files, documentation examples, test fixtures or non-UI data as production styling.

The test must prove both sides of the contract: an approved/classified color passes, and an injected unclassified color in a temporary fixture fails. The scan scope and exclusions must be documented so that it is not described as a scan of every arbitrary byte in the repository.

### 4.4 Automated theme-mode coverage

Extend the existing GTK integration test approach to exercise the actual application theme manager and affected UI surfaces.

Coverage must include:

- switching to `default`, `force-light` and `force-dark`;
- transitions between modes in one test process, not only initial construction;
- the downloaded-language success indicator;
- the History empty-state icon;
- the custom focus indicator where it is represented in application CSS;
- preservation of theme-managed surface/text/border roles and the warning state.

Tests should assert observable GTK state and the relevant style-class/theme-mode contract. Where GTK does not expose resolved CSS values through a stable test API, assert the supported semantic/style-manager state rather than inventing a pixel or color-resolution assertion.

Use the existing headless GTK/Weston CI environment. Do not add a new runtime dependency or require a physical display. Tests must restore global style-manager/settings state to avoid order-dependent failures.

## 5. Candidate files and change boundaries

Expected production/test touchpoints, subject to source inspection before implementation:

- `data/style.css` — semantic success and existing light/dark color rules;
- `anura/main.py` — only if the existing theme manager requires a test seam; no theme architecture rewrite;
- relevant UI Blueprint/Python files that own the downloaded-language or History state styling;
- `tests/test_ui_palette.py` — palette classification and scanner regression coverage;
- GTK integration test module(s) already used for theme/UI behavior;
- `docs/ui-design-system.md` — semantic color-role rules and scanner conventions;
- `CHANGELOG.md` — concise entry if implementation changes user-visible styling or test/maintenance behavior in a release-relevant way.

No other files should be changed without documenting why they are required. Roadmap and handover records are updated after the task outcome is established.

## 6. Acceptance criteria

M1-04 implementation is acceptable only if all of the following hold:

1. The existing green/teal palette values and their approved semantic distinctions are preserved.
2. The downloaded-language success indicator uses Libadwaita `.success` only if tests establish equivalent or better semantics and contrast in both schemes; otherwise a documented application-owned semantic token remains.
3. Repeated color literals are consolidated only where the semantic role is identical; no brand, success, focus or suggested-action roles are conflated.
4. The color scanner detects supported unclassified literals in its declared production UI scope and reports actionable file/literal details.
5. Scanner tests prove approved literals pass and unclassified fixture literals fail.
6. Automated GTK tests exercise all three theme modes and transitions on each affected custom-color surface.
7. Theme-managed surfaces, text, borders and warning colors remain theme-managed.
8. Existing theme mode selection, settings persistence and UI behavior remain unchanged.
9. Relevant unit/static and GTK integration tests pass in GitHub Actions on the exact implementation SHA.
10. No new dependency, OCR change, architecture change, portal/OS change or excluded manual verification is introduced or claimed.

## 7. Verification and evidence plan

- Run focused scanner/palette tests and the relevant GTK integration tests through GitHub Actions.
- Run the full existing CI Quality Check & Release workflow and CodeQL on the final implementation head.
- Record exact workflow URLs, commit SHA, job conclusions, test counts, skips and warnings.
- Inspect the diff for accidental changes to OCR, dependencies, packaging, portals, OS integration and unrelated UI behavior.
- Keep manual GNOME/GTK visual checks, real Orca/AT-SPI and manual keyboard checks explicitly excluded.
- Attribute every CI result to the exact SHA it tested; a later documentation-only commit must not inherit earlier CI evidence.

## 8. Alternatives considered

- **A — semantic consolidation only:** smaller change, but leaves the scanner and theme-transition coverage gaps unresolved.
- **B — semantic consolidation plus full automated coverage (selected):** addresses both the color-role concern and the missing regression guards while remaining bounded to UI styling and tests.
- **C — tests before visual changes:** reduces initial styling risk, but defers the already identified success-role and duplicate-token assessment.

Approach B is selected by the maintainer. The conditional rule in §4.1 prevents adopting `.success` if evidence shows a brand or contrast regression.

## 9. Approval gate

This document is a design proposal only. No source code, tests, CHANGELOG, workflows, roadmap or PR metadata are changed by the proposed implementation at this stage.

**Next step after approval:** prepare a separate implementation plan with file-by-file tasks, test-first steps, GitHub Actions verification and evidence checkpoints. Implementation requires a further explicit maintainer approval after the plan is reviewed.
