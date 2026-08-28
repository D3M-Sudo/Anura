#!/usr/bin/env python3
# .github/scripts/test_certifi_matcher.py
"""Tests for the FEDC certifi matcher (.github/scripts/fedc_certifi.py).

Validates the URL-filename matching logic against realistic manifest
fragments, including the FEDC-updated form and negative cases.

Run:  python3 test_certifi_matcher.py
"""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import fedc_certifi


def test_match_certifi_wheel():
    assert fedc_certifi.is_certifi_source(
        {"url": "https://files.pythonhosted.org/packages/xx/certifi-2026.4.22-py3-none-any.whl"}
    )


def test_no_match_other_packages():
    assert not fedc_certifi.is_certifi_source(
        {"url": "https://files.pythonhosted.org/packages/xx/gtts-2.5.4-py3-none-any.whl"}
    )
    assert not fedc_certifi.is_certifi_source(
        {"url": "https://files.pythonhosted.org/packages/xx/pillow-11.0.0.tar.gz"}
    )


def test_no_match_missing_url():
    assert not fedc_certifi.is_certifi_source({})
    assert not fedc_certifi.is_certifi_source({"type": "git"})


def test_no_match_partial_name():
    # e.g. a git repo named certifi-mirror must NOT match URL filename rule
    assert not fedc_certifi.is_certifi_source({"url": "https://github.com/org/certifi-mirror.git"})


def _real_manifest():
    return {
        "app-id": "io.github.d3msudo.anura",
        "modules": [
            {
                "name": "python3-pillow",
                "sources": [
                    {"url": "https://files.pythonhosted.org/packages/xx/pillow-11.0.0.tar.gz"}
                ],
            },
            {
                "name": "python3-certifi",
                "sources": [
                    {
                        "url": "https://files.pythonhosted.org/packages/xx/certifi-2025.8.3-py3-none-any.whl",
                        "sha256": "aaa",
                    }
                ],
            },
        ],
    }


def test_isolate_and_replace_roundtrip():
    with tempfile.TemporaryDirectory() as tmp:
        real = Path(tmp) / "real.json"
        iso = Path(tmp) / "isolated.json"
        real.write_text(json.dumps(_real_manifest(), indent=4) + "\n")

        fedc_certifi.create_isolated_manifest(str(real), str(iso))
        isolated = json.loads(iso.read_text())
        assert len(isolated["modules"]) == 1
        assert isolated["modules"][0]["name"] == "python3-certifi"
        assert isolated["modules"][0]["sources"][0]["sha256"] == "aaa"

        # Simulate FEDC having updated the isolated manifest
        isolated["modules"][0]["sources"][0]["url"] = (
            "https://files.pythonhosted.org/packages/xx/certifi-2026.4.22-py3-none-any.whl"
        )
        isolated["modules"][0]["sources"][0]["sha256"] = "bbb"
        iso.write_text(json.dumps(isolated, indent=4) + "\n")

        fedc_certifi.replace_certifi_source(str(real), str(iso))
        updated = json.loads(real.read_text())

        cert = updated["modules"][1]["sources"][0]
        assert cert["sha256"] == "bbb"
        assert cert["url"].endswith("certifi-2026.4.22-py3-none-any.whl")
        # Non-certifi module untouched
        assert updated["modules"][0]["sources"][0]["url"].endswith("pillow-11.0.0.tar.gz")


def test_zero_matches_raises():
    manifest = {"modules": [{"name": "m", "sources": [{"url": "https://example.com/other.whl"}]}]}
    try:
        fedc_certifi.find_certifi_sources(manifest)
    except SystemExit:
        return
    raise AssertionError("expected SystemExit for zero matches")


def test_multiple_matches_raises():
    src = {"url": "https://files.pythonhosted.org/packages/xx/certifi-2025.8.3-py3-none-any.whl"}
    manifest = {"modules": [{"name": "m", "sources": [src, dict(src)]}]}
    try:
        fedc_certifi.find_certifi_sources(manifest)
    except SystemExit:
        return
    raise AssertionError("expected SystemExit for multiple matches")


def test_against_real_manifest():
    repo_root = Path(__file__).resolve().parents[2]
    real = repo_root / "flatpak" / "io.github.d3msudo.anura.json"
    if not real.exists():
        print("SKIP: real manifest not found")
        return
    manifest = json.loads(real.read_text())
    matches = fedc_certifi.find_certifi_sources(manifest)
    assert len(matches) == 1
    url = matches[0][1]["url"]
    assert "certifi" in url
    print(f"  real manifest certifi source: {url}")


def main():
    tests = [
        test_match_certifi_wheel,
        test_no_match_other_packages,
        test_no_match_missing_url,
        test_no_match_partial_name,
        test_isolate_and_replace_roundtrip,
        test_zero_matches_raises,
        test_multiple_matches_raises,
        test_against_real_manifest,
    ]
    for t in tests:
        t()
        print(f"PASS {t.__name__}")
    print(f"\nAll {len(tests)} tests passed.")


if __name__ == "__main__":
    main()
