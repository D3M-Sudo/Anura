# This file is part of Anura.
# Copyright (C) 2022-2025 Andrey Maksimov (Frog)
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

from gettext import gettext as _
from typing import ClassVar
from urllib.parse import quote

import gi

# Set GTK version requirements before imports
gi.require_version("Adw", "1")
gi.require_version("Gio", "2.0")
gi.require_version("GLib", "2.0")
gi.require_version("GObject", "2.0")
gi.require_version("Gtk", "4.0")

from gi.repository import Adw, Gio, GLib, GObject, Gtk  # noqa: E402
from loguru import logger  # noqa: E402

from anura.utils import is_safe_url_string, uri_validator  # noqa: E402
from anura.utils.singleton import get_instance  # noqa: E402


class ShareService(GObject.GObject):
    """
    Service responsible for sharing extracted text to external providers.
    Designed for Anura to handle web-based and protocol-based URI launching.
    """

    __gtype_name__ = "ShareService"

    __gsignals__: ClassVar[dict[str, tuple]] = {"share": (GObject.SignalFlags.RUN_LAST, None, (bool,))}

    def __init__(self) -> None:
        super().__init__()
        self.launcher = Gtk.UriLauncher()

    @staticmethod
    def providers() -> list[str]:
        """
        Returns a list of supported share providers.
        """
        return [
            "email",
            "mastodon",
            "reddit",
            "telegram",
            "x",
            "bluesky",
            "discord",
            "linkedin",
            "threads",
            # NOTE: "instagram" removed — no URL prefill API available
        ]

    # Maximum URL length for safe sharing (most browsers support ~2000, be conservative)
    MAX_URL_LENGTH = 2000

    @staticmethod
    def _validate_share_url(url: str) -> bool:
        """
        Validate URL for sharing using security checks.
        Returns True if URL is safe to share, False otherwise.
        """
        # Security: Perform fundamental checks (length, control chars, ASCII) on all URLs
        if not is_safe_url_string(url):
            return False

        url = url.strip() if url else ""

        # Allow mailto and web+mastodon schemes after passing fundamental checks
        if url.startswith("mailto:") or url.startswith("web+mastodon:"):
            return True

        # Use centralized uri_validator for http/https URLs (includes hostname validation)
        return uri_validator(url)

    def share(self, provider: str, text: str) -> None:
        """
        Generates a share link and launches the default system handler.
        """
        text = text.strip() if text else ""
        if not text:
            logger.warning("Anura Share: Attempted to share empty text.")
            return
        handler = getattr(self, f"get_link_{provider}", None)

        if handler is None:
            logger.warning(f"Anura Share: Unknown provider '{provider}' - no handler found")
            return

        if handler:
            try:
                # Each get_link_* handler URL-encodes the text itself, so pass raw text through.
                if provider == "mastodon":
                    return self._share_mastodon_with_fallback(text)

                share_link: str = handler(text)

                # Validate URL length before attempting to launch
                if len(share_link) > self.MAX_URL_LENGTH:
                    logger.warning(f"Anura Share: URL too long ({len(share_link)} chars, max {self.MAX_URL_LENGTH})")
                    return

                # Security: validate URL before launching (defense in depth)
                # Use static method to avoid circular imports and instance creation
                if not ShareService._validate_share_url(share_link):
                    logger.warning(f"Anura Share: Blocked invalid URL: {share_link}")
                    return

                self.launcher.set_uri(share_link)
                self.launcher.launch(parent=None, cancellable=None, callback=self._on_share)
            except (ValueError, TypeError, AttributeError) as e:
                logger.error(f"Anura Share Error: Failed to share via {provider}. Reason: {e}")

    def _share_mastodon_with_fallback(self, text: str) -> None:
        """Share to Mastodon with official scheme and fallback to instance selection."""
        encoded_text = quote(text, safe="")

        # Try official web+mastodon:// scheme first. Validate length against
        # the URL we will actually launch (the web+mastodon:// scheme; the
        # https://mastodon.social/share fallback is shorter for the same
        # encoded text, so it's covered by this same check).
        mastodon_url = f"web+mastodon://share?text={encoded_text}"
        if len(mastodon_url) > self.MAX_URL_LENGTH:
            logger.warning(
                f"Anura Share: Mastodon URL too long ({len(mastodon_url)} chars, max {self.MAX_URL_LENGTH})",
            )

            def _on_share_idle(res):
                try:
                    self.emit("share", res)
                except Exception as e:
                    logger.exception(f"Anura: Failed to emit share status: {e}")
                return GLib.SOURCE_REMOVE

            GLib.idle_add(_on_share_idle, False)
            return

        self.launcher.set_uri(mastodon_url)

        def on_mastodon_result(_: object, result: Gio.AsyncResult) -> None:
            """Handle Mastodon share result with fallback."""
            try:
                success = self.launcher.launch_finish(result)
                if not success:
                    # Official scheme failed, show instance selection
                    logger.info("Anura Share: web+mastodon:// not supported, showing instance selection")
                    self._show_mastodon_instance_dialog(encoded_text)
                else:

                    def _on_share_idle(res):
                        try:
                            self.emit("share", res)
                        except Exception as e:
                            logger.error(f"Anura: Failed to emit share status: {e}")
                        return GLib.SOURCE_REMOVE

                    GLib.idle_add(_on_share_idle, True)
            except (GLib.Error, RuntimeError) as e:
                logger.warning(f"Anura Share: web+mastodon:// launch failed: {e}")
                self._show_mastodon_instance_dialog(encoded_text)

        try:
            self.launcher.launch(parent=None, cancellable=None, callback=on_mastodon_result)
        except (GLib.Error, RuntimeError) as e:
            logger.warning(f"Anura Share: Failed to launch web+mastodon:// scheme: {e}")
            self._show_mastodon_instance_dialog(encoded_text)

    def _show_mastodon_instance_dialog(self, encoded_text: str) -> None:
        """Show dialog to select Mastodon instance for fallback sharing."""
        instances = [
            ("mastodon.social", "Mastodon Official"),
            ("mastodon.online", "Mastodon Online"),
            ("fosstodon.org", "Fosstodon - Open Source"),
            ("hachyderm.io", "Hachyderm - Tech Community"),
        ]

        # Create selection dialog
        dialog = Adw.MessageDialog()
        dialog.set_heading(_("Select Mastodon Instance"))
        dialog.set_body(_("Choose your Mastodon instance to share the extracted text:"))

        # Add instance buttons
        for domain, name in instances:
            dialog.add_response(f"instance_{domain}", name)

        dialog.add_response("cancel", _("Cancel"))
        dialog.set_default_response("cancel")
        dialog.set_close_response("cancel")

        # Connect response signal
        def _on_response(dlg, response):
            try:
                self._on_mastodon_instance_selected(dlg, response, encoded_text)
            except Exception as e:
                logger.error(f"Anura: Unexpected error in Mastodon instance selection: {e}")

        dialog.connect("response", _on_response)

        # Show dialog (we need a parent window)
        try:
            # Try to get the active window from the application
            from gi.repository import Gio

            app = Gio.Application.get_default()
            parent_window = app.get_active_window() if app else None
            if parent_window:
                dialog.set_transient_for(parent_window)
                dialog.present()
            else:
                # No parent window available - show user notification
                logger.warning("Anura Share: No active window for Mastodon instance dialog")

                # Show toast notification through main window if available
                if app:
                    main_window = app.get_active_window()
                    if main_window and hasattr(main_window, "show_toast"):

                        def _on_toast_idle(msg):
                            try:
                                main_window.show_toast(msg)
                            except Exception as e:
                                logger.exception(f"Anura: Failed to show toast: {e}")
                            return GLib.SOURCE_REMOVE

                        GLib.idle_add(_on_toast_idle, _("Cannot show dialog without active window"))

                def _on_share_idle(res):
                    try:
                        self.emit("share", res)
                    except Exception as e:
                        logger.exception(f"Anura: Failed to emit share status: {e}")
                    return GLib.SOURCE_REMOVE

                GLib.idle_add(_on_share_idle, False)
                dialog.destroy()
        except (GLib.Error, RuntimeError) as e:
            logger.error(f"Anura Share: Failed to show Mastodon instance dialog: {e}")

            def _on_share_idle(res):
                try:
                    self.emit("share", res)
                except Exception as e:
                    logger.exception(f"Anura: Failed to emit share status: {e}")
                return GLib.SOURCE_REMOVE

            GLib.idle_add(_on_share_idle, False)
            dialog.destroy()

    def _on_mastodon_instance_selected(self, dialog: Adw.MessageDialog, response: str, encoded_text: str) -> None:
        """Handle Mastodon instance selection."""
        if response.startswith("instance_"):
            domain = response.replace("instance_", "")
            share_url = f"https://{domain}/share?text={encoded_text}"

            try:
                self.launcher.set_uri(share_url)
                self.launcher.launch(parent=None, cancellable=None, callback=self._on_share)
            except (GLib.Error, RuntimeError) as e:
                logger.error(f"Anura Share: Failed to share via Mastodon instance {domain}: {e}")

                def _on_share_idle(res):
                    try:
                        self.emit("share", res)
                    except Exception as e:
                        logger.exception(f"Anura: Failed to emit share status: {e}")
                    return GLib.SOURCE_REMOVE

                GLib.idle_add(_on_share_idle, False)

        dialog.destroy()

    def _on_share(self, _launcher: object, result: Gio.AsyncResult) -> None:
        """
        Async callback for URI launch completion.
        """
        try:
            success = self.launcher.launch_finish(result)

            def _on_share_idle(res):
                try:
                    self.emit("share", res)
                except Exception as e:
                    logger.exception(f"Anura: Failed to emit share status: {e}")
                return GLib.SOURCE_REMOVE

            GLib.idle_add(_on_share_idle, success)
        except (GLib.Error, RuntimeError) as e:
            logger.warning(f"Anura Share Warning: URI launch failed: {e}")

            def _on_share_idle(res):
                try:
                    self.emit("share", res)
                except Exception as e:
                    logger.exception(f"Anura: Failed to emit share status: {e}")
                return GLib.SOURCE_REMOVE

            GLib.idle_add(_on_share_idle, False)

    @staticmethod
    def get_link_telegram(text: str) -> str:
        if not text or not text.strip():
            return ""
        # Security: use safe="" to ensure special chars like '/' are encoded in params
        encoded_text = quote(text.strip(), safe="")
        return f"https://t.me/share/url?text={encoded_text}"

    @staticmethod
    def get_link_reddit(text: str) -> str:
        if not text or not text.strip():
            return ""
        text = text.strip()
        # For short texts (< 100 char): use title + body for better visibility
        if len(text) < 100:
            encoded_title = quote(text, safe="")
            encoded_text = quote(text, safe="")
            return f"https://www.reddit.com/submit?title={encoded_title}&selftext={encoded_text}"
        else:
            # For long texts: use only body to avoid title truncation
            encoded_text = quote(text, safe="")
            return f"https://www.reddit.com/submit?selftext={encoded_text}"

    @staticmethod
    def get_link_mastodon(text: str) -> str:
        # Official web+mastodon:// scheme - primary method
        if not text or not text.strip():
            return ""
        encoded_text = quote(text.strip(), safe="")
        return f"web+mastodon://share?text={encoded_text}"

    @staticmethod
    def get_link_x(text: str) -> str:
        """
        Twitter provider rebranded to X.com.
        """
        if not text or not text.strip():
            return ""
        encoded_text = quote(text.strip(), safe="")
        return f"https://x.com/intent/tweet?text={encoded_text}"

    @staticmethod
    def get_link_email(text: str) -> str:
        if not text or not text.strip():
            return ""
        subject = quote(_("Extracted Text"), safe="")
        body = quote(text.strip(), safe="")  # Properly encode body to prevent malformed mailto links
        return f"mailto:?subject={subject}&body={body}"

    @staticmethod
    def get_link_bluesky(text: str) -> str:
        """Share to Bluesky with their web interface."""
        if not text or not text.strip():
            return ""
        encoded_text = quote(text.strip(), safe="")
        return f"https://bsky.app/intent/compose?text={encoded_text}"

    @staticmethod
    def get_link_discord(text: str) -> str:
        """Share to Discord (opens status update dialog)."""
        if not text or not text.strip():
            return ""
        encoded_text = quote(text.strip(), safe="")
        return f"https://discord.com/channels/@me?content={encoded_text}"

    @staticmethod
    def get_link_linkedin(text: str) -> str:
        """Share to LinkedIn with proper URL encoding."""
        if not text or not text.strip():
            return ""
        encoded_text = quote(text.strip(), safe="")
        encoded_url = quote("https://github.com/D3M-Sudo/Anura", safe="")
        return f"https://www.linkedin.com/sharing/share-offsite/?url={encoded_url}&summary={encoded_text}"

    @staticmethod
    def get_link_threads(text: str) -> str:
        """Share to Threads (Instagram's text-based platform)."""
        if not text or not text.strip():
            return ""
        encoded_text = quote(text.strip(), safe="")
        return f"https://www.threads.net/intent/post?text={encoded_text}"


# Thread-safe singleton instance for global app access
def get_share_service() -> ShareService:
    """Get thread-safe share service singleton."""
    return get_instance(ShareService)
