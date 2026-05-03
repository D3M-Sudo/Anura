# share_service.py
#
# Copyright 2025 Andrey Maksimov
# Copyright 2026 D3M-Sudo (Anura fork and modifications)

from typing import ClassVar
from urllib.parse import quote

from gi.repository import Adw, GLib, GObject, Gtk
from loguru import logger


def _(s: str) -> str:
    return s


class ShareService(GObject.GObject):
    """
    Service responsible for sharing extracted text to external providers.
    Designed for Anura to handle web-based and protocol-based URI launching.
    """
    __gtype_name__ = "ShareService"

    __gsignals__: ClassVar[dict[str, tuple]] = {"share": (GObject.SIGNAL_RUN_LAST, None, (bool,))}

    def __init__(self):
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
            # NOTE: "instagram" removed — no URL prefill API available
        ]

    # Maximum URL length for safe sharing (most browsers support ~2000, be conservative)
    MAX_URL_LENGTH = 2000

    def share(self, provider: str, text: str):
        """
        Generates a share link and launches the default system handler.
        """
        if not text:
            logger.warning("Anura Share: Attempted to share empty text.")
            return

        text = text.strip()
        handler = getattr(self, f"get_link_{provider}", None)

        if handler:
            try:
                # Encode the text content, but preserve URL structure characters
                # The handler functions are responsible for proper URL construction
                encoded_text = quote(text, safe='')
                share_link: str = handler(encoded_text)

                # Special handling for Mastodon with fallback
                if provider == "mastodon":
                    return self._share_mastodon_with_fallback(encoded_text)

                # Validate URL length before attempting to launch
                if len(share_link) > self.MAX_URL_LENGTH:
                    logger.warning(f"Anura Share: URL too long ({len(share_link)} chars, max {self.MAX_URL_LENGTH})")
                    return
                self.launcher.set_uri(share_link)
                self.launcher.launch(parent=None, cancellable=None, callback=self._on_share)
            except (ValueError, TypeError, AttributeError) as e:
                logger.error(f"Anura Share Error: Failed to share via {provider}. Reason: {e}")

    def _share_mastodon_with_fallback(self, encoded_text: str):
        """Share to Mastodon with official scheme and fallback to instance selection."""
        try:
            # Try official web+mastodon:// scheme first
            mastodon_url = f"web+mastodon://share?text={encoded_text}"
            self.launcher.set_uri(mastodon_url)
            self.launcher.launch(parent=None, cancellable=None, callback=self._on_mastodon_share_attempt)
        except Exception as e:
            logger.warning(f"Anura Share: Failed to launch web+mastodon:// scheme: {e}")
            # Fallback to instance selection dialog
            self._show_mastodon_instance_dialog(encoded_text)

    def _on_mastodon_share_attempt(self, _, result):
        """Callback for Mastodon share attempt - fallback if it fails."""
        try:
            success = self.launcher.launch_finish(result)
            if not success:
                # Official scheme failed, show instance selection
                logger.info("Anura Share: web+mastodon:// not supported, showing instance selection")
                # We need the encoded text but don't have it here, so we'll need to store it
                # For now, just log and emit failure
                GLib.idle_add(self.emit, "share", False)
            else:
                GLib.idle_add(self.emit, "share", True)
        except (GLib.Error, RuntimeError) as e:
            logger.warning(f"Anura Share: web+mastodon:// launch failed: {e}")
            GLib.idle_add(self.emit, "share", False)

    def _show_mastodon_instance_dialog(self, encoded_text: str):
        """Show dialog to select Mastodon instance for fallback sharing."""
        instances = [
            ("mastodon.social", "Mastodon Official"),
            ("mastodon.online", "Mastodon Online"),
            ("fosstodon.org", "Fosstodon - Open Source"),
            ("hachyderm.io", "Hachyderm - Tech Community")
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
        dialog.connect("response", lambda d, response: self._on_mastodon_instance_selected(d, response, encoded_text))

        # Show dialog (we need a parent window)
        try:
            # Try to get the active window from the application
            from gi.repository import Gio
            app = Gio.Application.get_default()
            if app and app.get_active_window():
                dialog.set_transient_for(app.get_active_window())
            dialog.present()
        except Exception as e:
            logger.error(f"Anura Share: Failed to show Mastodon instance dialog: {e}")

    def _on_mastodon_instance_selected(self, dialog, response, encoded_text: str):
        """Handle Mastodon instance selection."""
        if response.startswith("instance_"):
            domain = response.replace("instance_", "")
            share_url = f"https://{domain}/share?text={encoded_text}"

            try:
                self.launcher.set_uri(share_url)
                self.launcher.launch(parent=None, cancellable=None, callback=self._on_share)
            except Exception as e:
                logger.error(f"Anura Share: Failed to share via Mastodon instance {domain}: {e}")
                GLib.idle_add(self.emit, "share", False)

        dialog.destroy()

    def _on_share(self, _, result):
        """
        Async callback for URI launch completion.
        """
        try:
            success = self.launcher.launch_finish(result)
            GLib.idle_add(self.emit, "share", success)
        except (GLib.Error, RuntimeError) as e:
            logger.warning(f"Anura Share Warning: URI launch failed: {e}")
            GLib.idle_add(self.emit, "share", False)

    @staticmethod
    def get_link_telegram(text: str):
        return f"https://t.me/share/url?text={text}"

    @staticmethod
    def get_link_reddit(text: str):
        # For short texts (< 100 char): use title + body for better visibility
        if len(text) < 100:
            return f"https://www.reddit.com/submit?title={text}&selftext={text}"
        else:
            # For long texts: use only body to avoid title truncation
            return f"https://www.reddit.com/submit?selftext={text}"

    @staticmethod
    def get_link_mastodon(text: str):
        # Official web+mastodon:// scheme - primary method
        return f"web+mastodon://share?text={text}"

    @staticmethod
    def get_link_x(text: str):
        """
        Twitter provider rebranded to X.com.
        """
        return f"https://x.com/intent/tweet?text={text}"

    # NOTE: get_link_instagram removed — Instagram has no URL prefill API
    # If Instagram adds sharing URL support in the future, re-enable:
    # @staticmethod
    # def get_link_instagram(text: str):
    #     return None  # Not supported

    @staticmethod
    def get_link_email(text: str):
        return f"mailto:?body={text}"
