# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""A share provider must not promise a transfer it cannot perform (#579).

`share_providers` has no GTK dependency, so these assertions run in the default
headless gate rather than the GTK tier.
"""

from anura.services.share_providers import PROVIDERS, generate_share_link


def test_reddit_does_not_duplicate_the_text():
    link = generate_share_link("reddit", "short text")

    assert link.count("short") == 1
    assert "title=" not in link


def test_reddit_sends_the_text_as_selftext():
    assert generate_share_link("reddit", "a b") == "https://www.reddit.com/submit?selftext=a%20b"


def test_discord_is_not_offered():
    assert "discord" not in {provider.id for provider in PROVIDERS}
    assert generate_share_link("discord", "x") == ""


def test_every_provider_produces_a_link_for_its_own_text():
    for provider in PROVIDERS:
        link = generate_share_link(provider.id, "hello world")
        assert link, f"{provider.id} produced no link"
        assert " " not in link, f"{provider.id} left an unescaped space: {link}"
