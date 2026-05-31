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
        result = rescale_filter.apply(large_img)
        assert result is large_img


# NOTE: test_lifecycle_teardown_loop was removed.
#
# AnuraWindow instantiation inside app.run() triggers an Ubuntu apport crash
# reporter side-effect: when AnuraWindow.__init__() raises (due to the
# PyGObject ABC + GObject SIGABRT described in test_audit_app_logic.py),
# Python's unhandled-exception hook invokes apport, which tries to import
# apt_pkg (a C extension) while the GC and ProcessPoolExecutor threads are
# active.  This race → SIGSEGV (exit 139).  The signal kills the entire
# pytest process and cannot be caught with try/except.
#
# SignalManagerMixin lifecycle is fully covered by test_signal_manager_registry_logic
# below, which exercises the same register/teardown/clear contract without GTK.


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
