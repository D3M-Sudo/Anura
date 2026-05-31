# This file is part of Anura.
# Copyright (C) 2022-2025 Andrey Maksimov (Frog)
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import contextlib
import ipaddress
import os
from pathlib import Path
import re
import unicodedata
from urllib.parse import urlparse

from loguru import logger

from anura.config import MAX_IMAGE_SIZE_BYTES, MAX_IMAGE_SIZE_MB

# Pre-compiled regex for C0 control characters (0x00-0x1F) and DEL (0x7F).
# Note: C1 controls (0x80-0x9F) are handled by is_safe_url_string's isascii() check.
# Using a regex is ~13x faster than a manual loop for control character detection.
_CONTROL_CHARS_RE = re.compile(r"[\x00-\x1f\x7f]")

# Centralized patterns for structured data detection (URLs, Emails, etc.)
# Used across TextPreprocessor, Transformers, and ResultDispatcher.
EMAIL_PATTERN = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,15}"
URL_PATTERN = (
    r"(?:(?:https?|ftp|file):\/\/|www\.)"
    r"(?:\([-A-Z0-9+&@#\/%=~_|$?!:,.]*\)|[-A-Z0-9+&@#\/%=~_|$?!:,.])*"
    r"(?:\([-A-Z0-9+&@#\/%=~_|$?!:,.]*\)|[A-Z0-9+&@#\/%=~_|$])"
)

# Regex objects for performance
EMAIL_RE = re.compile(EMAIL_PATTERN, re.IGNORECASE)
URL_RE = re.compile(URL_PATTERN, re.IGNORECASE)


def sanitize_text(text: str) -> str:
    """
    Sanitize text using heuristics to correct common OCR errors and remove artifacts.
    Also strips dangerous control and format characters to prevent terminal injection
    and spoofing attacks.
    """
    if not text:
        return ""

    # 1. Defense-in-depth: Strip non-printable Unicode Control (Cc), Format (Cf),
    # Private Use (Co), and Surrogate (Cs) characters, but preserve legitimate
    # formatting like \n, \r, and \t.
    # This prevents Null byte injection, Bell characters, RTL override spoofing,
    # and obfuscation using private-use or surrogate characters.
    text = "".join(
        ch for ch in text if unicodedata.category(ch) not in ("Cc", "Cf", "Co", "Cs") or ch in "\n\r\t"
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
    if not isinstance(text, str):
        return False

    # 1. Defense-in-depth: limit URL length BEFORE processing (standard limit)
    if len(text) > 2000:
        return False

    # 2. Security: Block backslashes to prevent URL spoofing and bypasses.
    # Browsers often normalize \ to / which can lead to parsing discrepancies.
    if "\\" in text:
        return False

    # 3. Homograph detection (BUG-034): If the hostname mixes ASCII Latin letters with
    # non-ASCII characters, reject the URL. This prevents homograph attacks
    # (e.g. mixing 'a' and 'cyrillic-a').
    try:
        from urllib.parse import urlparse
        parsed_for_homograph = urlparse(text)
        hostname = parsed_for_homograph.hostname or ""

        # Defense-in-depth: If urlparse fails to identify a hostname but the
        # string looks like it has one (e.g. 'https://goog\u0430le.com'),
        # we reject it as malformed/potentially malicious.
        if not hostname and "://" in text:
            return False

        if hostname and not hostname.isascii():
            # Check for mixed-script labels. We iterate through DNS labels
            # to be more precise than checking the whole hostname at once.
            for label in hostname.split("."):
                if not label or label.isascii():
                    continue

                # If the label contains both ASCII alphanumeric and non-ASCII, it's a high-risk mixed script.
                has_ascii = any(ch.isascii() and ch.isalnum() for ch in label)
                if has_ascii:
                    # Whitelist: Latin-1 Supplement (0x00A0-0x00FF) is generally safe
                    # (e.g. German umlauts like 'münchen.de') but we still block
                    # mixing them with ASCII in a single label if they are used
                    # for spoofing. However, standard IDN rules allow Latin-1 + ASCII.
                    # We block Cyrillic, Greek, Armenian, Hebrew, etc. if mixed with ASCII.
                    for ch in label:
                        cp = ord(ch)
                        if cp > 0x7F and not (0x00A0 <= cp <= 0x00FF):
                            # Reject if outside Latin-1 Supplement but mixed with ASCII
                            return False
                else:
                    # Pure non-ASCII label (e.g. '中文'): check for suspicious scripts
                    # commonly used in homograph attacks.
                    for ch in label:
                        cp = ord(ch)
                        # Block Cyrillic (0x0400-0x052F) and Greek (0x0370-0x03FF)
                        # if the overall hostname also contains ASCII labels (e.g. 'goog\u0430.com')
                        if (0x0400 <= cp <= 0x052F or 0x0370 <= cp <= 0x03FF) and hostname.isascii() is False:
                            # If hostname is not pure ASCII, we allow these scripts
                            # ONLY if the entire hostname uses them (pure IDN).
                            # If there's ANY ASCII label elsewhere, we block.
                            any_ascii_label = any(
                                part.isascii() and any(c.isalpha() for c in part) for part in hostname.split(".")
                            )
                            if any_ascii_label:
                                return False

    except (ValueError, AttributeError, TypeError):
        # Malformed URL parsing - treat as unsafe
        return False

    # 4. IDN normalization: convert international domain names (IDN) to their
    # Punycode ASCII-compatible encoding (ACE) before the ASCII safety check.
    # This allows legitimate URLs like https://münchen.de or https://中文.com
    # while still rejecting homograph attacks — Punycode is always ASCII, so
    # the isascii() check below still catches unencoded non-ASCII that isn't
    # a valid hostname label (e.g. invisible Unicode in the path/query).
    if not text.isascii():
        try:
            from urllib.parse import urlunparse
            # urlparse already available from homograph check scope
            parsed = urlparse(text)
            if parsed.hostname and not parsed.hostname.isascii():
                # Encode each DNS label separately; skip empty labels (leading dots etc.)
                punycode_labels = []
                for label in parsed.hostname.split("."):
                    if not label or label.isascii():
                        punycode_labels.append(label)
                    else:
                        punycode_labels.append(label.encode("idna").decode("ascii"))
                punycode_host = ".".join(punycode_labels)
                # Rebuild the netloc, preserving port and userinfo if present
                netloc = parsed.netloc.replace(parsed.hostname, punycode_host, 1)
                text = urlunparse(parsed._replace(netloc=netloc))
        except (UnicodeError, ValueError, UnicodeDecodeError):
            # IDNA encoding failed (e.g. label too long, invalid character set):
            # fall through to the isascii() guard which will reject the URL.
            pass

    # ASCII safety check: after IDN normalization, any remaining non-ASCII
    # characters indicate invalid or potentially malicious input.
    if not text.isascii():
        return False

    # 4. Block C0 control characters (0x00-0x1F) and DEL (0x7F)
    # BEFORE strip/sanitize to catch malicious trailing/injected characters.
    # Note: Regex is ~13x faster than a manual loop for this check.
    if _CONTROL_CHARS_RE.search(text):
        return False

    # 5. Clean and normalize text using heuristics
    # sanitize_text also strips Cc/Cf as defense-in-depth, but is_safe_url_string
    # has already rejected all non-ASCII characters by this point.
    text = sanitize_text(text)

    return True


def validate_image_resource(
    resource: str | bytes | object,
) -> tuple[bool, int, str | None]:
    """
    Centralized validation for image resources.
    Checks for existence, accessibility, and size to prevent DoS and crashes.

    Args:
        resource: File path (str), raw bytes, or stream-like object.

    Returns:
        tuple: (is_valid, size_in_bytes, error_message)
    """
    size = 0

    try:
        if isinstance(resource, str):
            # Security: Use is_file() instead of exists() to ensure we're not
            # attempting to process directories, FIFOs, or device files as images.
            path = Path(resource)
            if not path.is_file():
                return False, 0, "File not found"
            if not os.access(resource, os.R_OK):
                return False, 0, "Permission denied"
            size = path.stat().st_size
        elif isinstance(resource, bytes):
            size = len(resource)
        elif hasattr(resource, "getbuffer"):
            # Handle BytesIO and similar
            size = resource.getbuffer().nbytes
        elif hasattr(resource, "seek") and hasattr(resource, "tell"):
            # General stream fallback
            curr = resource.tell()
            resource.seek(0, os.SEEK_END)
            size = resource.tell()
            resource.seek(curr, os.SEEK_SET)
        else:
            return False, 0, "Unsupported resource type"

        if size == 0:
            return False, 0, "Image file is empty"

        if size > MAX_IMAGE_SIZE_BYTES:
            mb_size = round(size / (1024 * 1024), 1)
            return (
                False,
                size,
                f"Image too large: {mb_size}MB (max {MAX_IMAGE_SIZE_MB}MB)",
            )

        return True, size, None

    except (AttributeError, RuntimeError, TypeError, ValueError, OSError) as e:
        logger.error(f"Validation: Unexpected error: {e}")
        return False, 0, f"Validation error: {e}"


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


def launch_uri(url: str, window=None, error_callback=None) -> None:
    """
    Centralized URI launching with security validation and UI feedback.

    Args:
        url: The URI to launch.
        window: The parent window for the launcher.
        error_callback: Optional callback for error messages. If not provided,
                        it attempts to show a toast or alert dialog.
    """
    from gettext import gettext as _

    from gi.repository import Gio, GLib, Gtk

    url = url.strip() if url else ""
    if not uri_validator(url):
        logger.warning(f"Anura: Blocked invalid URL launch: {url}")
        msg = _("Invalid URL blocked for security")
        if error_callback:
            error_callback(msg)
        elif window and hasattr(window, "show_toast"):
            window.show_toast(msg)
        return

    launcher = Gtk.UriLauncher.new(url)

    def on_launch_finish(_launcher: object, result: Gio.AsyncResult) -> None:
        try:
            launcher.launch_finish(result)
        except GLib.Error as e:
            logger.error(f"Anura: Failed to launch URI: {e.message}")
            msg = _("Failed to open link")
            if error_callback:
                error_callback(msg)
            elif window and hasattr(window, "show_toast"):
                window.show_toast(msg)

    launcher.launch(window, None, on_launch_finish)
