# M1-06 — Reduced-motion coverage and UI color scanner enforcement

**Status:** Completed within approved scope; implementation, regression coverage, full CI and CodeQL passed.
**Date:** 2026-11-16
**Parent audit:** `docs/audit/ui-design-system-m1-05-2026-11-16.md`
**Target branch:** `fix/ui-modernization-aligned`

## Intent

Close the two Medium findings from M1-05 without expanding the UI modernization scope: make the separate Shortcuts window honor GTK's reduced-motion preference, and enforce the existing UI color scanner against production UI sources in pytest/CI.

## Approved approaches

- **F1 — A:** Apply the existing `is_reduced_motion_enabled()` / `sync_reduced_motion_class()` policy to `ShortcutsOverlay`, observing GTK settings changes while the window exists. This preserves normal animation when reduced motion is not requested.
- **F2 — A:** Add a repository-root scanner test to the existing pytest suite. Approvals are keyed by exact relative path and normalized color value, each with a non-empty semantic rationale.

## F1 requirements

- Read `Gtk.Settings` for the overlay's display during initialization.
- Apply the `.reduced-motion` class using the existing accessibility helper.
- Observe `notify::gtk-enable-animations` and, when exposed by the installed GTK version, `notify::gtk-interface-reduced-motion`.
- Reapply the class when either observed setting changes.
- Disconnect all newly connected settings handlers during window destruction.
- Do not mutate desktop-wide settings or alter the shared CSS animation rules.

## F2 requirements

- Determine the repository root from the test module location, not the current working directory.
- Call `scan_ui_color_literals(root)` and `find_unclassified_ui_colors(findings, approved)`.
- Maintain a path-specific approval map with non-empty rationales.
- Fail with actionable details including relative path, line, literal, and syntax for each unclassified finding.
- Keep fixture-based scanner tests and run the new repository test through the existing pytest invocation in `.github/workflows/main.yml`.

## Initial production color inventory to validate during implementation

The M1-05 snapshot reported these literals in `data/style.css`; the implementer must confirm exact scanner output before adding approvals:

- `#16a36a` — brand graphical accent.
- `#0f7650` — dark brand accent and light-scheme status text.
- `#ffffff` — foreground on the dark suggested-action background.
- `#21b77a` — dark-scheme status/focus accent.
- `rgba(0, 0, 0, 0.15)` — button hover shadow.
- `rgba(0, 0, 0, 0.1)` — button active shadow.
- `rgba(0, 0, 0, 0.12)` — card hover shadow.

No blanket/global color approval is permitted. If scanner output differs, investigate it; do not silently widen the allowlist.

## Non-goals and constraints

- No redesign of Shortcuts or other surfaces.
- No palette changes, CSS cleanup, or F3/F4 work from M1-05.
- No OCR, Tesseract, models, pipeline, architecture, portal, OS, or dependency changes.
- No changes to protected branches.
- PR #648 remains Open, Draft, unmerged, base `feature`, head `fix/ui-modernization-aligned`.
- This design approval alone did not authorize implementation; separate user approval for implementation was received on 2026-11-16. No merge or PR metadata changes were authorized.

## Acceptance

F1: initial reduced-motion state, initial normal-motion state, both live transition directions, and settings-handler cleanup are covered by GTK tests; normal animations remain enabled when the preference is off.

F2: the actual repository tree is scanned in pytest; an unapproved literal fails with path/line/value/syntax; path-specific approvals with blank rationales do not pass; existing fixture tests remain green.

Verification must be tied to the exact tested commit SHA. Run the relevant Python and GTK tests, then the applicable full CI and CodeQL checks. Manual visual, Orca/AT-SPI, manual keyboard and live multi-monitor tests remain outside scope and must not be claimed.


## Implementation outcome (2026-11-16)

- F1 and F2 implementation and automated regression coverage are complete on source/test SHA `35fa684e72fd4e83eae4d58d4b7e731a00d2486b`.
- F1 also removes/restores root `anura-fade-in` and `anura-card` classes because `.reduced-motion *` excludes the root widget; settings callbacks are disconnected on close-request and in `do_destroy()`.
- F2 scans the actual repository root with exact path/value approvals and semantic rationales.
- CI #43974750869 completed successfully on that SHA: all 9 executable jobs passed, including AppImage x86_64/aarch64 build, metadata, smoke-test and upload steps; Flatpak x86_64/aarch64; and both release-set validators. Python quality: 644 passed, 6 skipped, 277 deselected; GTK Integration: 447 passed, 5 skipped, 650 deselected, 2 warnings. Changelog integrity, Ruff, mypy, Bandit and CodeQL #43974750821 passed. `publish-release` was skipped as expected for a PR.
