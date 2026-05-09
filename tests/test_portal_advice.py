# tests/test_portal_advice.py
#
# Pure-Python tests for `anura.utils.portal_advice.detect_portal_advice`.
# These run under `uv run pytest tests/ -m "not gtk"` because the helper
# has zero GTK / Xdp / Gio dependencies — it only reads the host's
# `XDG_CURRENT_DESKTOP` env var and returns a structured advice object.

from __future__ import annotations

import pytest

from anura.utils.portal_advice import PortalAdvice, detect_portal_advice


def _advice_for(value: str | None) -> PortalAdvice:
    """Helper: call detect_portal_advice with an explicit env override."""
    env: dict[str, str] = {} if value is None else {"XDG_CURRENT_DESKTOP": value}
    return detect_portal_advice(env=env)


@pytest.mark.parametrize(
    "xdg_value",
    ["LXQt", "lxqt", "ubuntu:LXQt", "LXQt:Lubuntu"],
)
def test_lxqt_recommends_kde_backend_with_portals_conf_step(xdg_value: str) -> None:
    advice = _advice_for(xdg_value)
    assert advice.desktop == "LXQt"
    assert "lxqt-portals.conf" in advice.long_message
    assert "xdg-desktop-portal-kde" in advice.long_message
    assert "Screenshot=kde" in advice.long_message
    # Banner string must be short enough not to wrap awkwardly. The
    # detailed instructions only belong in long_message.
    assert "lxqt-portals.conf" not in advice.short_message
    assert advice.docs_url is not None


@pytest.mark.parametrize(
    "xdg_value",
    ["KDE", "kde", "KDE:Plasma", "plasma"],
)
def test_kde_recommends_xdg_desktop_portal_kde(xdg_value: str) -> None:
    advice = _advice_for(xdg_value)
    assert advice.desktop == "KDE Plasma"
    assert "xdg-desktop-portal-kde" in advice.long_message
    # The KDE branch must NOT recommend gtk or gnome (the kde backend is
    # the only correct one for native KDE Plasma sessions).
    assert "xdg-desktop-portal-gnome" not in advice.long_message
    assert "xdg-desktop-portal-gtk" not in advice.long_message


@pytest.mark.parametrize(
    "xdg_value",
    ["GNOME", "gnome", "ubuntu:GNOME", "Unity:Unity7:ubuntu", "Pantheon"],
)
def test_gnome_family_recommends_gnome_backend(xdg_value: str) -> None:
    advice = _advice_for(xdg_value)
    assert advice.desktop == "GNOME"
    assert "xdg-desktop-portal-gnome" in advice.long_message


@pytest.mark.parametrize(
    "xdg_value",
    ["sway", "Hyprland", "wlroots:sway", "river", "Niri"],
)
def test_wlroots_compositors_recommend_wlr_backend(xdg_value: str) -> None:
    advice = _advice_for(xdg_value)
    assert "xdg-desktop-portal-wlr" in advice.long_message


def test_xfce_recommends_gnome_or_kde_backend_not_gtk() -> None:
    """On modern Ubuntu the gtk portal lost the Screenshot interface, so
    the working install command is xdg-desktop-portal-gnome (or -kde),
    not -gtk. Regression test against the old hard-coded advice."""
    advice = _advice_for("XFCE")
    assert advice.desktop == "Xfce"
    assert "xdg-desktop-portal-gnome" in advice.long_message
    # Sanity-check we explicitly call out that -gtk is not enough.
    assert "xdg-desktop-portal-gtk" in advice.long_message


@pytest.mark.parametrize(
    ("xdg_value", "friendly"),
    [("MATE", "Mate"), ("Cinnamon", "Cinnamon"), ("X-Cinnamon", "Cinnamon"), ("Budgie", "Budgie")],
)
def test_other_gtk_desktops_get_named_friendly(xdg_value: str, friendly: str) -> None:
    advice = _advice_for(xdg_value)
    assert advice.desktop == friendly
    assert "xdg-desktop-portal-gnome" in advice.long_message


@pytest.mark.parametrize("xdg_value", [None, "", "FantasyWM"])
def test_unknown_or_missing_desktop_falls_back_to_generic_message(xdg_value: str | None) -> None:
    advice = _advice_for(xdg_value)
    assert advice.desktop == "your desktop"
    # The generic branch must still mention concrete backend names so
    # the user has somewhere to start, even on an unknown desktop.
    for backend in ("xdg-desktop-portal-gnome", "-kde", "-wlr"):
        assert backend in advice.long_message


def test_advice_dataclass_is_immutable() -> None:
    """PortalAdvice is frozen — guards against accidental mutation by
    callers that might want to "tweak" the message in place."""
    from dataclasses import FrozenInstanceError

    advice = _advice_for("GNOME")
    with pytest.raises(FrozenInstanceError):
        advice.desktop = "Other"  # type: ignore[misc]


def test_detect_uses_os_environ_when_env_omitted(monkeypatch: pytest.MonkeyPatch) -> None:
    """When called without an `env` argument, detect_portal_advice reads
    the real `os.environ`. Verify by monkey-patching XDG_CURRENT_DESKTOP."""
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "KDE")
    advice = detect_portal_advice()
    assert advice.desktop == "KDE Plasma"
    assert "xdg-desktop-portal-kde" in advice.long_message


def test_lxqt_match_is_case_insensitive_and_token_aware() -> None:
    """A real-world LXQt session reports XDG_CURRENT_DESKTOP=LXQt. The
    detector must be case-insensitive and tolerate colon-separated lists
    where LXQt is not the first token."""
    advice = _advice_for("ubuntu:LXQt")
    assert advice.desktop == "LXQt"
