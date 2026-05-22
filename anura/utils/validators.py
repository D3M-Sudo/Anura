# validators.py
#
# Copyright 2026 D3M-Sudo (Anura fork and modifications)

import contextlib
import ipaddress
import re
from urllib.parse import urlparse

# Pre-compiled regex for control characters (0x00-0x1F) and DEL (0x7F)
# Using a regex is ~13x faster than a manual loop for control character detection.
_CONTROL_CHARS_RE = re.compile(r"[\x00-\x1f\x7f]")


def is_safe_url_string(text: str) -> bool:
    """
    Perform fundamental security checks on a URL string.
    Checks for length, control characters, and ASCII-only characters.
    """
    if text is None:
        return False

    # Defense-in-depth: limit URL length to prevent UI/notification issues
    # and potential downstream buffer vulnerabilities.
    if len(text) > 2048:
        return False

    # Block control characters (0x00-0x1F) and DEL (0x7F) BEFORE strip
    # so that e.g. trailing \x1f (whitespace) is caught.
    if _CONTROL_CHARS_RE.search(text):
        return False

    # Ensure URL is ASCII-only (prevent Unicode homograph attacks).
    # str.isascii() is significantly faster than encoding to ascii and catching exceptions.
    return text.strip().isascii()


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
