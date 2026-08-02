# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

from unittest.mock import MagicMock

import pytest


def test_ocr_controller_window_destroyed_safety(headless_gi_mocks):
    """Verify that OcrController handles window destruction gracefully in callbacks."""
    import gc

    from anura.controllers.ocr_controller import OcrController

    class MockWindow:
        def __init__(self):
            self.backend = MagicMock()
            self.portal_banner = MagicMock()
        def register_controller(self, ctrl):
            pass

    window = MockWindow()
    ctrl = OcrController(window)

    # Simulate window destruction
    del window
    gc.collect()

    # Verify that calling _on_shot_done does not crash with ReferenceError
    try:
        ctrl._on_shot_done(MagicMock(), "extracted text", True, MagicMock(), "eng")
    except ReferenceError:
        pytest.fail("ReferenceError raised in _on_shot_done when window was destroyed!")
