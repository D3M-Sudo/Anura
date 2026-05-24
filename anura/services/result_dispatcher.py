# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

from gettext import gettext as _
from gettext import ngettext
import sys
from typing import ClassVar

from loguru import logger

# Conditional import for GI (required for GObject inheritance)
try:
    from gi.repository import GLib, GObject, Gtk

    HAS_GI = True
except ImportError:
    HAS_GI = False
    # Mock for non-GI environments (tests)
    if "pytest" in sys.modules:

        class GObjectMock:
            class Object:
                pass

            SignalFlags = type("SignalFlags", (), {"RUN_FIRST": 0})

        GObject = GObjectMock()
        GLib = type("GLib", (), {"Variant": lambda *args: None})
        Gtk = type("Gtk", (), {"Application": type("App", (), {"get_default": lambda: None})})
    else:
        raise

from anura.services.clipboard_service import get_clipboard_service
from anura.services.settings import settings
from anura.utils import uri_validator
from anura.utils.singleton import get_instance
from anura.utils.text_preprocessor import get_text_preprocessor


class ResultDispatcher(GObject.GObject):
    """
    UI-independent service for dispatching OCR/Barcode results.
    Handles URL detection, clipboard management, and structured data notifications.
    """

    __gtype_name__ = "ResultDispatcher"

    __gsignals__: ClassVar[dict[str, tuple]] = {
        "toast-requested": (GObject.SignalFlags.RUN_FIRST, None, (str,)),
        "uri-launch-requested": (GObject.SignalFlags.RUN_FIRST, None, (str,)),
        "notification-requested": (GObject.SignalFlags.RUN_FIRST, None, (str, str)),
    }

    def dispatch(self, text: str, copy_requested: bool = False) -> None:
        """
        Process and dispatch the extracted text based on its content and user settings.

        Args:
            text: The extracted text or barcode content.
            copy_requested: Whether explicit clipboard copy was requested (e.g., from CLI).
        """
        if not text:
            self.emit("notification-requested", _("Anura OCR"), _("No text found. Try to grab another region."))
            return

        preprocessor = get_text_preprocessor()
        structured = preprocessor.extract_structured_data(text)

        # Identify if the result is primarily a URL (e.g. from a QR code)
        primary_url = None
        if structured["urls"]:
            # If the entire text is just a URL (allowing for whitespace/newlines)
            candidate = structured["urls"][0]
            if candidate.strip() == text.strip():
                primary_url = candidate

        if primary_url:
            self._handle_url_flow(primary_url, copy_requested)
        else:
            self._handle_text_flow(text, structured, copy_requested)

    def _handle_url_flow(self, url: str, copy_requested: bool) -> None:
        """Handle dispatching for URL-primary results."""
        url = url.strip().strip("\n\r\t\v\f")

        if not uri_validator(url):
            self._handle_text_flow(url, {}, copy_requested)
            return

        if settings.get_boolean("autolinks"):
            # Behavior A: Open directly in browser
            self.emit("uri-launch-requested", url)
            self.emit("toast-requested", _("URL opened automatically"))
        else:
            # Behavior B: Send desktop notification with clickable action
            target = GLib.Variant("s", url)
            app = Gtk.Application.get_default()
            if app and hasattr(app, "notification_service"):
                app.notification_service.send_notification_with_action(
                    notification_id="qr-url",
                    title=_("QR Code URL Detected"),
                    body=url,
                    action_id="app.open-qr-url",
                    action_target=target,
                    priority="high",
                )
            else:
                self.emit("notification-requested", _("QR Code URL Detected"), url)

        # Handle URL Clipboard (respecting global autocopy or explicit request)
        if settings.get_boolean("autocopy") or copy_requested:
            get_clipboard_service().set(url)
            # Only show "copied" toast if we didn't open the browser automatically
            if not settings.get_boolean("autolinks"):
                self.emit("toast-requested", _("URL copied to clipboard"))

        logger.debug("ResultDispatcher: URL-primary result processed")

    def _handle_text_flow(self, text: str, structured: dict, copy_requested: bool) -> None:
        """Handle dispatching for regular text results."""
        is_window_active = bool(Gtk.Application.get_default().get_active_window())

        if settings.get_boolean("autocopy") or copy_requested:
            get_clipboard_service().set(text)
            self.emit("toast-requested", _("Text copied to clipboard"))
            if not is_window_active:
                self.emit("notification-requested", _("Anura OCR"), _("Text extracted and copied to clipboard."))
        else:
            if not is_window_active:
                self.emit("notification-requested", _("Anura OCR"), _("Text extracted successfully."))

        # Show toasts for other structured data found in text
        if structured.get("emails"):
            count = len(structured["emails"])
            self.emit(
                "toast-requested",
                ngettext("{n} email found in text", "{n} emails found in text", count).format(n=count),
            )

        if structured.get("phone_numbers"):
            count = len(structured["phone_numbers"])
            self.emit(
                "toast-requested",
                ngettext("{n} phone number found in text", "{n} phone numbers found in text", count).format(n=count),
            )


def get_result_dispatcher() -> ResultDispatcher:
    """Get the thread-safe ResultDispatcher singleton."""
    return get_instance(ResultDispatcher)
