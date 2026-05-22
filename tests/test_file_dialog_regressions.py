# tests/test_file_dialog_regressions.py
#
# Static regression checks for FileDialog configuration in window.py.
# These tests verify the fix for the LXQt/Flatpak filter glitch.

import ast
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ANURA_PKG = PROJECT_ROOT / "anura"


def _load_module_source(rel_path: str) -> tuple[ast.Module, str]:
    path = ANURA_PKG / rel_path
    text = path.read_text()
    return ast.parse(text), text


def _find_method(tree: ast.Module, class_name: str, method_name: str) -> ast.FunctionDef:
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == method_name:
                    return item
    raise AssertionError(f"{class_name}.{method_name} not found")


def test_open_image_dialog_is_local() -> None:
    """Verify Gtk.FileDialog is a local variable to prevent filter duplication."""
    tree, _ = _load_module_source("window.py")
    open_image_fn = _find_method(tree, "AnuraWindow", "open_image")

    found_local_dialog = False
    for node in ast.walk(open_image_fn):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if (
                    isinstance(target, ast.Name)
                    and target.id == "dialog"
                    and isinstance(node.value, ast.Call)
                    and isinstance(node.value.func, ast.Attribute)
                    and node.value.func.attr == "FileDialog"
                    and node.value.func.value.id == "Gtk"
                ):
                    found_local_dialog = True
                    break

    assert found_local_dialog, "Gtk.FileDialog must be instantiated as a local variable 'dialog'."


def test_open_image_set_default_filter() -> None:
    """Verify set_default_filter() is called to ensure cumulative filter is selected."""
    tree, _ = _load_module_source("window.py")
    open_image_fn = _find_method(tree, "AnuraWindow", "open_image")

    found_default = False
    for node in ast.walk(open_image_fn):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "set_default_filter"
        ):
            found_default = True
            break
    assert found_default, "AnuraWindow.open_image should call set_default_filter()."


def _find_nested_function_def(open_image_fn: ast.FunctionDef, name: str) -> ast.FunctionDef | None:
    """Find a function definition nested inside open_image."""
    for node in ast.walk(open_image_fn):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    return None


def _collect_add_pattern_nodes(target_fn: ast.FunctionDef) -> dict:
    """Collect all add_pattern / add_suffix / add_mime_type calls."""
    patterns_literal: list[str] = []
    patterns_fstring_count: int = 0
    mime_types_found: list[str] = []
    suffixes_found: list[str] = []

    for node in ast.walk(target_fn):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue

        attr = node.func.attr
        if attr == "add_pattern":
            if node.args and isinstance(node.args[0], ast.Constant):
                patterns_literal.append(node.args[0].value)
            elif node.args and isinstance(node.args[0], ast.JoinedStr):
                patterns_fstring_count += 1
        elif attr == "add_mime_type":
            if node.args and isinstance(node.args[0], (ast.Constant, ast.JoinedStr)):
                mime_types_found.append(node.args[0].value if isinstance(node.args[0], ast.Constant) else "<fstring>")
        elif attr == "add_suffix" and node.args and isinstance(node.args[0], (ast.Constant, ast.JoinedStr)):
            suffixes_found.append(node.args[0].value if isinstance(node.args[0], ast.Constant) else "<fstring>")

    return {
        "patterns_literal": patterns_literal,
        "patterns_fstring_count": patterns_fstring_count,
        "mime_types_found": mime_types_found,
        "suffixes_found": suffixes_found,
    }


def test_open_image_filters_structure() -> None:
    """Verify filters use only add_pattern() with proper extension coverage."""
    tree, _ = _load_module_source("window.py")
    open_image_fn = _find_method(tree, "AnuraWindow", "open_image")

    info = _collect_add_pattern_nodes(open_image_fn)

    # No add_mime_type or add_suffix should be used
    assert not info["mime_types_found"], "add_mime_type() should not be used in open_image()."
    assert not info["suffixes_found"], "add_suffix() should not be used — use add_pattern() instead."

    # Must have the catch-all "*" pattern (literal string)
    assert "*" in info["patterns_literal"], "Missing catch-all '*' pattern for the last filter."

    # Must have a helper function that generates case-insensitive patterns.
    # This is the canonical approach: nested function + add_pattern() calls.
    make_filter_fn = _find_nested_function_def(open_image_fn, "_make_format_filter")
    assert make_filter_fn is not None, (
        "Missing nested helper _make_format_filter(). "
        "Ensure a helper function uses add_pattern() for each extension "
        "(both lowercase and uppercase) inside the open_image() method."
    )

    # The helper must call add_pattern() inside its body.
    helper_info = _collect_add_pattern_nodes(make_filter_fn)
    assert helper_info["patterns_fstring_count"] >= 1 or len(helper_info["patterns_literal"]) >= 1, (
        "The _make_format_filter() helper must call add_pattern() with pattern arguments."
    )

    # Count filters created via _make_format_filter() and the all_img_filter
    # (7 individual format filters + the cumulative all_img_filter)
    make_filter_calls = sum(
        1
        for node in ast.walk(open_image_fn)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "_make_format_filter"
    )
    assert make_filter_calls == 7, (
        f"Expected 7 calls to _make_format_filter() (one per format), got {make_filter_calls}."
    )
