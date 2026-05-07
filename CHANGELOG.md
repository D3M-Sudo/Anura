# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added
- SignalManagerMixin for centralized signal tracking and automatic cleanup to prevent memory leaks
- ThreadSafeSingleton class with double-checked locking pattern for thread-safe service initialization
- Thread-safe GObjectWorker utility for background operations with proper GLib.idle_add integration
- cleanup_orphaned_resources() function for automatic cleanup of old TTS cache and temporary files
- DownloadState dataclass for tracking OCR model download progress
- LanguageItem GObject type for language list management with Gio.ListStore integration
- Keyboard shortcuts: Ctrl+? and Ctrl+/ for displaying shortcuts window
- Keyboard shortcut: Ctrl+V for paste from clipboard functionality
- Automatic URL extraction from OCR text with optional auto-opening via autolinks setting
- Screenshot safety timeout (30 seconds) to prevent window hiding on portal hang
- Comprehensive test suite with 10 new test files covering core services and utilities
- AGENTS.md documentation for AI assistant integration and development guidance
- Code quality workflow command with systematic 5-phase audit and refactoring process
- Pure-Python share_utils module with URL validation and provider link generation

### Changed
- Settings service moved to services/ with lazy initialization pattern for CLI-only operation
- Share service extracted pure-Python utilities to share_utils.py for better testability
- Reddit URL encoding improved with title/body separation for short vs long texts
- Mastodon sharing enhanced with web+mastodon:// scheme and instance selection fallback
- Updated Python version requirement from 3.11 to 3.12 in project documentation
- CI workflow updated to include pytest step before Flatpak build
- pytest configuration updated with proper ignore patterns for GTK-dependent tests
- All services now use ThreadSafeSingleton pattern for thread-safe initialization
- Image processing now validates file size (50MB limit) and uses os.lstat() for symlink protection
- Clipboard service enhanced with atomic cancellation and timeout management
- Screenshot service improved with performance timing and better error handling
- Refactored complex application methods into smaller, focused helper functions for better maintainability
- Improved code organization with single responsibility principle across main.py and screenshot_service.py
- Enhanced error handling patterns with dedicated exception handling methods
- Simplified image processing logic by separating QR detection and OCR extraction concerns
- Reduced cyclomatic complexity from 12+ to ≤10 per method throughout codebase
- Standardized code formatting with consistent double quotes and trailing commas in multi-line calls

### Fixed
- Fixed time.monotonic() usage in cleanup.py by replacing with time.time() for file modification checks
- Removed OCR text logging in main.py to protect user privacy and prevent sensitive data exposure
- Fixed empty copy=False branch in on_decoded() by adding proper notification for non-copy operations
- Fixed test_keyboard_shortcuts.py by adding @pytest.mark.gtk markers to prevent GTK import errors
- Updated obsolete CI comment to reflect current pytest integration
- Fixed memory leaks through proper signal disconnection using SignalManagerMixin
- Fixed symlink bypass vulnerability by using os.lstat() instead of os.stat() for file size validation
- Fixed race conditions in service initialization through ThreadSafeSingleton implementation
- Fixed clipboard timeout handling with atomic operations and proper cleanup
- Fixed URL length validation in share service to prevent overflow attacks
- Replaced try-except-pass patterns with contextlib.suppress() for cleaner error handling
- Fixed inconsistent string quotes by standardizing to double quotes throughout codebase
- Fixed missing docstrings for all public methods following PEP 257 conventions
- Fixed trailing comma issues in multi-line function calls for better readability
- Fixed import sorting and organization issues across all modules
- Fixed code complexity by extracting complex methods into smaller, focused functions
- Fixed threading import issues and type hint consistency in main.py
- Fixed unused variable warnings and code quality issues


## [0.1.4.2] - 2026-05-05

### Fixed
- Fixed `__slots__` conflict in ClipboardService - missing `_cancellable` in declaration causing AttributeError
- Fixed ruff linting errors across codebase including import sorting and code style issues
- Fixed concurrency issues in TTS and clipboard services against race conditions
- Fixed memory leaks and added structural robustness throughout application
- Fixed API contract, thread safety, and race condition issues in core services
- Fixed Flatpak manifest warnings by removing `_comment` properties

### Changed
- Extracted URI validation to utils module and relaxed IP/localhost restrictions
- Improved code quality with comprehensive type hints and cleanup
- Implemented atomic cancellation for Clipboard and thread-safe signal emission for TTS GStreamer bus
- Enhanced thread safety patterns across all services
- Added comprehensive unit tests for core services
- Resolved all remaining linting errors and line length issues

## [0.1.4.1] - 2026-05-02

### Fixed
- Fixed missing `Adw.init()` call causing "greyed out UI" on some systems
- Fixed GResource bundle loading to properly exit on failure instead of continuing with broken UI
- Fixed notification portal API to use proper GLib.Variant format (a{sv}) for XDG Portal compatibility
- Fixed notification import consistency with absolute imports throughout main.py
- Fixed HTML escaping in release notes generation to prevent XSS vulnerabilities

### Changed
- Added CHANGELOG.md as source of truth for release notes
- Added translate URL to metainfo for Weblate integration

## [0.1.4] - 2026-05-01

### Fixed
- Fixed critical thread-safety issues and race conditions in language manager and screenshot service
- Fixed memory leaks in widget lifecycle management and GStreamer bus watch
- Fixed all Flatpak manifest dependencies (requests, urllib3, certifi, hatchling, pyzbar)
- Fixed blueprint compiler output directory for Flatpak builds
- Fixed gresource bundle loading with correct UI file paths
- Fixed filesystem permissions for Open Image and Drag & Drop in sandbox
- Fixed silent CLI mode to properly exit without opening UI window
- Fixed CLI exit code to return 0 on success instead of 1
- Fixed code quality issues: lint errors, import sorting, gettext shadowing
- Fixed Telegram share URL to send text as message instead of URL

### Changed
- Updated OARS content rating for Flathub compliance
- Improved CI/CD workflow with smoke tests and build verification
- Updated tessdata-fast to pinned commit SHA for reproducible builds

## [0.1.3] - 2026-04-25

### Fixed
- Fixed import error in screenshot service (tessdata_config casing)
- Fixed missing init_tessdata() method in LanguageManager
- Fixed settings module path mismatch (moved to anura/services/settings.py)
- Fixed blueprint-compiler GIRepository compatibility with GNOME Platform 49

### Changed
- Improved TTS cache file location (XDG_CACHE_HOME)

## [0.1.0] - 2026-04-23

### Added
- Initial release of Anura (fork of Frog)
- Complete rebranding to Anura
- Removed all telemetry and PostHog tracking for total privacy
- Optimized sharing service: added X (formerly Twitter) and Instagram
- Updated dependencies for modern Linux distributions
