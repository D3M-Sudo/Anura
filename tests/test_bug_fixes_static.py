# This file is part of Anura.
# Copyright (C) 2022-2025 Andrey Maksimov (Frog)
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

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
    assert "active-language" in text, "ExtractedPage.listen() must read the OCR language from GSettings."


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
    assert "html.escape" in text, "Bare text fallback must be HTML-escaped before wrapping in <p>."


# ---------------------------------------------------------------------------
# Bug C: when the host portal returns G_IO_ERROR_FAILED with the generic
# "Screenshot failed" string (i.e. no screenshot-capable XDG backend is
# installed for the active desktop), surface an actionable hint to the user
# AND keep the diagnostic logger.error with domain/code/message.
# ---------------------------------------------------------------------------


def test_screenshot_service_logs_full_diagnostic_context() -> None:
    _tree, text = _load_module_source("services/screenshot/portal_provider.py")
    assert "domain={e.domain}" in text and "code={e.code}" in text, (
        "logger.error in take_screenshot_finish must include {e.domain} and "
        "{e.code} so the user/log analysis can identify the failing portal layer.",
    )


def test_screenshot_service_detects_generic_backend_failure() -> None:
    _tree, text = _load_module_source("services/screenshot/portal_provider.py")
    assert "Gio.IOErrorEnum.FAILED" in text, (
        "ScreenshotService must explicitly match Gio.IOErrorEnum.FAILED to "
        "detect the libportal generic-failure pattern."
    )
    assert "screenshot failed" in text.lower(), (
        "ScreenshotService must check the libportal 'Screenshot failed' "
        "message to recognise the generic backend-rejection case."
    )
    assert "xdg-desktop-portal" in text, (
        "User-facing message must guide the user to install a working xdg-desktop-portal backend.",
    )


# ---------------------------------------------------------------------------
# Persistent install-hint banner: ScreenshotService now also emits a
# "portal-backend-missing" signal when the libportal generic-failure pattern
# is detected, and AnuraWindow reveals an Adw.Banner from window.blp on
# receiving it. This pair-of-tests is the static guard for that wiring.
# ---------------------------------------------------------------------------


def test_screenshot_service_declares_portal_backend_missing_signal() -> None:
    _tree, text = _load_module_source("services/screenshot_service.py")
    assert '"portal-backend-missing"' in text, (
        "ScreenshotService.__gsignals__ must declare the 'portal-backend-missing' "
        "signal so consumers can react to a missing host portal backend."
    )
    # And the signal must be emitted in the generic-backend-failure branch.
    assert 'self.emit("portal-backend-missing")' in text, (
        "ScreenshotService must emit 'portal-backend-missing' (via GLib.idle_add) "
        "when it detects the libportal generic-failure pattern."
    )


def test_window_wires_portal_banner_and_signal_handler() -> None:
    text = (PROJECT_ROOT / "anura" / "window.py").read_text()
    ocr_text = (PROJECT_ROOT / "anura" / "controllers" / "ocr_controller.py").read_text()
    combined_text = text + ocr_text

    assert "portal_banner: Adw.Banner = Gtk.Template.Child()" in text, (
        "AnuraWindow must declare portal_banner as a Gtk.Template.Child mapping to the Adw.Banner in window.blp."
    )
    assert '"portal-backend-missing"' in combined_text, (
        "OcrController must connect to the new ScreenshotService signal."
    )
    assert "set_revealed(True)" in combined_text and "set_revealed(False)" in combined_text, (
        "OcrController must reveal the banner on the signal and hide it when the user dismisses it."
    )


def test_window_blp_contains_adw_banner() -> None:
    blp = (PROJECT_ROOT / "data" / "ui" / "window.blp").read_text()
    assert "Adw.Banner portal_banner" in blp, (
        "window.blp must declare an Adw.Banner with id 'portal_banner' so the Python template binding has a target."
    )
    # Banner must start hidden — only revealed when a screenshot fails with
    # the libportal generic-failure pattern.
    assert "revealed: false" in blp, "Banner must be hidden by default."


# ---------------------------------------------------------------------------
# Security: LanguageManager.remove_language() must validate the language code
# to prevent path traversal attacks.
# ---------------------------------------------------------------------------


def test_language_manager_remove_language_validates_code() -> None:
    """LanguageManager.remove_language must validate the input code against
    LANG_CODE_PATTERN to prevent path traversal."""
    tree, _ = _load_module_source("services/language_manager.py")
    remove_fn = _find_method(tree, "LanguageManager", "remove_language")

    found_validation = False
    for node in ast.walk(remove_fn):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "match"
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "re"
        ):
            # Check if LANG_CODE_PATTERN is passed to re.match
            for arg in node.args:
                if isinstance(arg, ast.Name) and arg.id == "LANG_CODE_PATTERN":
                    found_validation = True
                    break
    assert found_validation, (
        "LanguageManager.remove_language() must validate the code against "
        "LANG_CODE_PATTERN to prevent path traversal attacks."
    )


def test_metainfo_documents_portal_requirement() -> None:
    metainfo = (PROJECT_ROOT / "data" / "io.github.d3msudo.anura.metainfo.xml.in").read_text()
    assert "xdg-desktop-portal" in metainfo, (
        "metainfo.xml.in must document the portal backend requirement so Flathub users see it before installing."
    )


def test_readme_documents_runtime_requirements() -> None:
    readme = (PROJECT_ROOT / "README.md").read_text()
    assert "Runtime requirements" in readme, (
        "README must contain a 'Runtime requirements' section explaining the xdg-desktop-portal backend dependency."
    )
    assert "xdg-desktop-portal-gtk" in readme, "README must mention xdg-desktop-portal-gtk explicitly for LXQt users."


# ---------------------------------------------------------------------------
# Bug D: ExtractedPage share service signal handler must be disconnected in
# do_dispose to prevent memory leak
# ---------------------------------------------------------------------------


def test_extracted_page_disconnects_share_service_signal() -> None:
    """ExtractedPage.do_dispose must disconnect the share service signal handler."""
    text = (ANURA_PKG / "widgets" / "extracted_page.py").read_text()
    # Check that do_dispose contains disconnect for share service
    assert "self._share_service.disconnect(self._share_handler_id)" in text, (
        "ExtractedPage.do_dispose must disconnect the share service signal handler "
        "(_share_handler_id) to prevent memory leaks."
    )


def test_extracted_page_tracks_share_handler_id() -> None:
    """ExtractedPage must track the share service handler ID for cleanup."""
    text = (ANURA_PKG / "widgets" / "extracted_page.py").read_text()
    assert "_share_handler_id" in text, (
        "ExtractedPage must track the share service signal handler ID (_share_handler_id) for cleanup in do_dispose."
    )
    assert "_share_handler_id = self._share_service.connect" in text, (
        "ExtractedPage must store the share service connect() return value in _share_handler_id."
    )


# ---------------------------------------------------------------------------
# Bug E: AnuraWindow portal_banner signal handler must be disconnected in
# do_destroy to prevent memory leak
# ---------------------------------------------------------------------------


def test_window_disconnects_portal_banner_signal() -> None:
    """AnuraWindow.do_destroy must disconnect the portal_banner signal handler."""
    text = (ANURA_PKG / "window.py").read_text()
    # Check that do_destroy contains disconnect for portal_banner
    # Since Issue 4 refactor, we use SignalManagerMixin for automated cleanup.
    assert (
        "self.portal_banner.disconnect(handler_id)" in text
        or "self.portal_banner.disconnect(self._handler_portal_banner)" in text
        or "self.disconnect_all_signals()" in text
        or "self.teardown_all()" in text
    ), "AnuraWindow.do_destroy must disconnect signals to prevent memory leaks."


def test_window_tracks_portal_banner_handler_id() -> None:
    """OcrController must track the portal_banner handler ID for cleanup."""
    text = (ANURA_PKG / "window.py").read_text()
    ocr_text = (PROJECT_ROOT / "anura" / "controllers" / "ocr_controller.py").read_text()
    combined_text = text + ocr_text

    # Accept either manual tracking or SignalManagerMixin's connect_tracked
    assert "_handler_portal_banner" in combined_text or "connect_tracked" in ocr_text, (
        "OcrController must track the portal_banner signal handler for cleanup."
    )


# ---------------------------------------------------------------------------
# Security: AnuraWindow.process_file() must use os.path.getsize() which
# follows symlinks, instead of os.lstat() which doesn't, to correctly
# enforce the 50MB file size limit.
# ---------------------------------------------------------------------------


def test_window_process_file_uses_validate_image_resource() -> None:
    """AnuraWindow.process_file must use validate_image_resource() for size validation."""
    tree, _ = _load_module_source("window.py")
    process_file_fn = _find_method(tree, "AnuraWindow", "process_file")

    found_validation = False
    for node in ast.walk(process_file_fn):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "validate_image_resource":
            found_validation = True
            break
    assert found_validation, (
        "AnuraWindow.process_file() must use validate_image_resource() "
        "to correctly validate the actual file size and properties."
    )


@pytest.mark.parametrize(
    "rel_path",
    [
        "widgets/extracted_page.py",
        "widgets/welcome_page.py",
        "main.py",
        "services/screenshot_service.py",
        "window.py",
    ],
)
def test_modules_parse_cleanly(rel_path: str) -> None:
    """Sanity: each modified module must still be syntactically valid."""
    ast.parse((ANURA_PKG / rel_path).read_text())
