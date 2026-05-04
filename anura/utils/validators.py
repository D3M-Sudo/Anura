# validators.py
#
# Copyright 2026 D3M-Sudo (Anura fork and modifications)

import ipaddress
from urllib.parse import urlparse


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
    url = text.strip()

    # Block control characters (0x00-0x1F) and DEL (0x7F)
    # This prevents newline, tab, carriage return, null byte injection
    if any(ord(c) < 0x20 or ord(c) == 0x7F for c in url):
        return False

    # Ensure URL is ASCII-only (prevent Unicode homograph attacks)
    try:
        url.encode("ascii")
    except UnicodeEncodeError:
        return False

    try:
        res = urlparse(url)
        if not (res.scheme in ("http", "https") and bool(res.netloc)):
            return False

        # Allow localhost and IP addresses (common in development/enterprise)
        # Also allow hostnames with dots (normal domains)
        netloc_lower = res.netloc.lower()
        if netloc_lower == "localhost" or netloc_lower.startswith("localhost:"):
            return True
        if "." in res.netloc:
            return True
        # Check for valid IP address (IPv4 or IPv6)
        # Remove port if present for validation
        host = res.netloc
        if ':' in host and not host.endswith(']'):
            # Could be IPv4:port or IPv6:port - split on last colon
            host = host.rsplit(':', 1)[0]
        # Unbracket IPv6 if bracketed
        if host.startswith('[') and host.endswith(']'):
            host = host[1:-1]
        try:
            ipaddress.ip_address(host)
            return True
        except ValueError:
            pass

        # Reject single-word hostnames without dots (prevents "http://evil")
        return False
    except ValueError:
        return False
