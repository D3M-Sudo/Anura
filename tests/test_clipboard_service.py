# test_clipboard_service.py
#
# Unit tests for ClipboardService
# Tests clipboard read/write operations and error handling

from unittest.mock import Mock, patch

from anura.services.clipboard_service import ClipboardService


class TestClipboardService:
    """Test suite for ClipboardService core functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = ClipboardService()
        # Mock clipboard to avoid Gdk dependency
        self.service._clipboard = Mock()

    def test_init(self):
        """Test service initialization."""
        assert self.service._clipboard is not None
        assert self.service._clipboard_timeout_id is None
        assert self.service._cancellable is None

    def test_copy_text_success(self):
        """Test successful text copying to clipboard."""
        test_text = "Sample text to copy"

        with patch("anura.services.clipboard_service.GLib") as mock_glib:
            self.service.copy_text(test_text)

            self.service._clipboard.set_text.assert_called_once_with(test_text)
            mock_glib.timeout_add_seconds.assert_called_once()

    def test_copy_text_empty(self):
        """Test copying empty text."""
        with patch("anura.services.clipboard_service.GLib") as mock_glib:
            self.service.copy_text("")

            self.service._clipboard.set_text.assert_called_once_with("")
            mock_glib.timeout_add_seconds.assert_called_once()

    def test_copy_text_with_cancellation(self):
        """Test text copying with existing pending operations."""
        # Set up existing operation
        self.service._cancellable = Mock()
        self.service._clipboard_timeout_id = 123

        with patch("anura.services.clipboard_service.GLib") as mock_glib:
            self.service.copy_text("new text")

            # Should cancel existing operations
            self.service._cancellable.cancel.assert_called_once()
            mock_glib.source_remove.assert_called_once_with(123)

    def test_read_text_success(self):
        """Test successful text reading from clipboard."""

        # Mock the async read operation
        mock_future = Mock()
        self.service._clipboard.read_text_async.return_value = mock_future

        with patch("anura.services.clipboard_service.GLib") as mock_glib:
            self.service.read_text()

            self.service._clipboard.read_text_async.assert_called_once()
            mock_glib.timeout_add_seconds.assert_called_once()

    def test_read_text_with_cancellation(self):
        """Test text reading with existing pending operations."""
        # Set up existing operation
        self.service._cancellable = Mock()
        self.service._clipboard_timeout_id = 456

        mock_future = Mock()
        self.service._clipboard.read_text_async.return_value = mock_future

        with patch("anura.services.clipboard_service.GLib") as mock_glib:
            self.service.read_text()

            # Should cancel existing operations
            self.service._cancellable.cancel.assert_called_once()
            mock_glib.source_remove.assert_called_once_with(456)

    def test_on_text_read_success(self):
        """Test successful text read callback."""
        test_text = "Read text content"
        mock_source = Mock()
        self.service._clipboard_timeout_id = 789

        with patch("anura.services.clipboard_service.GLib") as mock_glib:
            self.service._on_text_read(mock_source, test_text)

            mock_glib.source_remove.assert_called_once_with(789)
            mock_glib.idle_add.assert_called_once()
            args = mock_glib.idle_add.call_args[0]
            assert args[0] == self.service.emit
            assert args[1] == "text-read"
            assert args[2] == test_text

    def test_on_text_read_empty(self):
        """Test empty text read callback."""
        mock_source = Mock()
        self.service._clipboard_timeout_id = 101

        with patch("anura.services.clipboard_service.GLib") as mock_glib:
            self.service._on_text_read(mock_source, "")

            mock_glib.source_remove.assert_called_once_with(101)
            mock_glib.idle_add.assert_called_once()
            args = mock_glib.idle_add.call_args[0]
            assert args[0] == self.service.emit
            assert args[1] == "text-read"
            assert args[2] == ""

    def test_on_text_read_error(self):
        """Test text read error callback."""
        mock_source = Mock()
        error = Exception("Test error")
        self.service._clipboard_timeout_id = 202

        with patch("anura.services.clipboard_service.GLib") as mock_glib:
            self.service._on_text_read(mock_source, None, error)

            mock_glib.source_remove.assert_called_once_with(202)
            mock_glib.idle_add.assert_called_once()
            args = mock_glib.idle_add.call_args[0]
            assert args[0] == self.service.emit
            assert args[1] == "text-read"
            assert args[2] == ""

    def test_cancel_pending_operations(self):
        """Test cancellation of pending operations."""
        # Set up pending operations
        mock_cancellable = Mock()
        self.service._cancellable = mock_cancellable
        self.service._clipboard_timeout_id = 303

        self.service.cancel_pending_operations()

        mock_cancellable.cancel.assert_called_once()
        assert self.service._cancellable is None
        assert self.service._clipboard_timeout_id is None

    def test_cancel_pending_operations_none(self):
        """Test cancellation when no operations are pending."""
        self.service.cancel_pending_operations()

        # Should not raise any errors
        assert self.service._cancellable is None
        assert self.service._clipboard_timeout_id is None

    def test_on_clipboard_timeout(self):
        """Test clipboard operation timeout."""
        mock_cancellable = Mock()
        self.service._cancellable = mock_cancellable

        with patch("anura.services.clipboard_service.GLib") as mock_glib:
            result = self.service._on_clipboard_timeout()

            mock_cancellable.cancel.assert_called_once()
            mock_glib.idle_add.assert_called_once()
            args = mock_glib.idle_add.call_args[0]
            assert args[0] == self.service.emit
            assert args[1] == "text-read"
            assert args[2] == ""
            assert result is False  # Should return False to not repeat timeout

    def test_cleanup_on_destroy(self):
        """Test cleanup when service is destroyed."""
        mock_cancellable = Mock()
        self.service._cancellable = mock_cancellable
        self.service._clipboard_timeout_id = 404

        self.service.cleanup()

        mock_cancellable.cancel.assert_called_once()
        assert self.service._cancellable is None
        assert self.service._clipboard_timeout_id is None
