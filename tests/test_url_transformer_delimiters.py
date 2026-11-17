# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""URL transformer: TLD detection with query, fragment and port (#530).

``_has_valid_tld()`` required ``/`` or end-of-string right after the TLD, so
valid URLs followed by ``?``, ``#`` or ``:`` were filtered out even though the
shared URL pattern matched them.
"""

import pytest

from anura.transformers.url_transformer import _extract_urls, _has_valid_tld


@pytest.mark.parametrize(
    "url",
    [
        "https://example.com",
        "https://example.com/",
        "https://example.com/path",
        "https://example.com?next=/path",
        "https://example.com#section",
        "https://example.com:8443/path",
        "https://sub.example.co.uk?q=1#top",
        "http://example.com/?a=1&b=2",
        "www.example.com",
        "example.com/path",
        "https://example.com.",
    ],
)
def test_valid_tlds_are_recognised(url):
    assert _has_valid_tld(url) is True


@pytest.mark.parametrize(
    "url",
    [
        "https://example.c",
        "https://example.1",
        "https://localhost",
        "https://localhost:8080/",
        "https://192.168.1.1/",
        "file:///etc/passwd",
        "https://example.com:notaport/",
    ],
)
def test_invalid_tlds_are_rejected(url):
    assert _has_valid_tld(url) is False


def test_extract_urls_keeps_urls_with_delimiters():
    text = (
        "Open https://example.com?next=/dashboard or "
        "https://example.org#results and finally https://example.net:8443/path"
    )

    urls = _extract_urls(text)

    assert len(urls) == 3
    assert urls[0].startswith("https://example.com")
    assert urls[1].startswith("https://example.org")
    assert urls[2].startswith("https://example.net")
