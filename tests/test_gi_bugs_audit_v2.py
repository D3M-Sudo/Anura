# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import time
from unittest.mock import MagicMock, patch

from PIL import Image
import pytest

pytest.importorskip("gi")

from anura.core.atomic_task_manager import AtomicTaskManager
from anura.utils.image_filters import AdaptiveThresholdFilter


def test_new_01_deadlock_prevention():
    """
    Verify that execute_isolated does not deadlock by calling it.
    This bug was caused by a non-reentrant lock being acquired twice.
    """
    mgr = AtomicTaskManager()

    def dummy_command(*args, **kwargs):
        return "done"

    # This would deadlock before the fix
    task_id = mgr.execute_isolated(dummy_command, args=())
    assert task_id is not None
    mgr.shutdown()


def test_new_02_interrupted_error_propagation_screenshot_service():
    """
    Verify that InterruptedError is correctly re-raised in _try_ocr_extraction.
    We mock the entire module to avoid Xdp dependency.
    """
    with patch("gi.require_version"):
        # Mocking the imports that fail
        with patch("gi.repository.Xdp", create=True):
            # We mock Settings class in anura.services.settings before importing screenshot_service
            with patch("anura.services.settings.Settings"):
                from anura.services.screenshot_service import ScreenshotService

                service = ScreenshotService.__new__(ScreenshotService)

    mock_img = MagicMock(spec=Image.Image)
    mock_img.mode = "L"

    # We patch settings in settings.py to avoid the RuntimeError in __getattr__
    # Using a different approach to bypass the proxy object's __getattr__
    with patch("anura.services.settings.settings._get_instance") as mock_get_instance:
        mock_settings = MagicMock()
        mock_get_instance.return_value = mock_settings
        mock_settings.get_string.return_value = "full"
        with patch("anura.services.screenshot_service.get_text_preprocessor") as mock_get_pre:
            mock_pre = MagicMock()
            mock_get_pre.return_value = mock_pre
            mock_pre.enhance_image.side_effect = InterruptedError("Cancelled")
            with pytest.raises(InterruptedError):
                service._try_ocr_extraction(mock_img, "eng", time.time(), task_id="test-task")


def test_new_03_interrupted_error_propagation_filters():
    """
    Verify that InterruptedError is correctly re-raised in AdaptiveThresholdFilter.
    """
    filt = AdaptiveThresholdFilter()
    mock_img = MagicMock(spec=Image.Image)

    with patch.object(filt, "_check_cancellation", side_effect=InterruptedError("Cancelled")):
        with pytest.raises(InterruptedError):
            filt.apply(mock_img, task_id="test-task")


def test_new_06_ipc_outside_lock_logic():
    """
    Mental/Logic check for NEW-06. Since we can't easily benchmark micro-stutters,
    we verify that the state is consistent after execute_isolated.
    """
    mgr = AtomicTaskManager()

    def dummy_command(*args, **kwargs):
        return "done"

    # We must mock the actual background process submission to avoid race conditions
    # with the result_wrapper cleaning up the map.
    with patch("concurrent.futures.ProcessPoolExecutor.submit"):
        task_id = mgr.execute_isolated(dummy_command)

        # Verify the task is in the cancellation map and NOT cancelled
        assert mgr._isolated_cancellation_map[task_id] is False

        # Start a new task, verifying the old one is marked as cancelled
        old_task_id = task_id
        new_task_id = mgr.execute_isolated(dummy_command)

        assert mgr._isolated_cancellation_map[old_task_id] is True
        assert mgr._isolated_cancellation_map[new_task_id] is False

    mgr.shutdown()


def test_new_05_silent_reset_on_cancellation():
    """
    Verify that run_ocr_pipeline returns (False, None, None, None) on InterruptedError,
    which triggers the silent reset in _on_isolated_complete.
    """
    with patch("gi.require_version"):
        with patch("gi.repository.Xdp", create=True):
            from anura.services.screenshot_service import run_ocr_pipeline

    with patch("anura.utils.barcode_detector.detect_barcodes", side_effect=InterruptedError()):
        # Create a dummy file for the pipeline
        with patch("os.path.exists", return_value=True), patch(
            "os.path.getsize", return_value=100
        ), patch("PIL.Image.open"):
            result = run_ocr_pipeline("eng", "dummy.png", "off", task_id="test")
            assert result == (False, None, None, None)
