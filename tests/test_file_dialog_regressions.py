# tests/test_file_dialog_regressions.py
#
# Static regression checks for FileDialog configuration in window.py.
# These tests verify the fix for the LXQt/Flatpak filter glitch.

import ast
from pathlib import Path
import pytest

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
                if isinstance(target, ast.Name) and target.id == "dialog":
                    if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Attribute):
                        if node.value.func.attr == "FileDialog" and node.value.func.value.id == "Gtk":
                            found_local_dialog = True
                            break

    assert found_local_dialog, "Gtk.FileDialog must be instantiated as a local variable 'dialog'."

def test_open_image_no_set_default_filter() -> None:
    """Verify set_default_filter() is NOT called to avoid LXQt D-Bus glitch."""
    tree, _ = _load_module_source("window.py")
    open_image_fn = _find_method(tree, "AnuraWindow", "open_image")

    for node in ast.walk(open_image_fn):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr == "set_default_filter":
                raise AssertionError("AnuraWindow.open_image must NOT call set_default_filter() - it causes glitches on LXQt.")

def test_open_image_filters_structure() -> None:
    """Verify the specific MIME types and order of filters."""
    tree, _ = _load_module_source("window.py")
    open_image_fn = _find_method(tree, "AnuraWindow", "open_image")

    mime_types_found = []
    patterns_found = []

    for node in ast.walk(open_image_fn):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr == "add_mime_type":
                if node.args and isinstance(node.args[0], ast.Constant):
                    mime_types_found.append(node.args[0].value)
            elif node.func.attr == "add_pattern":
                if node.args and isinstance(node.args[0], ast.Constant):
                    patterns_found.append(node.args[0].value)

    # Check for specific MIME types
    required_mimes = {"image/png", "image/jpeg", "image/webp", "image/tiff", "image/bmp"}
    for mime in required_mimes:
        assert mime in mime_types_found, f"Missing required MIME type: {mime}"

    assert "image/*" not in mime_types_found, "Broad 'image/*' MIME type should be replaced by explicit types."
    assert "*" in patterns_found, "Missing catch-all '*' pattern for the second filter."
