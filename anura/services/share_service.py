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

    def __init__(self):
        super().__init__()
        self.launcher = Gtk.UriLauncher()

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
                share_link: str = handler(quote(text, safe=''))
                # Validate URL length before attempting to launch
                if len(share_link) > self.MAX_URL_LENGTH:
                    logger.warning(f"Anura Share: URL too long ({len(share_link)} chars, max {self.MAX_URL_LENGTH})")
                    return
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

    # NOTE: get_link_instagram removed — Instagram has no URL prefill API
    # If Instagram adds sharing URL support in the future, re-enable:
    # @staticmethod
    # def get_link_instagram(text: str):
    #     return None  # Not supported

    @staticmethod
    def get_link_email(text: str):
        return f"mailto:?body={text}"
