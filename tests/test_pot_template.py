# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""Validate the gettext template (po/io.github.d3msudo.anura.pot).

`msgfmt -c` is the wrong check for a *template*: its header check
(`--check-header`) rejects the placeholder header that xgettext always writes
(`Plural-Forms: nplurals=INTEGER; plural=EXPRESSION;`, `PACKAGE VERSION`, ...),
so it reports "invalid nplurals value" / "found 2 fatal errors" even on a
freshly generated, correct template. That check belongs to the translated
`.po` files, where the header is filled in (all of them pass it).

These tests run what does apply to a template: it must parse without errors
(this also catches duplicate definitions), it must contain no duplicate
msgids, and the strings of the History feature must actually be extracted.
Format-string consistency is deliberately not claimed here: msgfmt compares
msgid and msgstr, and every msgstr in a template is empty, so that check only
has something to verify in the `.po` files.

The gettext tools are external, so the tests skip when they are not installed.
"""

import ast
from pathlib import Path
import shutil
import subprocess

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
POT_FILE = PROJECT_ROOT / "po" / "io.github.d3msudo.anura.pot"

# Sources whose translatable strings must be present in the template.
HISTORY_SOURCES = (
    PROJECT_ROOT / "anura" / "controllers" / "history_controller.py",
    PROJECT_ROOT / "anura" / "widgets" / "history_page.py",
)


def _require_tool(name: str) -> str:
    path = shutil.which(name)
    if path is None:
        pytest.skip(f"gettext tool '{name}' not installed")
    return path


def _translatable_literals(source: Path) -> set[str]:
    """String literals passed directly to `_()` in a Python source file."""
    tree = ast.parse(source.read_text(encoding="utf-8"))
    found: set[str] = set()
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "_"
            and len(node.args) == 1
            and isinstance(node.args[0], ast.Constant)
            and isinstance(node.args[0].value, str)
        ):
            found.add(node.args[0].value)
    return found


def _as_msgid_line(text: str) -> str:
    escaped = text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    return f'msgid "{escaped}"'


def test_template_exists():
    assert POT_FILE.is_file(), f"missing gettext template: {POT_FILE}"


def test_template_parses_without_errors():
    """Syntax and duplicate-definition errors (not `-c`, see module docstring)."""
    msgfmt = _require_tool("msgfmt")

    result = subprocess.run(
        [msgfmt, "--check-format", "--check-domain", "-o", "/dev/null", str(POT_FILE)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr


def test_template_has_no_duplicate_msgids():
    msguniq = _require_tool("msguniq")

    result = subprocess.run(
        [msguniq, "--repeated", str(POT_FILE)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "", f"duplicate msgids in template:\n{result.stdout}"


@pytest.mark.parametrize("source", HISTORY_SOURCES, ids=lambda p: p.name)
def test_history_strings_are_in_the_template(source):
    """Regression: a new `_("...")` in the History code must reach the template."""
    msgcat = _require_tool("msgcat")
    unwrapped = subprocess.run(
        [msgcat, "--no-wrap", str(POT_FILE)],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()
    template_msgids = {line for line in unwrapped if line.startswith("msgid ")}

    literals = _translatable_literals(source)
    assert literals, f"expected translatable strings in {source.name}"

    missing = sorted(text for text in literals if _as_msgid_line(text) not in template_msgids)
    assert not missing, f"strings of {source.name} missing from the template: {missing}"
