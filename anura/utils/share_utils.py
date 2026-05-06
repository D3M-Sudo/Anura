# share_utils.py
#
# Pure Python utilities for share service - no GTK dependencies
# These functions can be safely imported and tested without GTK

from gettext import gettext as _
from urllib.parse import quote


def validate_share_url(url: str) -> bool:
    """
    Validate URL for sharing using security checks.

    Args:
        url: URL to validate

    Returns:
        True if URL is safe for sharing, False otherwise
    """
    if not url or not isinstance(url, str):
        return False

    # Basic URL structure validation
    if not (url.startswith('http://') or url.startswith('https://') or
            url.startswith('web+mastodon://') or url.startswith('mailto:')):
        return False

    # Length check to prevent overflow attacks
    if len(url) > 2000:
        return False

    # Check for potentially dangerous characters
    dangerous_chars = ['<', '>', '"', "'", '&', '\n', '\r', '\t']
    return not any(char in url for char in dangerous_chars)


def get_providers() -> list[str]:
    """
    Returns a list of supported share providers.

    Returns:
        List of provider names
    """
    return [
        'email',
        'reddit',
        'telegram',
        'x',
        'mastodon',
    ]


def get_link_email(text: str) -> str:
    """Generate email share link."""
    subject = quote(_("Extracted Text from Anura"))
    body = quote(text)  # Properly encode body to prevent malformed mailto links
    return f"mailto:?subject={subject}&body={body}"


def get_link_telegram(text: str) -> str:
    """Generate Telegram share link."""
    return f"https://t.me/share/url?text={text}"


def get_link_reddit(text: str) -> str:
    """Generate Reddit share link."""
    # For short texts (< 100 char): use title + body for better visibility
    if len(text) < 100:
        title = quote(_("Extracted Text"))
        body = quote(text)
        return f"https://www.reddit.com/submit?title={title}&selftext={body}"
    else:
        # For long texts: use only body to avoid title truncation
        return f"https://www.reddit.com/submit?selftext={text}"


def get_link_mastodon(text: str) -> str:
    """Generate Mastodon share link."""
    # Official web+mastodon:// scheme - primary method
    return f"web+mastodon://share?text={text}"


def get_link_x(text: str) -> str:
    """
    Twitter provider rebranded to X.com.
    """
    return f"https://x.com/intent/tweet?text={text}"
