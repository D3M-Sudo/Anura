# M0-C — Global backlog consolidation execution plan

**Design:** [M0-C global backlog consolidation](../specs/2026-11-16-m0-c-global-backlog-consolidation-design.md)  
**Branch:** `fix/ui-modernization-aligned`  
**Mode:** documentation-only; no application code or test execution.

## Preconditions

- Maintainer explicitly approved the M0-C design and plan.
- Confirm the current branch head and PR #648 state before writing.
- Fetch current versions and blob SHAs of all three target documents; use those SHAs for content updates.
- Abort rather than overwrite if the branch head or file contents changed unexpectedly.

## Execution steps

1. **Record design and plan.** Add the approved M0-C design and this plan under `docs/superpowers/specs/` and `docs/superpowers/plans/`.
2. **Consolidate the global roadmap.**
   - Update the phase status snapshot: M0 Completed only after this consolidation; M1–M4 Partial; M5 not started as a complete phase; M6–M7 Partial.
   - Replace the stale M0-C “next” statement with the completed M0 snapshot.
   - Correct M1-04 statements that still say semantic class linkage/theme-transition tests are unimplemented.
   - Add the prioritized backlog, dependencies, boundaries and acceptance criteria from the design.
   - Add an M0-C completion record with the resulting documentation commit/head and PR state.
3. **Align the PR #648 subordinate roadmap.**
   - State that the global roadmap controls current global status and backlog.
   - Preserve existing task/CI history.
   - Add a current-state reconciliation record and mark older “next task” directions as historical/superseded where they conflict.
   - Do not edit PR metadata or its description.
4. **Align `HANDOVER.md`.**
   - Add a concise current operational snapshot and authoritative links.
   - Identify stale continuation steps as historical and subordinate to the global roadmap.
   - Preserve technical and historical records.
5. **Review.**
   - Re-fetch all three documents and inspect changed sections.
   - Check relative links and ensure all three name M1-05 as the next recommended candidate, subject to a separate task proposal/approval.
   - Verify no forbidden file category or protected branch was modified.
6. **Verify PR state.** Re-read PR #648 and confirm Open, Draft, unmerged, base `feature`, head `fix/ui-modernization-aligned`.
7. **Report.** List each changed file, commit SHA(s), exact branch head, PR state, and any validation limitations. Do not claim project CI ran for documentation-only changes unless a new exact-SHA workflow result is observed.

## Stop conditions

- Unexpected branch head movement or blob-SHA mismatch.
- Any indication that the target branch is protected or not `fix/ui-modernization-aligned`.
- PR #648 is no longer Open/Draft/unmerged or its base/head differs from the approved state.
- A proposed edit would require changing code, tests, workflows, CHANGELOG, PR metadata or protected branches.

## Expected outcome

M0-C is complete when the global roadmap, subordinate PR roadmap and handover are mutually consistent, preserve historical evidence and identify M1-05 as the next task to propose—not as pre-authorized implementation.
