# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""Deterministic scanner for hardcoded color literals in production UI sources."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

import ast
import re


@dataclass(frozen=True, slots=True)
class ColorLiteral:
    """A color literal found in a production UI source file."""

    path: str
    value: str
    line: int
    syntax: str


_HEX_RE = re.compile(r"(?<![\w/:#])#[0-9a-fA-F]{8}|(?<![\w/:#])#[0-9a-fA-F]{6}|(?<![\w/:#])#[0-9a-fA-F]{4}|(?<![\w/:#])#[0-9a-fA-F]{3}(?![\w])")
_RGB_RE = re.compile(
    r"(?i)\brgb\(\s*(?:\d+(?:\.\d+)?%?\s*,\s*){2}\d+(?:\.\d+)?%?\s*\)"
)
_RGBA_RE = re.compile(
    r"(?i)\brgba\(\s*(?:\d+(?:\.\d+)?%?\s*,\s*){3}\d+(?:\.\d+)?%?\s*\)"
)


def _strip_css_comments(source: str) -> str:
    """Remove CSS block comments while preserving line numbers."""

    return re.sub(
        r"/\*.*?\*/",
        lambda match: "".join("\n" if char == "\n" else " " for char in match.group()),
        source,
        flags=re.DOTALL,
    )


def _strip_blueprint_comments(source: str) -> str:
    """Remove Blueprint line and block comments while preserving line numbers."""

    source = _strip_css_comments(source)
    return re.sub(r"//[^\n]*", lambda match: " " * len(match.group()), source)


def _python_string_literals(source: str) -> list[tuple[str, int]]:
    """Return non-docstring Python string constants and their source lines."""

    tree = ast.parse(source)
    docstring_nodes: set[int] = set()

    def mark_docstring(body: list[ast.stmt]) -> None:
        if body and isinstance(body[0], ast.Expr):
            value = body[0].value
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                docstring_nodes.add(id(value))

    mark_docstring(tree.body)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            mark_docstring(node.body)

    literals: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and id(node) not in docstring_nodes
        ):
            literals.append((node.value, node.lineno))
    return literals


def _scan_text(path: str, source: str, syntax: str) -> list[ColorLiteral]:
    findings: list[ColorLiteral] = []
    for line_number, line in enumerate(source.splitlines(), start=1):
        for match in _HEX_RE.finditer(line):
            findings.append(
                ColorLiteral(path, match.group().lower(), line_number, "hex")
            )
        for kind, pattern in (("rgb", _RGB_RE), ("rgba", _RGBA_RE)):
            for match in pattern.finditer(line):
                findings.append(
                    ColorLiteral(path, re.sub(r"\s+", " ", match.group()), line_number, kind)
                )
    return findings


def _scan_python(path: str, source: str) -> list[ColorLiteral]:
    findings: list[ColorLiteral] = []
    for value, start_line in _python_string_literals(source):
        for offset, line in enumerate(value.splitlines() or [value]):
            for match in _HEX_RE.finditer(line):
                findings.append(
                    ColorLiteral(path, match.group().lower(), start_line + offset, "hex")
                )
            for kind, pattern in (("rgb", _RGB_RE), ("rgba", _RGBA_RE)):
                for match in pattern.finditer(line):
                    findings.append(
                        ColorLiteral(
                            path,
                            re.sub(r"\s+", " ", match.group()),
                            start_line + offset,
                            kind,
                        )
                    )
    return findings


def scan_ui_color_literals(root: Path) -> list[ColorLiteral]:
    """Find color literals in the declared production UI source scope."""

    root = Path(root)
    candidates: set[Path] = set()
    stylesheet = root / "data/style.css"
    if stylesheet.is_file():
        candidates.add(stylesheet)

    ui_directory = root / "data/ui"
    if ui_directory.is_dir():
        candidates.update(ui_directory.rglob("*.blp"))

    widget_directory = root / "anura/widgets"
    if widget_directory.is_dir():
        candidates.update(widget_directory.rglob("*.py"))

    for relative in ("anura/window.py", "anura/main.py"):
        path = root / relative
        if path.is_file():
            candidates.add(path)

    findings: list[ColorLiteral] = []
    for path in sorted(candidates):
        relative_path = path.relative_to(root).as_posix()
        source = path.read_text(encoding="utf-8")
        if path.suffix == ".py":
            findings.extend(_scan_python(relative_path, source))
        elif path.suffix == ".blp":
            findings.extend(
                _scan_text(
                    relative_path,
                    _strip_blueprint_comments(source),
                    "blueprint",
                )
            )
        else:
            findings.extend(
                _scan_text(relative_path, _strip_css_comments(source), "css")
            )

    return sorted(
        findings,
        key=lambda item: (item.path, item.line, item.value, item.syntax),
    )


def find_unclassified_ui_colors(
    findings: Sequence[ColorLiteral],
    approved: Mapping[tuple[str, str], str],
) -> list[ColorLiteral]:
    """Return findings without a path-specific, non-empty semantic rationale."""

    return [
        finding
        for finding in findings
        if not approved.get((finding.path, finding.value), "").strip()
    ]
