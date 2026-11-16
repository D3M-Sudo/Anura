# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""Tests for deterministic classification of production UI color literals."""

from __future__ import annotations

import importlib
from pathlib import Path

try:
    scanner = importlib.import_module("tests.ui_color_scanner")
except ModuleNotFoundError:
    scanner = None


def _scanner_api():
    assert scanner is not None, "tests.ui_color_scanner must be implemented"
    assert hasattr(scanner, "scan_ui_color_literals")
    assert hasattr(scanner, "find_unclassified_ui_colors")
    return scanner.scan_ui_color_literals, scanner.find_unclassified_ui_colors


def _write(root: Path, relative_path: str, content: str) -> None:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _tuples(findings):
    return {(item.path, item.value, item.syntax) for item in findings}


def test_finds_hex_colors_in_stylesheet_and_blueprint(tmp_path: Path):
    scan, _ = _scanner_api()
    _write(
        tmp_path,
        "data/style.css",
        """
        .one { color: #abc; }
        .two { color: #abcd; }
        .three { color: #112233; }
        .four { color: #11223344; }
        """,
    )
    _write(tmp_path, "data/ui/panel.blp", 'Label { styles: ["custom"]; /* color: #000 */ }\n// #badbad\n')

    findings = scan(tmp_path)
    assert _tuples(findings) == {
        ("data/style.css", "#abc", "hex"),
        ("data/style.css", "#abcd", "hex"),
        ("data/style.css", "#112233", "hex"),
        ("data/style.css", "#11223344", "hex"),
    }


def test_finds_rgb_and_rgba_colors_in_stylesheet(tmp_path: Path):
    scan, _ = _scanner_api()
    _write(
        tmp_path,
        "data/style.css",
        """
        .one { color: rgb(1, 2, 3); }
        .two { color: rgba(10, 20, 30, 0.5); }
        """,
    )

    findings = scan(tmp_path)
    assert _tuples(findings) == {
        ("data/style.css", "rgb(1, 2, 3)", "rgb"),
        ("data/style.css", "rgba(10, 20, 30, 0.5)", "rgba"),
    }


def test_finds_color_literals_in_python_string_constants(tmp_path: Path):
    scan, _ = _scanner_api()
    _write(
        tmp_path,
        "anura/widgets/example.py",
        '''
"""Module documentation mentioning #badbad must not be scanned."""

COLOR = "#123456"


def color_value():
    """A docstring with #abcdef is not a UI color declaration."""
    return "#ABCDEF"
''',
    )

    findings = scan(tmp_path)
    assert _tuples(findings) == {
        ("anura/widgets/example.py", "#123456", "hex"),
        ("anura/widgets/example.py", "#abcdef", "hex"),
    }


def test_ignores_comments_and_non_ui_files(tmp_path: Path):
    scan, _ = _scanner_api()
    _write(
        tmp_path,
        "data/style.css",
        """
        /* #badc0de */
        /* #deadbeef */
        .real { color: #123456; }
        """,
    )
    _write(tmp_path, "data/ui/panel.blp", "// #badc0de\n/* #deadbeef */\nLabel { }\n")
    _write(tmp_path, "anura/widgets/example.py", "# COLOR = '#badc0de'\nCOLOR = '#123456'\n")
    _write(tmp_path, "anura/services/worker.py", "COLOR = '#fedcba'\n")
    _write(tmp_path, "README.md", "Example color: #010203\n")

    findings = scan(tmp_path)
    assert _tuples(findings) == {
        ("data/style.css", "#123456", "hex"),
        ("anura/widgets/example.py", "#123456", "hex"),
    }


def test_ignores_non_color_hash_strings_and_theme_references(tmp_path: Path):
    scan, _ = _scanner_api()
    _write(
        tmp_path,
        "data/style.css",
        """
        .icon { background-image: url("icons.svg#abcdef"); }
        .theme { color: @theme_fg_color; background: @accent_color; border-color: @warning_color; }
        .real { color: #123456; }
        """,
    )
    _write(
        tmp_path,
        "anura/widgets/example.py",
        """
ICON_URL = "resource:///icons.svg#abcdef"
THEME_COLOR = "@theme_fg_color"
COLOR = "#123456"
""",
    )

    findings = scan(tmp_path)
    assert _tuples(findings) == {
        ("data/style.css", "#123456", "hex"),
        ("anura/widgets/example.py", "#123456", "hex"),
    }


def test_approved_literal_requires_path_and_semantic_rationale(tmp_path: Path):
    scan, unclassified = _scanner_api()
    _write(tmp_path, "data/style.css", ".approved { color: #123456; }\n")
    _write(tmp_path, "data/ui/other.blp", 'Label { color: "#123456"; }\n')

    findings = scan(tmp_path)
    approved = {("data/style.css", "#123456"): "brand graphical accent"}
    remaining = unclassified(findings, approved)

    assert {(item.path, item.value) for item in remaining} == {("data/ui/other.blp", "#123456")}


def test_unclassified_fixture_reports_path_line_and_literal(tmp_path: Path):
    scan, unclassified = _scanner_api()
    _write(tmp_path, "data/style.css", ".first { color: #123456; }\n.second { color: #abcdef; }\n")

    findings = scan(tmp_path)
    remaining = unclassified(findings, {("data/style.css", "#123456"): "approved accent"})

    assert len(remaining) == 1
    assert remaining[0].path == "data/style.css"
    assert remaining[0].line == 2
    assert remaining[0].value == "#abcdef"


def test_scanner_discovers_new_files_without_updating_a_file_list(tmp_path: Path):
    scan, _ = _scanner_api()
    _write(tmp_path, "anura/widgets/first.py", 'COLOR = "#123456"\n')
    first = scan(tmp_path)
    _write(tmp_path, "anura/widgets/nested/new_widget.py", 'COLOR = "#abcdef"\n')
    second = scan(tmp_path)

    assert {item.path for item in first} == {"anura/widgets/first.py"}
    assert {item.path for item in second} == {
        "anura/widgets/first.py",
        "anura/widgets/nested/new_widget.py",
    }

def test_repository_ui_colors_are_classified():
    scan, unclassified = _scanner_api()
    repository_root = Path(__file__).resolve().parents[1]
    approved = {
        ("data/style.css", "#16a36a"): "Brand green graphical accent, reserved for non-text emphasis.",
        ("data/style.css", "#0f7650"): "Dark green brand surface and light-scheme status text.",
        ("data/style.css", "#ffffff"): "Foreground text on the dark suggested-action surface.",
        ("data/style.css", "#21b77a"): "Light green status and focus accent on dark surfaces.",
        ("data/style.css", "rgba(0, 0, 0, 0.15)"): "Subtle shadow for button hover elevation.",
        ("data/style.css", "rgba(0, 0, 0, 0.1)"): "Subtle shadow for active button feedback.",
        ("data/style.css", "rgba(0, 0, 0, 0.12)"): "Subtle shadow for card hover elevation.",
    }

    findings = scan(repository_root)
    remaining = unclassified(findings, approved)
    details = "\\n".join(
        f"{item.path}:{item.line}: {item.value} ({item.syntax})" for item in remaining
    )

    assert not remaining, f"Unclassified production UI color literals:\\n{details}"

