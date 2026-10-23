# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""QR autolink policy (#529).

A QR code is attacker-controlled content. Auto-opening every decoded URL let a
crafted code navigate the browser to a loopback admin UI or an intranet service
without confirmation, so autolinks now defaults to off and local/private
destinations always require an explicit confirmation.
"""

from pathlib import Path
import xml.etree.ElementTree as ET

import pytest

from anura.utils.validators import is_local_or_private_url

_SCHEMA = Path("data/io.github.d3msudo.anura.gschema.xml")


def test_autolinks_defaults_to_false():
    root = ET.parse(_SCHEMA).getroot()
    key = root.find(".//key[@name='autolinks']")

    assert key is not None
    assert key.findtext("default") == "false"


@pytest.mark.parametrize(
    "url",
    [
        "http://localhost:8080/admin",
        "http://localhost./",
        "http://LOCALHOST/",
        "http://127.0.0.1/",
        "http://127.1.2.3:631/printers",
        "http://[::1]/",
        "http://10.0.0.5/router",
        "http://192.168.1.1/",
        "http://172.16.4.2/",
        "http://169.254.169.254/latest/meta-data",
        "http://0.0.0.0/",
        "http://printer.local/status",
    ],
)
def test_local_and_private_destinations_require_confirmation(url):
    assert is_local_or_private_url(url) is True


@pytest.mark.parametrize(
    "url",
    [
        "https://example.com",
        "https://example.com:8443/path?q=1#frag",
        "http://8.8.8.8/",
        "https://sub.domain.example.org/page",
    ],
)
def test_public_destinations_can_open_automatically(url):
    assert is_local_or_private_url(url) is False


def test_host_less_or_unparsable_urls_are_treated_as_local():
    assert is_local_or_private_url("file:///etc/passwd") is True
    assert is_local_or_private_url("mailto:someone@example.com") is True
    assert is_local_or_private_url("not a url") is True


def test_uri_detected_applies_the_policy():
    source = Path("anura/main.py").read_text(encoding="utf-8")

    assert "is_local_or_private_url(url)" in source
