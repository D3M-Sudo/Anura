# Anura — History V2, minimal cut: row interaction (current behaviour on `testing`)

This document is the **normative** reference for what History rows do since the
History V2 minimal cut ([#434](https://github.com/D3M-Sudo/Anura/pull/434) copy button,
[#452](https://github.com/D3M-Sudo/Anura/pull/452) expandable rows). Storage, settings,
recorded fields and the clear action are unchanged and stay documented in
[history-v1.md](history-v1.md). The design decisions and the measurements behind
them are in [../planning/history-v2-interactive-rows.md](../planning/history-v2-interactive-rows.md).

## What History V2 provides

- Each entry is an expandable row (`Adw.ExpanderRow`).
- Activating the row header (Enter, Space or click) expands it and shows the **full
  stored text**.
- A copy button in the row header copies the full stored text to the clipboard.

Not provided in this cut: opening an entry in the external editor
([#454](https://github.com/D3M-Sudo/Anura/issues/454)), TTS replay
([#455](https://github.com/D3M-Sudo/Anura/issues/455)), re-OCR
([#456](https://github.com/D3M-Sudo/Anura/issues/456)), row-level shortcuts. Search,
thumbnails, image archiving, database storage, sync, export/import, tags/folders,
editing of historical entries and OCR result versioning remain out of scope.

## Row behaviour

- **Header:** title = first line of the stored text (capped at 200 characters),
  subtitle = `timestamp · language · applied_name · confidence%` (empty fields skipped),
  as in V1. Title and subtitle are **not** parsed as Pango markup (`use_markup=False`):
  OCR text such as `a < b & c` would otherwise fail to parse and show an empty title.
- **One row open at a time.** Expanding a row collapses the previous one.
- **Expansion is not remembered.** Every `HistoryPage.refresh()` (opening the page,
  after Clear) rebuilds the list with all rows collapsed.
- **Expanded content:** a read-only, wrapping `Gtk.TextView` inside a
  `Gtk.ScrolledWindow` of at most 240 px (`_EXPANDED_TEXT_MAX_HEIGHT`); longer text
  scrolls. Its minimum height is estimated from the text
  (`estimate_text_area_height`), because a text view reports only the height of the
  part it has already laid out; short text takes only the room it needs.
- **The content is created on the first expansion**, once per row, not when the page
  is populated. The list is not virtualised and stored text has no size limit; creating
  every area up front made a 50-entry list of 50 KB entries take 48 s to show, against
  2 s with lazy creation (measured with software rendering; the ratio is what matters).

## Copy action

- Button in the row header (`edit-copy-symbolic`), reachable with the keyboard
  whether the row is open or not. It copies the full stored text, not the header title.
- `HistoryController.copy_entry_text(text)` returns `True` only when the text reached
  the clipboard service. Outcomes are reported through GObject signals and
  `AnuraWindow` shows them as toasts:

  | Outcome | Signal | Toast |
  | --- | --- | --- |
  | Copied | `copied` | `Text copied to clipboard` |
  | Empty text | `error-occurred` | `No text to copy` |
  | No display / clipboard unavailable (`RuntimeError`) | `error-occurred` | `Failed to copy text to clipboard` |

- On success the button shows `object-select-symbolic` and the tooltip/accessible
  label change for 2 s, then return to normal. A failed copy shows no success
  feedback. `emblem-ok-symbolic` is deliberately not used: it does not exist in the
  `org.gnome.Platform//50` icon theme.
- The text reaches other applications as plain text (`text/plain`) through
  `ClipboardService`.

## Architecture and lifecycle

- `HistoryPage` is a UI shell; the action logic lives in
  `anura/controllers/history_controller.py` (`HistoryController`), created and
  registered by `AnuraWindow` and injected into `HistoryPage.setup()`. The page keeps
  only a weak reference to the controller.
- Per-row signal handlers are **not** tracked by `SignalManagerMixin` (it would keep
  discarded rows alive until teardown). They are stored in `_row_handlers` and
  disconnected in `_clear_rows()`, together with the pending feedback timers.
- `HistoryEntry` is frozen and is never mutated by row actions; copying and expanding
  are read-only.
- No GSettings keys, shortcuts or translatable strings were added for row expansion.

## Tests

| File | Coverage |
| --- | --- |
| `tests/test_history_ui.py` (headless) | Rows are `ExpanderRow` with a header copy button, markup disabled, lazy text area, single open row, reset on refresh, full text, height estimate, handler and timer cleanup |
| `tests/test_history_controller.py` (headless) | Copy outcomes and signals, typed error handling, registration and cleanup |
| `tests/test_history_expansion_real.py` (GTK-marked) | Real `HistoryPage` and real widgets: initial state, full text, single open row, refresh, rendered height of long and short text, cost of a 300 KB text, copy with the row open |
| `tests/test_clipboard_service.py` (GTK-marked) | Text published as a plain string; read-back from the real clipboard |
| `tests/test_pot_template.py` | The gettext template parses, has no duplicate msgids and contains the History strings |

## Limitations

- Expansion is not remembered across refreshes.
- Very long text is shown in a scrollable area of limited height rather than in full.
- The expanded/collapsed state is left to `AdwExpanderRow`: Anura adds no accessibility
  annotation of its own for it (the copy button keeps its own accessible label). How a
  screen reader announces it depends on the libadwaita version in use.
