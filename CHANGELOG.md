# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

## [0.1.5] - 2026-06-15 {version-0.1.5-architectural-milestone}

### Added
- Implemented **Controller-based Composition Architecture**; dismantled legacy mixins for OCR, TTS, and DnD
- Introduced immutable **OcrResult** and **OcrWord** dataclasses with `slots=True` for optimized memory and performance
- Added boot-time **Capability Audit** (`ApplicationContext`) to detect system dependencies (Tesseract, ZXing, GStreamer)
- Implemented proactive **UI Sensitivity Binding** to prevent runtime failures on unsupported environments
- Implemented **Deep Codebase Audit & Reliability Hardening** (v0.1.5 architecture)
- Replaced legacy `GObjectWorker` with `AtomicTaskManager` for single-slot task execution with UUID-based result validation
- Migrated `AnuraWindow` to a modular architecture using **Naked Mixins** (`WindowOCRMixin`, `WindowTTSMixin`, `WindowDnDMixin`)
- Implemented automated signal lifecycle management via `SignalManagerMixin` across all core widgets and services
- Added modular **Image Filter Chain** (`anura/utils/image_filters.py`) for extensible OCR preprocessing
- Integrated `StructuralReconstructor` for spatial layout analysis and paragraph merging
- Replaced `pyzbar` with `zxing-cpp` for more robust and reliable barcode and QR code detection
- Expanded the test suite to **437 tests**, including 393 unit tests (Non-GTK) and 44 integration tests (GTK)
- Added comprehensive security-focused tests for DoS prevention and structural UI verification
- Added support for Tesseract multi-language pooling in `~/.cache/anura/tessdata_pool/`
- Added keyboard shortcut hints and empty search state in the language selector
- Added 'All files (*)' filter to the image selection dialog
- Improved pluralization and internationalization support for text statistics

### Fixed
- Fixed **GStreamer Bus Memory Safety** using `weakref` closures to prevent reference cycles in `TTSService`
- Fixed silent scanning failures by implementing explicit **Dependency Fail-Fast** propagation
- Fixed critical race conditions in OCR processing by invalidating stale tasks in `AtomicTaskManager`
- Resolved memory leaks by ensuring automated signal disconnection via `connect_tracked()`
- Fixed `Gtk.FileFilter` regression to prevent duplicate entries on portal backends like LXQt and GNOME
- Corrected `Gio.File.query_info_async` implementation by providing exact positional arguments
- Resolved layout reflow issues where `Gtk.TextView` content was clipped in GTK4
- Fixed `__slots__` conflict and potential `AttributeError` in `ClipboardService`
- Improved error handling for missing Tesseract languages with `Adw.Toast` feedback
- Fixed keyboard shortcuts to use universal key names (F1, K) for cross-layout compatibility
- Resolved navigation focus race conditions and spinner animation states

### Security
- Implemented **Resource-based DoS Protection** by validating image file sizes (`MAX_IMAGE_SIZE_BYTES`) before processing
- Hardened text extraction with `validators.sanitize_text`, stripping Unicode Control (Cc) and Format (Cf) characters
- Hardened URL validation and encoding in `ShareService` against injection and RTL spoofing attacks

### Changed
- Optimized OCR pipeline by unifying Tesseract parsing into a single $O(N)$ pass
- Standardized file headers across the entire repository for project-wide consistency
- Updated Tesseract language identifier for German Fraktur to the correct `deu_latf` code
- Optimized multi-monitor support with improved DPI scaling (`notify::scale-factor`)
- Standardized UI placeholders and messages with Unicode ellipses (…) following GNOME HIG
- Renamed application ID from com.github.d3msudo.anura to io.github.d3msudo.anura
- Updated GitHub Actions to major versions (checkout@v6, upload-artifact@v7) for CI reliability

### Removed
- Removed legacy `gobject_worker.py` and all direct `GLib.idle_add` emissions for task results
- Deleted the legacy `po/com.github.d3msudo.anura.pot` file

## [0.1.4.3] - 2026-05-16 {version-0.1.4.3}

### Added

- Advanced TextPreprocessor utility with intelligent image enhancement and OCR text cleanup
- Smart text preprocessing including common OCR error correction, whitespace normalization, and punctuation fixing
- Structured data extraction from OCR text (emails, URLs, phone numbers, dates)
- Adaptive image enhancement based on brightness/contrast analysis for better OCR accuracy
- Modern ShortcutsOverlay widget with live search and categorized keyboard shortcuts
- Enhanced keyboard shortcuts overlay with search functionality and elegant Adw.Window-based interface
- Configurable logging level via `ANURA_LOG_LEVEL` environment variable for debugging
- Host screenshot fallback system using `flatpak-spawn --host` for missing portal backends
- Persistent install-hint banner when screenshot portal backend is missing
- Desktop-aware portal advice messages with environment-specific guidance
- Enhanced diagnostic logging for host screenshot operations
- Comprehensive drag-and-drop functionality with visual feedback and proper lifecycle management
- Complete drag-and-drop event handlers (enter, leave, motion, drop) with CSS styling for hover states
- Enhanced AboutDialog with complete legal information for Flathub compliance
- Full copyright and MIT license text for transparency
- Open source dependencies attribution in legal information
- Complete legal information ensuring Flathub compliance requirements
- Asynchronous Drag-and-Drop implementation to prevent UI freezes, especially in VM environments
- Fallback for URI list on clipboard texture read failure
- Optimized image thresholding using Look-Up Tables (LUT) for performance
- Enhanced accessibility and Micro-UX improvements for the OCR results page
- Persistent Drag-and-Drop controller for better stability
- Clickable QR URL notifications via XDG Desktop Portal (Flatpak-safe)
- Autocopy for QR-detected URLs with improved toast feedback
- Pattern-based file filters for image selection dialog
- Real-time word count status bar in OCR results page
- Standardized localization infrastructure and Application ID

### Fixed

- Fixed notification service cleanup by removing incorrect underscore reference
- Fixed URI validator function call in window.py for proper URL validation
- Fixed dialog response handling for browser launch failures with proper error management
- Fixed extra language combo signal connection to ensure it's always connected regardless of settings
- Fixed modal property removal from shortcuts window for better user experience
- Fixed keyboard shortcuts test to match correct method signature with _param parameter
- Fixed five UI/runtime bugs from Flatpak debug log
- Fixed three additional bugs (release notes parse, TTS AttributeError, screenshot diagnostic)
- Fixed Gio.Subprocess.wait() method usage instead of wait_sync()
- Fixed host screenshot file existence check with retry loop
- Fixed designer credit and share-row action prefix corrections
- Fixed incomplete URL substring sanitization (security fix)
- Resolved multiple critical runtime bugs, memory leaks, and signal leaks across core services
- Fixed X11 Drag-and-Drop deadlocks and portal file transfer freezes
- Corrected Text-to-Speech (TTS) state transitions, visual feedback, and "zombie audio" issues
- Fixed localization initialization and updated Italian translations
- Fixed broken status window in "Legal Information" page
- Resolved GTK navigation warnings and ruff linting violations (E501, W292)
- Fixed About dialog property names and legal information display
- Improved error handling for browser launch and file filters
- Fixed UI spinner animations and state management
- Fixed missing trailing newline in anura/window.py
- Fixed path traversal vulnerability in LanguageManager.remove_language (HIGH severity)
- Fixed URL userinfo spoofing in uri_validator (security fix)
- Fixed URL truncation during QR code extraction and hand-off
- Fixed clipboard infinite fallback loop on image read failures
- Fixed callback exception handling in clipboard service
- Fixed Gio.Notification API usage for XDG Portal compatibility
- Fixed i18n bindings in Flatpak and globalized autocopy behavior
- Fixed Flatpak hybrid UI regression (i18n)
- Fixed localization issues and cleaned up UI code
- Fixed broken state warning on Acknowledgements page
- Fixed navigation focus race condition
- Removed compiled gresource from git tracking and updated .gitignore
- Fixed line length violation in notification service tests

### Changed

- Enhanced screenshot service with host fallback capabilities
- Improved error handling and logging throughout the application
- Better portal environment diagnostics and user guidance
- Updated release notes generation logic with hybrid GitHub link display
- Lower threshold for GitHub link from 15 to 12 items for better UX
- Enhanced drag-and-drop drop target attachment to welcome page widget
- Improved release notes generation with tracking for truncated sections
- Refactored Drag-and-Drop system for improved reliability
- Optimized Flatpak build and updated dependencies (urllib3)
- Improved OCR pipeline and image processing performance
- Deep codebase audit and concurrency hardening across all services
- Pre-compiled regex patterns and optimized PIL thresholding for performance
- Optimized URI validation performance with compiled regex
- Optimized image enhancement pipeline
- Optimized QR code detection by restricting symbol scan
- i18n: full audit and fixed hardcoded UI strings across the application
- i18n: stabilized infrastructure and synchronized translations (Phase 1A)
- i18n: finalized Italian localization and fixed navigation focus (Phase 1B)
- Palette: UX and accessibility improvements across ExtractedPage
- Refactored language API, removed dead code, improved test coverage
- Standardized loading spinner size across the application
- Updated testing documentation

## [0.1.4.2] - 2026-05-05 {version-0.1.4.2}

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

## [0.1.4.1] - 2026-05-02 {version-0.1.4.1}

### Fixed

- Fixed missing `Adw.init()` call causing "greyed out UI" on some systems
- Fixed GResource bundle loading to properly exit on failure instead of continuing with broken UI
- Fixed notification portal API to use proper GLib.Variant format (a{sv}) for XDG Portal compatibility
- Fixed notification import consistency with absolute imports throughout main.py
- Fixed HTML escaping in release notes generation to prevent XSS vulnerabilities

### Changed

- Added CHANGELOG.md as source of truth for release notes
- Added translate URL to metainfo for Weblate integration

## [0.1.4] - 2026-05-01 {version-0.1.4}

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

## [0.1.3] - 2026-04-25 {version-0.1.3}

### Fixed

- Fixed import error in screenshot service (tessdata_config casing)
- Fixed missing init_tessdata() method in LanguageManager
- Fixed settings module path mismatch (moved to anura/services/settings.py)
- Fixed blueprint-compiler GIRepository compatibility with GNOME Platform 49

### Changed

- Improved TTS cache file location (XDG_CACHE_HOME)

## [0.1.0] - 2026-04-23 {version-0.1.0}

### Added

- Initial release of Anura (fork of Frog)
- Complete rebranding to Anura
- Removed all telemetry and PostHog tracking for total privacy
- Optimized sharing service: added X (formerly Twitter) and Instagram
- Updated dependencies for modern Linux distributions
