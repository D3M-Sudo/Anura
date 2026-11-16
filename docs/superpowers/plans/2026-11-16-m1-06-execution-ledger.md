# M1-06 execution ledger

Plan: `docs/superpowers/plans/2026-11-16-m1-06-reduced-motion-color-scanner-plan.md`
Spec: `docs/superpowers/specs/2026-11-16-m1-06-reduced-motion-color-scanner-design.md`
Base: `57d2bad6399526f155d3ccb2d992a41631e8b877`
Branch: `fix/ui-modernization-aligned`

## Task 1 — F1 Shortcuts reduced-motion

- Tests first. Test-only SHA `2a937aca9e196973dfa6646c986fe84909fb8dad`: expected RED, 4 new GTK tests failed; existing GTK tests 443 passed, 5 skipped, 650 deselected.
- Added root-motion assertions and fallback coverage. Test-only SHA `f7f03be1f5eddecf9257d6cc75e52cb0c0ddee4f`: expected RED, same 4 tests failed before implementation.
- Implemented on `33e113f8e6d1c8f865addeb653392a91e5d4bcf3`: settings observation, helper reuse, initial synchronization and root motion class suppression/restoration.
- **Ruling:** the `.reduced-motion *` selector excludes the root widget. Remove `anura-fade-in` and `anura-card` while reduced motion is active and restore in normal mode. This preserves CSS and keeps the fix scoped. Cost if wrong: root-level motion could persist.
- GTK exposed a lifecycle gap: `Gtk.Window.destroy()` in the integration test did not exercise the existing `do_destroy()` cleanup. Test-only SHA `08870472896167b7321e9aa71b557ebdd8f93b3b` remained RED on handler disconnection.
- **Ruling:** disconnect settings handlers on `_on_close_request()` as well as in `do_destroy()`, retaining the latter as an idempotent fallback. Cost if wrong: a close path bypassing both hooks could retain a settings callback.
- Cleanup implementation SHA: `f0fded293f2358dfa274b5f92254ee8f599183b5`.
- Added live fallback changes for GTK versions without `gtk-interface-reduced-motion` in test SHA `35fa684e72fd4e83eae4d58d4b7e731a00d2486b`.
- Green: GTK #43974750869 on SHA `35fa684e72fd4e83eae4d58d4b7e731a00d2486b`: 447 passed, 5 skipped, 650 deselected, 2 warnings.

## Task 2 — F2 production UI color scanner

- Added repository-root test in `tests/test_ui_color_scanner.py`; scanner implementation and fixture tests unchanged.
- Allowlist uses exact `(relative_path, normalized_value)` keys and non-empty semantic rationales for four hex literals and three shadow values in `data/style.css`.
- Assertion diagnostics include relative path, line, literal and syntax.
- Green: Python quality #43974750869 on SHA `35fa684e72fd4e83eae4d58d4b7e731a00d2486b`: scanner repository test and fixture tests passed; full Python suite 644 passed, 6 skipped, 277 deselected.

## Task 3 — Documentation and verification

- Updated CHANGELOG, global roadmap, PR roadmap, HANDOVER and this ledger.
- Static checks passed in Python quality: Ruff lint/format, mypy, Bandit and runtime dependency coverage.
- Changelog integrity passed.
- CodeQL #43974750821 passed on SHA `35fa684e72fd4e83eae4d58d4b7e731a00d2486b`.
- CI #43974750869 on the same SHA: Python and GTK passed; AppImage x86_64/aarch64 and Flatpak x86_64/aarch64 plus release validation were still running at the time of this ledger update.
- PR #648 last checked: Open, Draft, unmerged, base `feature`, head `fix/ui-modernization-aligned`.
- No protected branches, PR metadata, dependencies, OCR, palette, architecture, portal or OS configuration changed.
- Manual visual, Orca/AT-SPI, keyboard and live multi-monitor checks are excluded and not claimed. F3/F4 remain deferred.

## Final review

- Read-only compare `57d2bad6399526f155d3ccb2d992a41631e8b877...35fa684e72fd4e83eae4d58d4b7e731a00d2486b` reviewed. Final implementation diff is limited to `anura/widgets/shortcuts_overlay.py`, `tests/test_widgets.py` and `tests/test_ui_color_scanner.py`; no Critical or Important code issues identified in self-review.
- Ruff, mypy, Bandit, Python and GTK CI passed on the exact implementation/test SHA. No independent subagent review was possible or claimed.
- The AI Delivery Evidence Checker assessed supplied materials only and returned partial support because it cannot inspect repository code or authenticate CI. It is an evidence-sufficiency aid, not a correctness verdict.
- At this ledger snapshot, all CI jobs on SHA `35fa684e72fd4e83eae4d58d4b7e731a00d2486b` passed except AppImage aarch64, which remained in progress. M1-06 closure and final plan Step 4 remain pending until that job finishes.