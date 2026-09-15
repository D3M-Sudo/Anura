# tests/test_conftest_error_reporting.py
# SPDX-License-Identifier: MIT
"""Regression tests for conftest._print_failure_reports.

These tests verify that pytest collection/setup errors (reported under the
'error' key in terminalreporter.stats) are printed alongside test failures
(reported under the 'failed' key).  Previously only 'failed' was printed,
causing 'error' entries to be completely invisible in CI output before
os._exit() was called.
"""

from unittest.mock import MagicMock

from conftest import _print_failure_reports


def _make_mock_report(nodeid: str, longrepr: str, sections=None) -> MagicMock:
    """Create a MagicMock resembling a pytest TestReport."""
    rep = MagicMock()
    rep.nodeid = nodeid
    rep.longrepr = longrepr
    rep.sections = sections or []
    return rep


def _make_mock_terminal_reporter(stats: dict) -> MagicMock:
    """Create a MagicMock resembling a pytest TerminalReporter with given stats."""
    tr = MagicMock()
    tr.stats = stats
    return tr


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestPrintFailureReports:
    """Tests for _print_failure_reports covering both 'failed' and 'error' keys."""

    def test_prints_error_reports(self, capsys):
        """Collection/setup errors (under 'error' key) must be printed."""
        err_rep = _make_mock_report(
            nodeid="tests/test_broken.py",
            longrepr="ImportError: No module named missing_pkg",
            sections=[("Captured stderr", "Traceback ... ImportError")],
        )
        tr = _make_mock_terminal_reporter({"error": [err_rep], "failed": []})

        _print_failure_reports(tr)

        captured = capsys.readouterr()
        assert "ERROR IN tests/test_broken.py:" in captured.out
        assert "ImportError: No module named missing_pkg" in captured.out
        assert "--- Captured stderr ---" in captured.out

    def test_prints_failure_reports(self, capsys):
        """Test failures (under 'failed' key) must still be printed."""
        fail_rep = _make_mock_report(
            nodeid="tests/test_something.py::test_case",
            longrepr="AssertionError: 1 != 2",
            sections=[("Captured stdout", "some debug output")],
        )
        tr = _make_mock_terminal_reporter({"failed": [fail_rep], "error": []})

        _print_failure_reports(tr)

        captured = capsys.readouterr()
        assert "FAILURE IN tests/test_something.py::test_case:" in captured.out
        assert "AssertionError: 1 != 2" in captured.out
        assert "--- Captured stdout ---" in captured.out

    def test_prints_both_error_and_failure_reports(self, capsys):
        """Both categories should be printed when both are present."""
        err_rep = _make_mock_report(
            nodeid="tests/test_broken.py",
            longrepr="ImportError: No module named x",
        )
        fail_rep = _make_mock_report(
            nodeid="tests/test_ok.py::test_one",
            longrepr="AssertionError: True is not False",
        )
        tr = _make_mock_terminal_reporter({
            "error": [err_rep],
            "failed": [fail_rep],
        })

        _print_failure_reports(tr)

        captured = capsys.readouterr()
        # Error comes first (printed before failures)
        assert "ERROR IN tests/test_broken.py:" in captured.out
        assert "ImportError: No module named x" in captured.out
        assert "FAILURE IN tests/test_ok.py::test_one:" in captured.out
        assert "AssertionError: True is not False" in captured.out

    def test_error_printed_before_failure(self, capsys):
        """The 'error' category should be printed before 'failed'."""
        err_rep = _make_mock_report(nodeid="err_test", longrepr="error details")
        fail_rep = _make_mock_report(nodeid="fail_test", longrepr="failure details")
        tr = _make_mock_terminal_reporter({
            "error": [err_rep],
            "failed": [fail_rep],
        })

        _print_failure_reports(tr)

        captured = capsys.readouterr()
        err_pos = captured.out.find("ERROR IN err_test:")
        fail_pos = captured.out.find("FAILURE IN fail_test:")
        assert err_pos != -1
        assert fail_pos != -1
        assert err_pos < fail_pos, "ERROR section should appear before FAILURE section"

    def test_empty_stats_does_not_crash(self, capsys):
        """Empty tr.stats should not raise."""
        tr = _make_mock_terminal_reporter({"failed": [], "error": []})

        _print_failure_reports(tr)

        captured = capsys.readouterr()
        assert "FAILURE" not in captured.out
        assert "ERROR IN" not in captured.out

    def test_missing_keys_does_not_crash(self, capsys):
        """Missing 'error' or 'failed' keys should not raise."""
        tr = _make_mock_terminal_reporter({"failed": []})

        _print_failure_reports(tr)

        captured = capsys.readouterr()
        assert "FAILURE" not in captured.out
        assert "ERROR IN" not in captured.out

    def test_multiple_reports_in_each_category(self, capsys):
        """Multiple errors and failures should all be printed."""
        err1 = _make_mock_report(nodeid="err1.py", longrepr="error 1")
        err2 = _make_mock_report(nodeid="err2.py", longrepr="error 2")
        fail1 = _make_mock_report(nodeid="fail1.py", longrepr="failure 1")
        fail2 = _make_mock_report(nodeid="fail2.py", longrepr="failure 2")

        tr = _make_mock_terminal_reporter({
            "error": [err1, err2],
            "failed": [fail1, fail2],
        })

        _print_failure_reports(tr)

        captured = capsys.readouterr()
        assert "ERROR IN err1.py:" in captured.out
        assert "ERROR IN err2.py:" in captured.out
        assert "FAILURE IN fail1.py:" in captured.out
        assert "FAILURE IN fail2.py:" in captured.out

    def test_report_with_no_sections(self, capsys):
        """Reports without sections should still print the header and longrepr."""
        rep = _make_mock_report(nodeid="test.py", longrepr="Some error", sections=[])
        tr = _make_mock_terminal_reporter({"error": [rep], "failed": []})

        _print_failure_reports(tr)

        captured = capsys.readouterr()
        assert "ERROR IN test.py:" in captured.out
        assert "Some error" in captured.out

    def test_report_with_multiple_sections(self, capsys):
        """Reports with multiple sections should print all of them."""
        rep = _make_mock_report(
            nodeid="test.py",
            longrepr="Failure",
            sections=[
                ("Captured stdout call", "stdout content"),
                ("Captured stderr call", "stderr content"),
            ],
        )
        tr = _make_mock_terminal_reporter({"failed": [rep], "error": []})

        _print_failure_reports(tr)

        captured = capsys.readouterr()
        assert "--- Captured stdout call ---" in captured.out
        assert "stdout content" in captured.out
        assert "--- Captured stderr call ---" in captured.out
        assert "stderr content" in captured.out
