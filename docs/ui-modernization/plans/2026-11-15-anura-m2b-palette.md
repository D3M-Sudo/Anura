# Anura M2-B Palette Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Apply the approved green palette roles and preserve clear interaction states across the existing UI modernization.

**Architecture:** Keep palette tokens and component state rules in the existing `data/style.css`. Add a focused, dependency-free regression test that reads the shipped stylesheet, checks token roles and WCAG contrast calculations, and protects button interaction-state declarations. No new CSS framework or runtime abstraction.

**Tech Stack:** GTK 4, Libadwaita, GTK CSS, Python 3.12, pytest, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-11-15-anura-m2b-palette-design.md`

## Global Constraints
- Work only on `fix/ui-modernization-aligned`; do not modify protected `feature`.
- Keep PR #648 open and Draft; do not merge.
- Use `#16A36A` for non-text brand accents, `#0F7650` for light-surface accent text and suggested-action backgrounds with white foreground, and `#21B77A` for dark-surface accent text.
- No screen redesign, behavior change, or dependency addition.
- Manual Linux Mint, keyboard and Orca/AT-SPI checks are skipped and must remain explicitly unverified.

## Review Focus
- Light and dark Adwaita surfaces: each text accent must meet WCAG AA normal-text contrast.
- Graphical accent against light and dark surfaces: maintain at least 3:1 contrast.
- Suggested-action foreground/background pairing: maintain at least 4.5:1 contrast.
- Focus and disabled controls: custom hover/active effects must not obscure focus or make disabled controls appear actionable.
- Welcome primary action: Screenshot must retain its existing suggested-action hierarchy.

---

### Task 1: Consolidate palette roles and interaction-state styling

**Files:**
- Modify: `data/style.css`
- Create: `tests/test_ui_palette.py`
- Preserve: `data/ui/welcome_page.blp` Screenshot primary-action declaration

**Interfaces:**
- Consumes: existing GTK CSS tokens and selectors in `data/style.css`.
- Produces: approved token values and explicit `.anura-button:focus` / `.anura-button:disabled` rules; test helpers remain private to `tests/test_ui_palette.py`.

- [ ] **Step 1: Add failing tests first.** Cover token roles, WCAG contrast thresholds (4.5:1 text, 3:1 graphical accents), light/dark downloaded-label text colors, hover/active/focus/disabled declarations, and Screenshot's suggested-action class.
- [ ] **Step 2: Verify RED.** Run `pytest tests/test_ui_palette.py -q` in the PR validation workflow. Expected: failures for the old token values and missing explicit focus/disabled rules; no collection or syntax errors.
- [ ] **Step 3: Implement the minimal stylesheet change.** Set `accent_color=#16A36A`, `accent_bg_color=#0F7650`, `accent_fg_color=#FFFFFF`; use `#0F7650` for downloaded text on light surfaces and `#21B77A` in dark mode. Add a visible 2px accent focus outline and suppress hover transforms/shadows when disabled. Do not change the Welcome Blueprint.
- [ ] **Step 4: Verify GREEN.** Run `pytest tests/test_ui_palette.py -q`, then the complete CI triggered by the PR update. Expected: focused tests pass; Python quality, Changelog integrity, GTK integration, AppImage and Flatpak jobs pass.
- [ ] **Step 5: Update delivery records.** Add a concise M2-B Task 2 entry to `HANDOVER.md` and `CHANGELOG.md`, recording actual CI links/results and explicitly stating manual desktop/AT-SPI checks were not performed.
- [ ] **Step 6: Commit the implementation.** Use a focused commit message such as `feat(ui): consolidate approved green palette`.

## Delivery gates
- Verify the branch and PR state after changes; PR #648 remains Draft and unmerged.
- Do not claim the branch is rebased unless Git ancestry proves it. The current GitHub connector exposes commit/ref operations but no native rebase operation; do not replace a rebase with a merge or history-squashing rewrite.
- Report any test or CI evidence that could not be obtained as a gap, not as a pass.
