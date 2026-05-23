# This file is part of Anura.
# Copyright (C) 2022-2025 Andrey Maksimov (Frog)
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

from collections.abc import Callable
import contextlib
import ipaddress
import re
import unicodedata
from urllib.parse import urlparse

from loguru import logger

# Pre-compiled regex for control characters (0x00-0x1F) and DEL (0x7F)
# Using a regex is ~13x faster than a manual loop for control character detection.
_CONTROL_CHARS_RE = re.compile(r"[\x00-\x1f\x7f]")


def sanitize_text(text: str) -> str:
    """
    Sanitize text using heuristics to correct common OCR errors and remove artifacts.
    Also strips dangerous control and format characters to prevent terminal injection
    and spoofing attacks.
    """
    if not text:
        return ""

    # 1. Defense-in-depth: Strip non-printable Unicode Control (Cc) and Format (Cf)
    # characters, but preserve legitimate formatting like \n, \r, and \t.
    # This prevents Null byte injection, Bell characters, and RTL override spoofing.
    text = "".join(
        ch
        for ch in text
        if unicodedata.category(ch) not in ("Cc", "Cf") or ch in "\n\r\t"
    )

    # 2. Normalize horizontal whitespace (squash multiple spaces/tabs)
    # Note: \n and \r are preserved by the [ \t]+ pattern.
    text = re.sub(r"[ \t]+", " ", text)

    # 3. Fix common OCR mistakes in URLs/Emails if they look like them
    # e.g. "http: //" -> "http://"
    text = re.sub(r"(https?|ftp|file):\s+/{2}", r"\1://", text)

    return text.strip()

def is_safe_url_string(text: str) -> bool:
    """
    Perform fundamental security checks on a URL string.
    Checks for length, control characters, and ASCII-only characters.
    """
    if text is None:
        return False

    # Defense-in-depth: limit URL length BEFORE processing
    if len(text) > 2048:
        return False

    # Block control characters (0x00-0x1F) and DEL (0x7F) BEFORE strip/sanitize
    # to catch malicious trailing characters.
    if _CONTROL_CHARS_RE.search(text):
        return False

    # Clean and normalize text using heuristics
    text = sanitize_text(text)

    # Ensure URL is ASCII-only (prevent Unicode homograph attacks).
    return text.isascii()


def uri_validator(text: str) -> bool:
    """
    Centralized URI validation for Anura OCR.

    Validates URLs to prevent:
    - Control character injection (0x00-0x1F, 0x7F)
    - Unicode homograph attacks
    - Invalid URL schemes
    - Single-word hostnames without dots

    Args:
        text: The URL string to validate.

    Returns:
        True if the URL is safe to use, False otherwise.
    """
    if not is_safe_url_string(text):
        return False

    url = text.strip()

    try:
        res = urlparse(url)
        if not (res.scheme in ("http", "https") and bool(res.netloc)):
            return False

        # Security: Reject URLs with userinfo (username or password)
        # This prevents spoofing attacks like http://google.com@evil.com
        if res.username or res.password:
            return False

        # Use hostname for validation (excludes port and userinfo)
        host = res.hostname
        if not host:
            return False

        # Allow localhost and IP addresses (common in development/enterprise)
        # Also allow hostnames with dots (normal domains)
        host_lower = host.lower()
        if host_lower == "localhost":
            return True
        if "." in host:
            return True

        # Check for valid IP address (IPv4 or IPv6)
        # res.hostname handles unbracketing IPv6
        with contextlib.suppress(ValueError):
            ipaddress.ip_address(host)
            return True

        # Reject single-word hostnames without dots (prevents "http://evil")
        return False
    except ValueError:
        return False

def launch_uri(window: object | None, url: str, error_callback: Callable | None = None) -> None:
    """
    Centralized URI launcher with security validation and error handling.

    Args:
        window: The parent window (Gtk.Window) for the launcher and error dialogs.
        url: The URL to launch.
        error_callback: Optional callback for error messages.
    """
    url = url.strip() if url else ""
    if not uri_validator(url):
        logger.warning(f"Anura Security: Blocked invalid URL launch: {url}")
        if error_callback:
            error_callback("Invalid URL blocked for security")
        return

    import gi

    gi.require_version("Gtk", "4.0")
    from gi.repository import Gio, GLib, Gtk

    launcher = Gtk.UriLauncher.new(url)

    def on_launch_finish(_launcher: object, result: Gio.AsyncResult) -> None:
        try:
            launcher.launch_finish(result)
        except GLib.Error as e:
            logger.error(f"Anura: Failed to launch URI: {e.message}")
            if error_callback:
                error_callback("Failed to open link")

    launcher.launch(window, None, on_launch_finish)
