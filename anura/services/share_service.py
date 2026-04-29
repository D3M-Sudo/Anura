# share_service.py
#
# Copyright 2025 Andrey Maksimov
# Copyright 2026 D3M-Sudo (Anura fork and modifications)

from typing import List
from urllib.parse import quote

from gi.repository import GObject, Gtk
from loguru import logger


class ShareService(GObject.GObject):
    """
    Service responsible for sharing extracted text to external providers.
    Designed for Anura to handle web-based and protocol-based URI launching.
    """
    __gtype_name__ = "ShareService"

    __gsignals__ = {"share": (GObject.SIGNAL_RUN_LAST, None, (bool,))}

    launcher: Gtk.UriLauncher = Gtk.UriLauncher()

    def __init__(self):
        super().__init__()

    @staticmethod
    def providers() -> List[str]:
        """
        Returns a list of supported share providers.
        """
        return [
            "email",
            "mastodon",
            "reddit",
            "telegram",
            "x",
            "instagram",
        ]

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
                share_link: str = handler(quote(text))
                self.launcher.set_uri(share_link)
                self.launcher.launch(parent=None, cancellable=None, callback=self._on_share)
            except Exception as e:
                logger.error(f"Anura Share Error: Failed to share via {provider}. Reason: {e}")

    def _on_share(self, _, result):
        """
        Async callback for URI launch completion.
        """
        try:
            success = self.launcher.launch_finish(result)
            self.emit("share", success)
        except Exception as e:
            logger.warning(f"Anura Share Warning: URI launch failed: {e}")
            self.emit("share", False)

    @staticmethod
    def get_link_telegram(text: str):
        return f"tg://msg_url?url={text}"

    @staticmethod
    def get_link_reddit(text: str):
        return f"https://www.reddit.com/submit?title={text}"

    @staticmethod
    def get_link_mastodon(text: str):
        return f"https://sharetomastodon.github.io/?title={text}"

    @staticmethod
    def get_link_x(text: str):
        """
        Twitter provider rebranded to X.com.
        """
        return f"https://x.com/intent/tweet?text={text}"

    @staticmethod
    def get_link_instagram(text: str):
        """
        Instagram doesn't support text-prefill via URL. 
        Opening the direct web-create page as a fallback.
        """
        return "https://www.instagram.com/reels/create/"

    @staticmethod
    def get_link_email(text: str):
        return f"mailto:?body={text}"