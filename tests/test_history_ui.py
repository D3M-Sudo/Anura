# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""Focused headless tests for the History V1 page (HistoryPage).

Uses the repository's headless gi-mock convention: widgets are constructed
with `headless_gi_mocks` and gi-dependent modules are imported inside the
test functions. Behaviour is asserted on the template-child mocks.
"""

from unittest.mock import MagicMock

from anura.services.history_service import HistoryService


class FakeSettings:
    def __init__(self, enabled: bool = True):
        self.enabled = enabled

    def get_boolean(self, key: str) -> bool:
        if key != "history-enabled":
            raise KeyError(key)
        return self.enabled


def _make_page(headless_gi_mocks, service: HistoryService | None = None, enabled: bool = True):
    """Import and build the HistoryPage under headless gi stubs."""
    from anura.widgets.history_page import HistoryPage

    page = HistoryPage()
    # Under headless stubs, template children are shared class-level mocks;
    # give this instance fresh isolated mocks so call counts don't leak.
    page.history_stack = MagicMock()
    page.history_list = MagicMock()
    page.clear_button = MagicMock()
    page.settings = FakeSettings(enabled)
    if service is not None:
        page.setup(service)
    return page


# ---------------------------------------------------------------------- #
# Empty history / disabled state
# ---------------------------------------------------------------------- #


def test_empty_enabled_history_shows_empty_state(headless_gi_mocks, tmp_path):
    service = HistoryService(base_dir=tmp_path)
    page = _make_page(headless_gi_mocks, service, enabled=True)

    page.history_stack.set_visible_child_name.assert_called_with("empty")


def test_disabled_history_shows_disabled_state(headless_gi_mocks, tmp_path):
    service = HistoryService(base_dir=tmp_path)
    page = _make_page(headless_gi_mocks, service, enabled=False)

    page.history_stack.set_visible_child_name.assert_called_with("disabled")


def test_disabled_history_does_not_delete_existing_entries(headless_gi_mocks, tmp_path):
    """history-enabled=false must NOT clear persisted history."""
    service = HistoryService(base_dir=tmp_path)
    service.record("kept", "eng")
    _make_page(headless_gi_mocks, service, enabled=False)

    assert len(service.get_entries()) == 1


# ---------------------------------------------------------------------- #
# Entries display
# ---------------------------------------------------------------------- #


def test_one_entry_displayed(headless_gi_mocks, tmp_path):
    service = HistoryService(base_dir=tmp_path)
    service.record("hello world", "eng", applied_name="Magic", conf=91.0)
    page = _make_page(headless_gi_mocks, service)

    page.history_stack.set_visible_child_name.assert_called_with("entries")
    assert page.history_list.append.call_count == 1


def test_multiple_entries_newest_first(headless_gi_mocks, tmp_path):
    service = HistoryService(base_dir=tmp_path)
    service.record("first", "eng")
    service.record("second", "eng")
    service.record("third", "eng")
    page = _make_page(headless_gi_mocks, service)

    assert page.history_list.append.call_count == 3
    # Service API already guarantees newest-first; the page must not reorder.
    assert service.get_entries()[0].text == "third"


def test_long_text_does_not_break_page(headless_gi_mocks, tmp_path):
    service = HistoryService(base_dir=tmp_path)
    service.record("x" * 10_000, "eng")
    page = _make_page(headless_gi_mocks, service)

    page.history_stack.set_visible_child_name.assert_called_with("entries")
    assert page.history_list.append.call_count == 1


# ---------------------------------------------------------------------- #
# History V2 (minimal cut): per-row copy action
# ---------------------------------------------------------------------- #


def _patch_ui(monkeypatch):
    """Swap the gi namespaces used by history_page for recording fakes."""
    import anura.widgets.history_page as module

    timer_ids = iter(range(100, 200))
    fake_adw = MagicMock(name="Adw")
    fake_gtk = MagicMock(name="Gtk")
    fake_glib = MagicMock(name="GLib")
    fake_glib.SOURCE_REMOVE = False
    fake_glib.timeout_add_seconds.side_effect = lambda *_args: next(timer_ids)
    monkeypatch.setattr(module, "Adw", fake_adw)
    monkeypatch.setattr(module, "Gtk", fake_gtk)
    monkeypatch.setattr(module, "GLib", fake_glib)
    return fake_adw, fake_gtk, fake_glib


def _make_wired_page(headless_gi_mocks, tmp_path, copy_result=True):
    """Page wired to a fake controller (the page only keeps a weak reference)."""
    controller = MagicMock()
    controller.copy_entry_text.return_value = copy_result
    page = _make_page(headless_gi_mocks)
    page.setup(HistoryService(base_dir=tmp_path), controller)
    return page, controller


def test_rows_are_expander_rows_with_a_copy_button_in_the_header(headless_gi_mocks, monkeypatch, tmp_path):
    """Each entry is an expandable row; the copy button is a header suffix, not a row action."""
    fake_adw, fake_gtk, _fake_glib = _patch_ui(monkeypatch)
    service = HistoryService(base_dir=tmp_path)
    service.record("first", "eng")
    service.record("second", "eng")
    _make_page(headless_gi_mocks, service)

    assert fake_adw.ExpanderRow.call_count == 2
    fake_row = fake_adw.ExpanderRow.return_value
    assert fake_row.add_suffix.call_count == 2

    # The button's own handler is "clicked"; the row only listens to its expansion.
    button_calls = fake_gtk.Button.return_value.connect.call_args_list
    assert [c.args[0] for c in button_calls] == ["clicked", "clicked"]
    assert [c.args[2] for c in button_calls] == ["second", "first"]  # newest first
    row_calls = fake_row.connect.call_args_list
    assert [c.args[0] for c in row_calls] == ["notify::expanded", "notify::expanded"]
    assert [c.args[2] for c in row_calls] == ["second", "first"]


def test_row_text_is_not_parsed_as_pango_markup(headless_gi_mocks, monkeypatch, tmp_path):
    """Regression: OCR text like "a < b & c" must not be parsed as markup.

    Adwaita rows parse title and subtitle as Pango markup by default; text with
    `&` or `<` then fails to parse and the row shows an empty title (or drops
    tags such as `<b>`).
    """
    fake_adw, _fake_gtk, _fake_glib = _patch_ui(monkeypatch)
    service = HistoryService(base_dir=tmp_path)
    service.record("a < b & c", "eng")
    service.record("<b>bold</b> R&D", "eng")
    _make_page(headless_gi_mocks, service)

    assert fake_adw.ExpanderRow.call_count == 2
    for call in fake_adw.ExpanderRow.call_args_list:
        assert call.kwargs.get("use_markup") is False


def test_no_text_area_exists_before_a_row_is_expanded(headless_gi_mocks, monkeypatch, tmp_path):
    """The area is created on the first expansion: building the list must stay cheap."""
    fake_adw, fake_gtk, _fake_glib = _patch_ui(monkeypatch)
    service = HistoryService(base_dir=tmp_path)
    for i in range(3):
        service.record(f"entry {i} " + "x" * 10_000, "eng")
    _make_page(headless_gi_mocks, service)

    fake_gtk.TextView.assert_not_called()
    fake_gtk.ScrolledWindow.assert_not_called()
    fake_adw.ExpanderRow.return_value.add_row.assert_not_called()


def test_expanding_a_row_builds_a_bounded_read_only_text_area_once(headless_gi_mocks, monkeypatch, tmp_path):
    _fake_adw, fake_gtk, _fake_glib = _patch_ui(monkeypatch)
    page, _controller = _make_wired_page(headless_gi_mocks, tmp_path)
    row = MagicMock()
    row.get_expanded.return_value = True

    page._on_row_expanded(row, None, "full stored text")
    page._on_row_expanded(row, None, "full stored text")  # re-expanding must not rebuild

    row.add_row.assert_called_once_with(fake_gtk.ScrolledWindow.return_value)
    fake_gtk.TextView.assert_called_once()
    text_view_kwargs = fake_gtk.TextView.call_args.kwargs
    assert text_view_kwargs["editable"] is False
    assert text_view_kwargs["accepts_tab"] is False
    fake_gtk.TextView.return_value.get_buffer.return_value.set_text.assert_called_once_with("full stored text")
    scrolled_kwargs = fake_gtk.ScrolledWindow.call_args.kwargs
    assert scrolled_kwargs["max_content_height"] == 240
    assert scrolled_kwargs["propagate_natural_height"] is True
    assert scrolled_kwargs["hscrollbar_policy"] == fake_gtk.PolicyType.NEVER


def test_the_expanded_text_is_the_full_text_not_the_header_title(headless_gi_mocks, monkeypatch, tmp_path):
    """The header shows the first line, capped; the text handed to the area is the whole entry."""
    fake_adw, _fake_gtk, _fake_glib = _patch_ui(monkeypatch)
    full_text = ("first line " * 40) + "\nsecond line\nthird line " + ("y" * 5_000)
    service = HistoryService(base_dir=tmp_path)
    service.record(full_text, "eng")
    _make_page(headless_gi_mocks, service)

    title = fake_adw.ExpanderRow.call_args.kwargs["title"]
    assert len(title) < len(full_text)
    assert "second line" not in title
    assert fake_adw.ExpanderRow.return_value.connect.call_args.args[2] == full_text


def test_only_one_row_is_open_at_a_time(headless_gi_mocks, monkeypatch, tmp_path):
    _patch_ui(monkeypatch)
    page, _controller = _make_wired_page(headless_gi_mocks, tmp_path)
    first, second = MagicMock(name="first"), MagicMock(name="second")
    first.get_expanded.return_value = True
    second.get_expanded.return_value = True

    page._on_row_expanded(first, None, "A")
    assert page._open_row is first
    first.set_expanded.assert_not_called()

    page._on_row_expanded(second, None, "B")
    assert page._open_row is second
    first.set_expanded.assert_called_once_with(False)
    second.set_expanded.assert_not_called()

    # The previous row reporting that it collapsed must not close the new one.
    first.get_expanded.return_value = False
    page._on_row_expanded(first, None, "A")
    assert page._open_row is second

    # Collapsing the open row leaves none open.
    second.get_expanded.return_value = False
    page._on_row_expanded(second, None, "B")
    assert page._open_row is None


def test_text_area_height_estimate_is_small_for_short_text_and_capped_for_long_text(headless_gi_mocks):
    """Regression: a text view reports a tiny natural height until its layout is validated.

    With a long text the area stayed about 54 px tall, so the user would have had to
    scroll a two-line window. The minimum height is estimated from the text instead.
    """
    from anura.widgets.history_page import estimate_text_area_height

    assert estimate_text_area_height("") == estimate_text_area_height("short")
    assert 0 < estimate_text_area_height("short") < 100
    assert estimate_text_area_height("one\ntwo\nthree") > estimate_text_area_height("one")
    assert estimate_text_area_height("w" * 600) > estimate_text_area_height("w" * 60)  # wrapped lines count
    assert estimate_text_area_height("long " * 4_000) == 240
    assert estimate_text_area_height("x\n" * 100_000) == 240


def test_expanded_area_minimum_height_comes_from_the_text(headless_gi_mocks, monkeypatch, tmp_path):
    _fake_adw, fake_gtk, _fake_glib = _patch_ui(monkeypatch)
    page, _controller = _make_wired_page(headless_gi_mocks, tmp_path)
    row = MagicMock()
    row.get_expanded.return_value = True

    page._on_row_expanded(row, None, "long " * 4_000)

    assert fake_gtk.ScrolledWindow.call_args.kwargs["min_content_height"] == 240


def test_refresh_forgets_the_open_row_and_the_built_text_areas(headless_gi_mocks, monkeypatch, tmp_path):
    _patch_ui(monkeypatch)
    service = HistoryService(base_dir=tmp_path)
    service.record("entry", "eng")
    page = _make_page(headless_gi_mocks, service)
    row = MagicMock()
    row.get_expanded.return_value = True
    page._on_row_expanded(row, None, "entry")
    assert page._open_row is row
    assert row in page._content_built

    page.refresh()

    assert page._open_row is None
    assert page._content_built == set()


def test_copy_click_delegates_to_controller_and_shows_feedback(headless_gi_mocks, monkeypatch, tmp_path):
    _adw, _gtk, fake_glib = _patch_ui(monkeypatch)
    page, controller = _make_wired_page(headless_gi_mocks, tmp_path)
    button = MagicMock()

    page._on_copy_clicked(button, "copied text")

    controller.copy_entry_text.assert_called_once_with("copied text")
    button.set_icon_name.assert_called_once_with("object-select-symbolic")
    fake_glib.timeout_add_seconds.assert_called_once_with(2, page._reset_row_copy_button, button)
    assert page._feedback_timers == {button: 100}


def test_feedback_icons_are_available_in_the_gnome_50_runtime():
    """Regression: `emblem-ok-symbolic` is absent from the GNOME Platform 50 icon theme.

    Verified inside org.gnome.Platform//50: `object-select-symbolic` and
    `edit-copy-symbolic` exist, `emblem-ok-symbolic` does not (only the legacy
    emblem-important/emblem-system remain), which would render a missing icon in
    the Flatpak build.
    """
    import anura.widgets.history_page as module

    assert module._COPY_ICON == "edit-copy-symbolic"
    assert module._COPIED_ICON == "object-select-symbolic"


def test_failed_copy_shows_no_success_feedback(headless_gi_mocks, monkeypatch, tmp_path):
    _adw, _gtk, fake_glib = _patch_ui(monkeypatch)
    page, controller = _make_wired_page(headless_gi_mocks, tmp_path, copy_result=False)
    button = MagicMock()

    page._on_copy_clicked(button, "text")

    controller.copy_entry_text.assert_called_once_with("text")
    button.set_icon_name.assert_not_called()
    fake_glib.timeout_add_seconds.assert_not_called()
    assert page._feedback_timers == {}


def test_repeated_click_during_feedback_keeps_a_single_timer(headless_gi_mocks, monkeypatch, tmp_path):
    _adw, _gtk, fake_glib = _patch_ui(monkeypatch)
    page, controller = _make_wired_page(headless_gi_mocks, tmp_path)
    button = MagicMock()

    page._on_copy_clicked(button, "text")
    page._on_copy_clicked(button, "text")

    assert controller.copy_entry_text.call_count == 2
    assert fake_glib.timeout_add_seconds.call_count == 1


def test_reset_row_copy_button_restores_state(headless_gi_mocks, monkeypatch, tmp_path):
    _adw, _gtk, _fake_glib = _patch_ui(monkeypatch)
    page, _controller = _make_wired_page(headless_gi_mocks, tmp_path)
    button = MagicMock()
    page._on_copy_clicked(button, "text")

    result = page._reset_row_copy_button(button)

    assert result is False  # GLib.SOURCE_REMOVE: the timer must not repeat
    button.set_icon_name.assert_called_with("edit-copy-symbolic")
    assert page._feedback_timers == {}


def test_copy_without_controller_is_a_safe_noop(headless_gi_mocks):
    page = _make_page(headless_gi_mocks)
    button = MagicMock()

    page._on_copy_clicked(button, "text")

    button.set_icon_name.assert_not_called()
    assert page._feedback_timers == {}


def test_clear_rows_cancels_timers_and_disconnects_row_handlers(headless_gi_mocks, monkeypatch, tmp_path):
    fake_adw, fake_gtk, fake_glib = _patch_ui(monkeypatch)
    fake_button = fake_gtk.Button.return_value
    fake_row = fake_adw.ExpanderRow.return_value
    fake_button.connect.side_effect = [11, 12, 13, 14]
    fake_row.connect.side_effect = [21, 22, 23, 24]
    service = HistoryService(base_dir=tmp_path)
    service.record("first", "eng")
    service.record("second", "eng")
    page = _make_page(headless_gi_mocks, service)  # first refresh: buttons 11, 12; rows 21, 22
    controller = MagicMock()
    controller.copy_entry_text.return_value = True

    page.setup(service, controller)  # second refresh clears the first rows

    fake_button.disconnect.assert_any_call(11)
    fake_button.disconnect.assert_any_call(12)
    fake_row.disconnect.assert_any_call(21)
    fake_row.disconnect.assert_any_call(22)
    assert sorted(handler_id for _widget, handler_id in page._row_handlers) == [13, 14, 23, 24]

    page._on_copy_clicked(MagicMock(), "text")
    pending_id = next(iter(page._feedback_timers.values()))
    page._clear_rows()

    fake_glib.source_remove.assert_called_once_with(pending_id)
    fake_button.disconnect.assert_any_call(13)
    fake_button.disconnect.assert_any_call(14)
    fake_row.disconnect.assert_any_call(23)
    fake_row.disconnect.assert_any_call(24)
    assert page._feedback_timers == {}
    assert page._row_handlers == []


def test_refresh_does_not_accumulate_tracked_connections(headless_gi_mocks, tmp_path):
    """Regression: per-row tracked connections kept discarded rows alive."""
    service = HistoryService(base_dir=tmp_path)
    for i in range(5):
        service.record(f"entry {i}", "eng")
    page = _make_page(headless_gi_mocks, service)
    baseline = page.get_tracked_signal_count()

    for _ in range(3):
        page.refresh()

    assert page.get_tracked_signal_count() == baseline
    assert len(page._row_handlers) == 5 * 2  # copy button + expansion, per row


def test_teardown_all_cancels_pending_timers_and_drops_controller(headless_gi_mocks, monkeypatch, tmp_path):
    _adw, _gtk, fake_glib = _patch_ui(monkeypatch)
    page, controller = _make_wired_page(headless_gi_mocks, tmp_path)
    page._on_copy_clicked(MagicMock(), "text")
    pending_id = next(iter(page._feedback_timers.values()))

    page.teardown_all()

    fake_glib.source_remove.assert_called_once_with(pending_id)
    assert page._feedback_timers == {}
    assert page._history_controller is None
    # After teardown a stray click must not reach the controller.
    page._on_copy_clicked(MagicMock(), "again")
    controller.copy_entry_text.assert_called_once_with("text")


# ---------------------------------------------------------------------- #
# Malformed entry / defensive formatting
# ---------------------------------------------------------------------- #


def test_malformed_entry_does_not_crash(headless_gi_mocks):
    """Defensive formatting must survive incomplete/garbage field values."""
    from anura.models.history import HistoryEntry
    from anura.widgets.history_page import (
        format_entry_subtitle,
        format_entry_timestamp,
        format_entry_title,
    )

    entry = HistoryEntry(text="ok", language="eng", applied_name="", conf=-1.0)
    subtitle = format_entry_subtitle(entry)
    assert isinstance(subtitle, str)
    assert "eng" in subtitle

    # Garbage timestamp → raw fallback, no exception
    entry_bad_ts = HistoryEntry(text="ok", language="eng", timestamp="not-a-date")
    assert format_entry_timestamp("not-a-date") == "not-a-date"
    assert format_entry_subtitle(entry_bad_ts).startswith("not-a-date")

    # Empty/None-ish text handling
    assert format_entry_title("") == ""
    assert format_entry_title(None) == ""  # type: ignore[arg-type]


# ---------------------------------------------------------------------- #
# Clear action
# ---------------------------------------------------------------------- #


def test_clear_action_refreshes_page(headless_gi_mocks, tmp_path):
    service = HistoryService(base_dir=tmp_path)
    service.record("doomed", "eng")
    page = _make_page(headless_gi_mocks, service)

    dialog = MagicMock()
    page._on_clear_response(dialog, "clear")
    dialog.force_close.assert_called_once()

    assert service.get_entries() == []


def test_clear_cancelled_keeps_entries(headless_gi_mocks, tmp_path):
    service = HistoryService(base_dir=tmp_path)
    service.record("safe", "eng")
    page = _make_page(headless_gi_mocks, service)

    page._on_clear_response(MagicMock(), "cancel")

    assert len(service.get_entries()) == 1


def test_clear_io_failure_does_not_crash(headless_gi_mocks, tmp_path, monkeypatch):
    service = HistoryService(base_dir=tmp_path)
    service.record("entry", "eng")
    page = _make_page(headless_gi_mocks, service)

    def failing_clear():
        raise OSError("disk full")

    monkeypatch.setattr(service, "clear", failing_clear)
    # Must not raise
    page._on_clear_response(MagicMock(), "clear")


# ---------------------------------------------------------------------- #
# Wiring (window-level, verified statically — window construction
# requires the full GTK template)
# ---------------------------------------------------------------------- #


def test_window_wires_history_page_and_navigation():
    from pathlib import Path

    window_src = (Path(__file__).resolve().parents[1] / "anura" / "window.py").read_text()
    assert "self.history_controller = HistoryController(self)" in window_src
    assert "self.history_page.setup(self.history_service, self.history_controller)" in window_src
    # Controller outcomes reach the user as toasts.
    assert 'self.connect_tracked(self.history_controller, "copied", self._on_history_copied)' in window_src
    assert 'self.connect_tracked(self.history_controller, "error-occurred", self._on_history_error)' in window_src
    assert 'self.navigation_view.push_by_tag("history")' in window_src

    window_blp = (Path(__file__).resolve().parents[1] / "data" / "ui" / "window.blp").read_text()
    assert "$HistoryPage history_page {" in window_blp
    assert 'tag: "history";' in window_blp

    welcome_blp = (Path(__file__).resolve().parents[1] / "data" / "ui" / "welcome_page.blp").read_text()
    assert '"win.show-history"' in welcome_blp


# ---------------------------------------------------------------------- #
# Clear confirmation dialog (regression: TypeError on present(parent))
# ---------------------------------------------------------------------- #


class _FakeAlertDialog:
    """Minimal stand-in recording the dialog wiring and presentation."""

    instances: list = []  # noqa: RUF012

    def __init__(self, **kwargs: object) -> None:
        self.kwargs = kwargs
        self.responses: list[tuple[str, str]] = []
        self.appearances: dict[str, object] = {}
        self.default_response: str | None = None
        self.close_response: str | None = None
        self.handlers: list[tuple[str, object]] = []
        self.presented_with: object = "<never-presented>"
        type(self).instances.append(self)

    def add_response(self, response: str, label: str) -> None:
        self.responses.append((response, label))

    def set_response_appearance(self, response: str, appearance: object) -> None:
        self.appearances[response] = appearance

    def set_default_response(self, response: str) -> None:
        self.default_response = response

    def set_close_response(self, response: str) -> None:
        self.close_response = response

    def connect(self, signal: str, callback: object) -> None:
        self.handlers.append((signal, callback))

    def force_close(self) -> None:
        pass

    def present(self, parent: object) -> None:
        self.presented_with = parent


def test_clear_clicked_uses_alert_dialog_and_presents_with_parent(
    headless_gi_mocks, monkeypatch, tmp_path
):
    """Regression: Adw.MessageDialog.present(parent) raised TypeError.

    The clear-confirmation dialog must be an Adw.AlertDialog presented with
    the parent window (dialog.present(parent) is valid on Adw.AlertDialog).
    """
    import anura.widgets.history_page as history_page_module

    _FakeAlertDialog.instances.clear()
    monkeypatch.setattr(history_page_module.Adw, "AlertDialog", _FakeAlertDialog)

    service = HistoryService(base_dir=tmp_path)
    page = _make_page(headless_gi_mocks, service)
    parent = object()
    page.get_ancestor = lambda _cls: parent  # isolate from any widget tree

    page._on_clear_clicked(MagicMock())

    assert len(_FakeAlertDialog.instances) == 1
    dialog = _FakeAlertDialog.instances[0]
    assert dialog.kwargs.get("heading") is not None
    assert ("clear", "Clear") in dialog.responses
    assert dialog.default_response == "cancel"
    assert dialog.close_response == "cancel"
    assert dialog.appearances.get("clear") is not None
    assert dialog.presented_with is parent


def test_clear_dialog_response_wiring_survives_migration(
    headless_gi_mocks, monkeypatch, tmp_path
):
    """The 'clear' response must still trigger service.clear(); 'cancel' must not."""
    import anura.widgets.history_page as history_page_module

    _FakeAlertDialog.instances.clear()
    monkeypatch.setattr(history_page_module.Adw, "AlertDialog", _FakeAlertDialog)

    service = HistoryService(base_dir=tmp_path)
    service.record("entry", "eng")
    page = _make_page(headless_gi_mocks, service)
    page.get_ancestor = lambda _cls: None

    page._on_clear_clicked(MagicMock())
    dialog = _FakeAlertDialog.instances[0]
    assert dialog.handlers and dialog.handlers[0][0] == "response"

    handler = dialog.handlers[0][1]
    handler(dialog, "cancel")
    assert len(service.get_entries()) == 1  # cancel keeps history

    handler(dialog, "clear")
    assert service.get_entries() == []  # clear wipes history


def test_history_page_no_longer_references_messagedialog():
    """Static guard: the deprecated crash-prone class must not come back."""
    from pathlib import Path

    source = (Path(__file__).resolve().parents[1] / "anura" / "widgets" / "history_page.py").read_text()
    assert "MessageDialog" not in source
    assert "Adw.AlertDialog" in source
