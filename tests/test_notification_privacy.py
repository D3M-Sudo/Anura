# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""Desktop-notification privacy and lifecycle (#534, #537).

Notifications must not echo extracted text (lock-screen and notification
history exposure), and the application must clean up the same singleton that
the controllers use to create them.
"""

from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]


def _source(relative: str) -> str:
    return (_ROOT / relative).read_text(encoding="utf-8")


def test_ocr_notification_does_not_include_extracted_text():
    source = _source("anura/controllers/ocr_controller.py")

    assert "text[:80]" not in source
    assert 'body=_("Text extracted successfully.")' in source


def test_application_uses_the_shared_notification_service():
    source = _source("anura/main.py")

    assert "self.notification_service = get_notification_service()" in source
    assert "NotificationService(APP_ID)" not in source


def test_controllers_use_the_same_lookup():
    source = _source("anura/controllers/ocr_controller.py")

    assert "get_notification_service()" in source
