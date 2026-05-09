# test_bug_fixes_static.py
#
# Static (AST / source-text) regression checks for the bug fixes that follow
# PR #25. These tests do NOT import GTK / Xdp / GStreamer (which are unavailable
# on the host CI runner outside the Flatpak sandbox). Instead they parse the
# source files and verify the structural invariants that prevent each bug from
# regressing.

import ast
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ANURA_PKG = PROJECT_ROOT / "anura"


def _load_module_source(rel_path: str) -> tuple[ast.Module, str]:
    path = ANURA_PKG / rel_path
    text = path.read_text()
    return ast.parse(text), text


# ---------------------------------------------------------------------------
# Bug B: ExtractedPage.listen() must NOT call self.get_language() — that
# attribute lives on AnuraWindow, not on ExtractedPage. The previous code
# raised AttributeError as soon as the user clicked the Listen button.
# ---------------------------------------------------------------------------


def _find_method(tree: ast.Module, class_name: str, method_name: str) -> ast.FunctionDef:
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == method_name:
                    return item
    raise AssertionError(f"{class_name}.{method_name} not found")


def test_extracted_page_listen_does_not_call_self_get_language() -> None:
    tree, _ = _load_module_source("widgets/extracted_page.py")
    listen_fn = _find_method(tree, "ExtractedPage", "listen")
    for node in ast.walk(listen_fn):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            is_self = isinstance(node.func.value, ast.Name) and node.func.value.id == "self"
            if is_self and node.func.attr == "get_language":
                raise AssertionError(
                    "ExtractedPage.listen() must not call self.get_language() — "
                    "that method only exists on AnuraWindow.",
                )


def test_extracted_page_listen_uses_tts_effective_language() -> None:
    """Resolve the gTTS code via TTSService.get_effective_language() so the
    Tesseract→ISO 639-1 mapping (e.g. 'ita'→'it') and the user's tts-language
    override are both honoured."""
    _tree, text = _load_module_source("widgets/extracted_page.py")
    assert "get_effective_language(" in text, (
        "ExtractedPage.listen() must call get_effective_language() to resolve "
        "the TTS language code from the OCR setting."
    )
    assert "active-language" in text, (
        "ExtractedPage.listen() must read the OCR language from GSettings."
    )


# ---------------------------------------------------------------------------
# Bug A safety net: AnuraApplication._get_release_notes() must wrap bare-text
# fallbacks in <p>...</p> so Adw.AboutDialog (libxml) accepts them.
# ---------------------------------------------------------------------------


def test_get_release_notes_wraps_bare_text() -> None:
    _tree, text = _load_module_source("main.py")
    # The function must guard against output that does not start with an XML element.
    assert 'startswith("<")' in text, (
        "_get_release_notes must check that returned markup starts with '<' to "
        "avoid the libxml 'document must start with an element' error."
    )
    assert "html.escape" in text, (
        "Bare text fallback must be HTML-escaped before wrapping in <p>."
    )


# ---------------------------------------------------------------------------
# Bug C: when the host portal returns G_IO_ERROR_FAILED with the generic
# "Screenshot failed" string (i.e. no screenshot-capable XDG backend is
# installed for the active desktop), surface an actionable hint to the user
# AND keep the diagnostic logger.error with domain/code/message.
# ---------------------------------------------------------------------------


def test_screenshot_service_logs_full_diagnostic_context() -> None:
    _tree, text = _load_module_source("services/screenshot_service.py")
    assert "domain={e.domain}" in text and "code={e.code}" in text, (
        "logger.error in take_screenshot_finish must include {e.domain} and "
        "{e.code} so the user/log analysis can identify the failing portal layer.",
    )


def test_screenshot_service_detects_generic_backend_failure() -> None:
    _tree, text = _load_module_source("services/screenshot_service.py")
    assert "Gio.IOErrorEnum.FAILED" in text, (
        "ScreenshotService must explicitly match Gio.IOErrorEnum.FAILED to "
        "detect the libportal generic-failure pattern."
    )
    assert "screenshot failed" in text.lower(), (
        "ScreenshotService must check the libportal 'Screenshot failed' "
        "message to recognise the generic backend-rejection case."
    )
    assert "xdg-desktop-portal" in text, (
        "User-facing message must guide the user to install a working "
        "xdg-desktop-portal backend.",
    )


@pytest.mark.parametrize(
    "rel_path",
    [
        "widgets/extracted_page.py",
        "main.py",
        "services/screenshot_service.py",
    ],
)
def test_modules_parse_cleanly(rel_path: str) -> None:
    """Sanity: each modified module must still be syntactically valid."""
    ast.parse((ANURA_PKG / rel_path).read_text())
