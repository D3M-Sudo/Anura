# tests/test_services.py
#
# Unit tests for Anura services
# No GTK/GLib required — pure Python only with mocks




class TestLanguageManagerBasics:
    """Basic tests for LanguageManager without filesystem dependencies."""

    def test_language_mapping_completeness(self):
        """Test that all language codes in LANG_MAP have corresponding entries."""
        from anura.language_manager import language_manager

        # Test that common languages are mapped
        assert language_manager.get_language("eng") == "English"
        assert language_manager.get_language("ita") == "Italian"
        assert language_manager.get_language("fra") == "French"
        assert language_manager.get_language("deu") == "German"

        # Test that unknown codes return the code itself
        assert language_manager.get_language("unknown") == "unknown"

    def test_language_item_creation(self):
        """Test LanguageItem creation and properties."""
        from anura.types.language_item import LanguageItem

        item = LanguageItem(code="eng", title="English")
        assert item.code == "eng"
        assert item.title == "English"

    def test_get_language_item_valid_codes(self):
        """Test getting language items for valid codes."""
        from anura.language_manager import language_manager

        item = language_manager.get_language_item("eng")
        assert item is not None
        assert item.code == "eng"
        assert item.title == "English"

        # Test invalid code returns None
        item = language_manager.get_language_item("invalid")
        assert item is None
