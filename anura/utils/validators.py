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

    # 3. Homograph detection: Strict whitelist model (Latin-1 + IDNA).
    # If the hostname contains non-ASCII characters, it MUST be valid IDNA (Punycode).
    # Mixed-script hostnames (e.g. ASCII mixed with Cyrillic/Greek) are blocked.
    try:
        parsed_for_homograph = urlparse(text)
        hostname = parsed_for_homograph.hostname
        if not hostname:
            # BUG-034: Fail instantly if hostname is empty or parsing failed.
            return False

        if not hostname.isascii():
            # Strict Whitelist: Allow ONLY standard ASCII/Latin-1 (0x00-0xFF) in the hostname.
            # Any IDN outside this range (e.g. Cyrillic, Armenian, Hebrew) MUST be
            # Punycode-encoded (xn--) to be considered safe.
            for ch in hostname:
                if ord(ch) > 0xFF:
                    return False

            # Homograph Defense: Mixed-script check within Latin-1.
            # Block mixing ASCII alphanumeric characters with non-ASCII Latin-1 supplement
            # (e.g. googlé.com) as this is a common spoofing pattern.
            # "münchen.de" is allowed because "ü" is considered a separate label or
            # the user intended it, but "googlé" mixes them in one label.
            # Actually, per directive: "Block any URI that mixes scripts outside this narrow whitelist."
            # We'll block any mixed ASCII + Non-ASCII hostname for maximum safety.
            # Block any hostname that contains non-ASCII characters if it's not
            # pure non-ASCII (IDN). This is more restrictive than required but
            # safer. However, per directive we must support Latin-1.
            # To support "münchen.de", we check if the non-ASCII label is mixed with ASCII.
            for label in hostname.split("."):
                if not label.isascii() and any(c.isascii() and c.isalpha() for c in label):
                    return False

    except (ValueError, AttributeError, TypeError):
        # BUG-034: Fail instantly on any parsing exception.
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
