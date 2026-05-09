# Copyright 2026 D3M-Sudo (Anura fork and modifications)
#
# MIT License
"""Desktop-aware advice for missing xdg-desktop-portal Screenshot backend.

When the host's xdg-desktop-portal returns the generic
``g-io-error-quark code=0 "Screenshot failed"`` (no backend declares
``org.freedesktop.impl.portal.Screenshot`` for the active session),
the install hint Anura shows depends on the desktop. Hard-coding
``xdg-desktop-portal-gtk`` is wrong on most modern desktops:

* On Ubuntu 24.04+, the upstream ``gtk.portal`` no longer implements
  the ``Screenshot`` interface — installing ``xdg-desktop-portal-gtk``
  alone does not bring screenshots back on LXQt / Xfce / MATE.
* On LXQt the only registered portal for the LXQt session is
  ``lxqt.portal`` which exposes ``FileChooser`` only; the user has to
  install ``xdg-desktop-portal-kde`` *and* delegate the Screenshot
  interface to ``kde`` via a ``portals.conf`` override.

This module returns the right advice based on ``XDG_CURRENT_DESKTOP``.
It is pure-Python and has no GTK dependency, which makes it directly
testable from ``pytest -m "not gtk"``.
"""

from __future__ import annotations

from dataclasses import dataclass
from gettext import gettext as _
import os


@dataclass(frozen=True)
class PortalAdvice:
    """Recommended action when no portal backend handles Screenshot.

    Attributes:
        desktop: Friendly name of the detected desktop (e.g. ``"GNOME"``,
            ``"KDE Plasma"``, ``"LXQt"``, ``"your desktop"`` for the unknown
            fallback).
        short_message: One-line, banner-friendly text. Already translated
            via ``gettext``.
        long_message: Multi-line toast / notification body with the install
            command and any extra configuration step. Already translated.
        docs_url: Optional URL pointing at the relevant section of the
            project README so the user can see the full instructions.
    """

    desktop: str
    short_message: str
    long_message: str
    docs_url: str | None


_DOCS_URL = "https://github.com/D3M-Sudo/Anura#runtime-requirements"


def _split_xdg_current_desktop(value: str) -> list[str]:
    """Return lower-cased tokens from an ``XDG_CURRENT_DESKTOP`` value.

    The variable is colon-separated by spec (e.g. ``"ubuntu:GNOME"``).
    Empty tokens are dropped.
    """
    return [token.strip().lower() for token in value.split(":") if token.strip()]


def detect_portal_advice(env: dict[str, str] | None = None) -> PortalAdvice:
    """Return desktop-aware install advice for a missing Screenshot backend.

    Args:
        env: Override for ``os.environ`` — useful for tests. When ``None``
            (the default), ``os.environ`` is read.

    The detection order is intentional: more specific desktops are matched
    first (e.g. ``LXQt`` before generic Qt/KDE-flavoured fallbacks), and
    common compositor families that Ubuntu/Debian ship a dedicated portal
    backend for (``-gnome``, ``-kde``, ``-wlr``) take precedence over the
    generic ``-gtk`` advice.
    """
    source = env if env is not None else os.environ
    tokens = _split_xdg_current_desktop(source.get("XDG_CURRENT_DESKTOP") or "")

    def has(*names: str) -> bool:
        """Return True if any of the given desktop names is in tokens."""
        return any(name in tokens for name in names)

    # LXQt: lxqt.portal exposes FileChooser only, gtk.portal lost
    # Screenshot upstream — the working setup is xdg-desktop-portal-kde
    # plus a portals.conf override delegating Screenshot to it.
    if has("lxqt"):
        return PortalAdvice(
            desktop=_("LXQt"),
            short_message=_("Screenshot portal is not configured for LXQt. See the README for the LXQt setup steps."),
            long_message=_(
                "On LXQt, install xdg-desktop-portal-kde, then create "
                "~/.config/xdg-desktop-portal/lxqt-portals.conf with "
                "[preferred] org.freedesktop.impl.portal.Screenshot=kde, "
                "and restart the portal "
                "(systemctl --user restart xdg-desktop-portal.service)."
            ),
            docs_url=_DOCS_URL,
        )

    if has("kde", "plasma"):
        return PortalAdvice(
            desktop=_("KDE Plasma"),
            short_message=_("Screenshot portal unavailable. Install xdg-desktop-portal-kde and re-login."),
            long_message=_(
                "Screenshot failed. On KDE Plasma, install xdg-desktop-portal-kde "
                "(e.g. sudo apt install xdg-desktop-portal-kde) and log out and back in."
            ),
            docs_url=_DOCS_URL,
        )

    # wlroots-based compositors usually ship via xdg-desktop-portal-wlr.
    if has("sway", "hyprland", "wlroots", "river", "niri"):
        return PortalAdvice(
            desktop=_("your wlroots compositor"),
            short_message=_("Screenshot portal unavailable. Install xdg-desktop-portal-wlr and re-login."),
            long_message=_(
                "Screenshot failed. On wlroots-based compositors (Sway, Hyprland, river, Niri, …), "
                "install xdg-desktop-portal-wlr "
                "(e.g. sudo apt install xdg-desktop-portal-wlr) and log out and back in."
            ),
            docs_url=_DOCS_URL,
        )

    # GNOME family. Pantheon (elementary) and Unity (Ubuntu Unity) report
    # GNOME tokens or sit best on the GNOME backend in practice.
    if has("gnome", "unity", "pantheon"):
        return PortalAdvice(
            desktop=_("GNOME"),
            short_message=_("Screenshot portal unavailable. Install xdg-desktop-portal-gnome and re-login."),
            long_message=_(
                "Screenshot failed. On GNOME / Ubuntu, install xdg-desktop-portal-gnome "
                "(e.g. sudo apt install xdg-desktop-portal-gnome) and log out and back in."
            ),
            docs_url=_DOCS_URL,
        )

    # Other GTK-based desktops (Xfce, MATE, Cinnamon, Budgie). On modern
    # Ubuntu the gtk.portal no longer implements Screenshot, so the working
    # path is the same as LXQt: route Screenshot to the KDE backend.
    if has("xfce", "mate", "x-cinnamon", "cinnamon", "budgie"):
        # Title-case the first token for the friendly name.
        friendly = next(
            (t.title() for t in tokens if t in {"xfce", "mate", "x-cinnamon", "cinnamon", "budgie"}),
            "your desktop",
        )
        if friendly == "X-Cinnamon":
            friendly = "Cinnamon"
        return PortalAdvice(
            desktop=friendly,
            short_message=_("Screenshot portal unavailable. Install xdg-desktop-portal-gnome (or -kde) and re-login."),
            long_message=_(
                "Screenshot failed. On {desktop}, install xdg-desktop-portal-gnome "
                "(or xdg-desktop-portal-kde) and log out and back in. On modern Ubuntu "
                "xdg-desktop-portal-gtk no longer provides the Screenshot interface."
            ).format(desktop=friendly),
            docs_url=_DOCS_URL,
        )

    # Unknown / unset desktop — keep the previous generic message.
    return PortalAdvice(
        desktop=_("your desktop"),
        short_message=_("Screenshot portal unavailable. Install the xdg-desktop-portal backend matching your desktop."),
        long_message=_(
            "Screenshot failed. Your desktop session does not appear to expose a "
            "working screenshot portal. Install the xdg-desktop-portal backend "
            "matching your desktop (e.g. xdg-desktop-portal-gnome, -kde, -wlr) and re-login."
        ),
        docs_url=_DOCS_URL,
    )
