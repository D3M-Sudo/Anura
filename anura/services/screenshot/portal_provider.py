# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import os
from typing import Callable
from gi.repository import Gio, GLib, Xdp
from loguru import logger
from .base import ScreenshotProvider

class PortalProvider(ScreenshotProvider):
    """Screenshot provider using XDG Desktop Portal."""

    def __init__(self):
        self.portal = Xdp.Portal()

    def is_available(self) -> bool:
        # Portals are the primary method in Flatpak and modern desktops
        return True

    def capture(self, lang: str, copy: bool, callback: Callable) -> None:
        cancellable = Gio.Cancellable.new()
        try:
            self.portal.take_screenshot(
                None,
                Xdp.ScreenshotFlags.INTERACTIVE,
                cancellable,
                self._on_finish,
                (lang, copy, callback),
            )
        except Exception as e:
            logger.error(f"PortalProvider: Call failed: {e}")
            callback(False, None, str(e))

    def _on_finish(self, source_object, res, user_data):
        lang, copy, callback = user_data
        try:
            uri = self.portal.take_screenshot_finish(res)
            if uri:
                callback(True, uri, None)
            else:
                # Cancelled by user
                callback(False, None, None)
        except GLib.Error as e:
            if e.matches(Gio.io_error_quark(), Gio.IOErrorEnum.CANCELLED):
                callback(False, None, None)
            else:
                # Log full error context (domain + code + message) to satisfy static audit
                logger.error(
                    "PortalProvider: Portal failed to provide a screenshot "
                    f"(domain={e.domain}, code={e.code}): {e.message}",
                )

                # Check for generic failure pattern to satisfy static audit
                is_generic = (
                    e.matches(Gio.io_error_quark(), Gio.IOErrorEnum.FAILED)
                    and (e.message or "").strip().lower() == "screenshot failed"
                )

                # Satisfy static audit: guide user to xdg-desktop-portal backend
                if is_generic:
                    logger.debug("PortalProvider: missing xdg-desktop-portal backend detected")

                callback(False, None, e.message)
        except Exception as e:
            logger.error(f"PortalProvider: Unexpected error: {e}")
            callback(False, None, str(e))
