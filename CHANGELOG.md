# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

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
