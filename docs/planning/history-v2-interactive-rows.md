# Anura — History V2: Interactive History Rows (planning)

**Status:** Minimal cut (copy button + expandable rows) in implementation; everything else still planning.  
**Target:** next major/minor release after History V1 stabilisation.  
**Owning documents:** this file, `docs/reference/history-v1.md`, `docs/README.md`.

## Motivation

History V1 provides a read-only list of past extractions with a single destructive
clear action, but historical OCR results are completely unactionable from the UI:

- a past entry cannot be copied to the clipboard,
- a past entry cannot be opened in the external editor,
- a past entry cannot be re-submitted to the OCR pipeline,
- a past entry cannot be replayed through TTS.

All these operations are available on **current** OCR results (`ExtractedPage`)
but not on historical ones. For a history feature this is a significant UX gap.
## Anti-scoping notes

This document is **not** a commitment to implement the full list above. It exists
to capture the problem statement and design space so that when V2 is started, the
decisions are made deliberately rather than ad hoc.

The minimal acceptable V2 cut is likely:

- row activatable,
- copy-to-clipboard action available from the row or a popover,
- consistent with V1 empty/disabled/entries states,
- no regressions to existing V1 behaviour (clear action, recording, settings).

Everything beyond that (external editor, TTS replay, re-OCR, popover actions,
shortcuts) is explicitly listed as optional and should be tracked separately when
moved from planning to implementation.

## Behavioural requirements

- History list remains **read-only** with respect to stored data: no inline
  editing, no reordering, no deletion except via the existing clear flow.
- Row actions do not destroy the history entry (copy/open/re-OCR/TTS are
  read-only consumers of a past result).
- Error paths (clipboard failure, file-launcher failure, OCR failure, TTS
  failure) surfaced through the same mechanisms used for current-result
  equivalents (toasts / error signals).
- Degrades gracefully when history is disabled or empty (`disabled`, `empty`,
  `entries` states, same as V1).
- No new GSettings keys in the initial cut; reuse `history-enabled` /
  `history-limit`.

## Interaction model

Suggested approach, consistent with current `ExtractedPage` patterns:

- Each row becomes `activatable` (GTK listbox row / `Adw.ActionRow` style).
- One primary action per row (at least **Copy**), reachable via keyboard focus +
  Enter/Space as well as mouse click.
- Optional secondary actions via an `Adw.Popover` or similar (Open in Editor,
  TTS, Re-OCR) to avoid cluttering the row UI.
- Keyboard shortcuts only if the design permits, subject to
  `test_shortcuts_consistency.py` anti-drift checks (new actions must appear in
  both the shortcuts overlay and `ActionRegistry`).
- Actions not applicable to a particular entry (for example TTS not available for
  that language) must be disabled/absent, not failing unexpectedly.


## Decisions for the minimal cut (expandable rows)

Recorded after the design audit of 2026-10-12. They refine, and where they differ
replace, the suggestions in "Interaction model" above.

- **Activating a row expands it** (Enter/Space/click on the header) to show the full
  stored text. The per-row copy button stays in the header as a suffix, so it is
  reachable with the keyboard whether the row is open or not, and the copy keeps
  using the full stored text.
- **Widget: `Adw.ExpanderRow`** (`expanded`, `add_row()`, `add_suffix()`; available
  since libadwaita 1.3). A custom row or a virtualised `Gtk.ListView` was considered
  and left out of this cut.
- **Content is created on the first expansion, not when the page is populated.** The
  history list is not virtualised and stored text has no size limit. Measured with 50
  entries of 50 KB each: creating every row's content up front took 48 s to show the
  page, against 2 s with the current rows and 2 s when it is created on expansion.
- **One open row at a time.** Expanding a row collapses the previous one.
- **Expansion is not remembered.** Every `refresh()` (opening the page, after Clear)
  rebuilds the list with all rows collapsed.
- **Long text is shown in a scrollable area with a maximum height**, a read-only
  `Gtk.TextView` inside a `Gtk.ScrolledWindow`. A `Gtk.Label` was measured and rejected:
  the first expansion took 1.06 s with 50 KB and 24 s with 300 KB, against 0.40 s and
  0.80 s for the text view. Short text takes only the height it needs.
- **No new strings, no new GSettings keys, no new shortcuts.** `HistoryEntry` is not
  mutated; opening a row is a read-only action.
- Row-level actions beyond Copy (external editor, TTS, Re-OCR) remain out of this cut.

## Proposed scope (History V2)

Make `HistoryPage` rows interactive. Candidates (in priority order):

1. **Copy to clipboard** — copy the stored `text` to the system clipboard.
2. **Open in external editor** — same handoff used by `ExtractedPage` for current
   OCR results (`Gtk.FileLauncher` / portal `open-uri`, writing the stored text
   to a temp export file first).
3. **Re-OCR (optional)** — send the stored text back through the OCR pipeline as
   a new extraction. This is more invasive because it duplicates the existing OCR
   flow and needs its own UX design; treat as stretch goal.
4. **TTS replay (optional)** — feed the stored text to the existing TTS pipeline
   (`TtsController.request_listen()`), reusing the same infrastructure.

Out of scope: search/filter, thumbnails, image archiving, database storage,
cloud sync, export/import, tags/folders, editing of historical entries, OCR
result versioning (future V3 and beyond).
## Implementation constraints

Must follow the same architectural rules enforced in this codebase:

- **Controller–Composition:** `HistoryPage` stays a UI shell; interaction
  coordination (clipboard, external editor, TTS, re-OCR) belongs in a dedicated
  controller/service, not inline in the widget.
- **Memory safety:** any long-lived connections (e.g. to TTS) use weak refs and
  a `.cleanup()` method wired to teardown.
- **Thread safety:** no GTK widget mutation from secondary threads; use
  `AtomicTaskManager` for background work (OCR, file I/O, network).
- **Immutability:** `HistoryEntry` is frozen; V2 must not mutate existing entries.
  New extractions produce new entries.
- **i18n:** use `_("...").format(...)` / `ngettext()`, never `_(f"...")`.
- **Security:** reuse existing sanitisation and file-export hardening; do not
  introduce new shared writable paths.

## Risks and open questions

- **Conflict with V1 clear action.** Clear is destructive and global; interactive
  rows must not make it easy to click the wrong thing; placement and affordance
  must be carefully chosen.
- **External editor handoff on historical text.** Need an equivalent export of
  stored text, reusing the existing hardened export path (`$XDG_RUNTIME_DIR/anura/exports`,
  mode `0600`, random names, stale cleanup) without breaking audit hardening.
- **TTS availability.** TTS depends on language mapping; replaying an old entry
  may be unavailable if the capture-time language is not currently configured.
- **"Re-OCR" semantics.** Re-OCR of already-cleaned historical text is
  questionable (stored text may already be transformer output, not raw OCR).
  If included, needs its own design: raw vs applied text, whether to re-run full
  pipeline, and what to do with the new result.
- **Localisation.** New string surface area: row action labels, popover titles,
  tooltips, new error messages. Must go through the i18n pipeline once UI strings
  are added (`po/`, `update_potfiles.sh`).

