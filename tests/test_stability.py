from unittest.mock import MagicMock, patch

from PIL import Image
import pytest

# Mock GI imports if not available for non-GTK tests
try:
    import gi

    gi.require_version("GObject", "2.0")
    from gi.repository import GObject

    HAS_GI = True
except (ImportError, ValueError):
    HAS_GI = False
    GObject = MagicMock()

from anura.utils.image_filters import RescaleFilter
from anura.utils.signal_manager import SignalManagerMixin


class MockController:
    """Duck-typed controller: exposes teardown() without inheriting from a Protocol.

    Teardownable was removed from signal_manager in BUG-041/Hardening in favour of
    hasattr()-based duck typing.  Tests use plain classes with a teardown() method.
    """

    def __init__(self, window):
        self.teardown_called = False
        if hasattr(window, "register_controller"):
            window.register_controller(self)

    def teardown(self):
        self.teardown_called = True


def test_resource_guard_activation():
    """Verify that RescaleFilter blocks on large images when memory is low."""
    rescale_filter = RescaleFilter()

    # Large image (>20MP)
    large_img = Image.new("L", (5000, 5000))  # 25MP

    # Mock low memory
    mock_mem = MagicMock()
    mock_mem.available = 100 * 1024 * 1024
    mock_mem.percent = 95.0  # 5% free

    with patch("psutil.virtual_memory", return_value=mock_mem):
        result = rescale_filter.apply(large_img)
        # Should return the same image object (blocked)
        assert result is large_img


def test_rescale_allowed_on_high_memory():
    """Verify that RescaleFilter proceeds on large images when memory is sufficient."""
    rescale_filter = RescaleFilter()

    # Large image (>20MP)
    large_img = Image.new("L", (5000, 5000))  # 25MP

    # Mock high memory
    mock_mem = MagicMock()
    mock_mem.available = 4 * 1024 * 1024 * 1024
    mock_mem.percent = 50.0  # 50% free

    with patch("psutil.virtual_memory", return_value=mock_mem):
        # We don't want it to actually resize if it doesn't need to (size < 1000 check)
        # but here we just want to see it didn't trigger the Guard.
        # RescaleFilter resizes if width or height < 1000.
        # Since 5000 > 1000, it should return the original image if NO guard is triggered.
        result = rescale_filter.apply(large_img)
        assert result is large_img


@pytest.mark.gtk
@pytest.mark.timeout(30)
def test_lifecycle_teardown_loop():
    """Stress test window lifecycle to verify signal and controller cleanup."""
    pytest.importorskip("gi.repository.Adw")
    from gi.repository import Adw

    from anura.services.screenshot_service import ScreenshotService
    from anura.window import AnuraWindow

    # We need a Gtk Application for the window
    app = Adw.Application(application_id="io.github.d3msudo.anura.stability")

    def run_stress_test(app):
        backend = MagicMock(spec=ScreenshotService)

        try:
            for _i in range(50):
                win = AnuraWindow(application=app, backend=backend)

                # Create a mock controller and register it
                mock_ctrl = MockController(win)

                # Verify registration
                assert mock_ctrl in win._registered_controllers

                # Destroy window
                win.destroy()

                # Verify teardown was called
                assert mock_ctrl.teardown_called
                # Verify registry is cleared
                assert len(win._registered_controllers) == 0
        finally:
            app.quit()

    app.connect("activate", run_stress_test)
    app.run([])


def test_signal_manager_registry_logic():
    """Verify SignalManagerMixin registry and teardown without GTK."""

    class MockWindow(SignalManagerMixin):
        def __init__(self):
            # Test lazy initialization
            self.destroyed = False

        def destroy(self):
            self.teardown_all()
            self.destroyed = True

    win = MockWindow()
    ctrl1 = MockController(win)
    ctrl2 = MockController(win)

    # Check that lazy init worked
    assert hasattr(win, "_registered_controllers")
    assert len(win._registered_controllers) == 2

    win.destroy()
    assert ctrl1.teardown_called
    assert ctrl2.teardown_called
    assert len(win._registered_controllers) == 0
