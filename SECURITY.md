# Security Policy

## Reporting a Vulnerability

We take the security of Anura OCR seriously. If you believe you have found a security vulnerability, please report it to us as described below.

### Preferred Method: GitHub Security Advisories

**Please report security vulnerabilities using [GitHub Security Advisories](https://github.com/d3msudo/anura/security/advisories/new).**

This method enables:

- Private disclosure and discussion
- Coordinated vulnerability disclosure
- CVE assignment through GitHub
- Draft advisories before public disclosure

### Alternative Method: GitHub Issues

For non-sensitive security questions or general inquiries, you can open a [GitHub Issue](https://github.com/d3msudo/anura/issues). Please do NOT report sensitive vulnerabilities publicly — use GitHub Security Advisories for those.

## Supported Versions

Anura OCR is in active development. Security updates are provided for:

| Version | Supported          |
|---------|-------------------|
| 0.1.x   | :white_check_mark: |

This policy will be updated as the project matures.

## What to Report

### High Priority

- **Tesseract Injection**: Unvalidated `lang_code` arguments passed to pytesseract or tesseract process
- **Path Traversal**: Access to files outside intended directories (tessdata, TTS cache, downloads)
- **Command Injection**: Insufficient sanitization of paths or user input in shell commands
- **Data Exposure**: OCR text content exposed to unintended third-party services or without sanitization
- **Flatpak Sandbox Bypass**: Circumvention of `--filesystem=xdg-download` permissions or XDG portal restrictions

### Medium Priority

- **Denial of Service**: Crashes or resource exhaustion from malformed images (Pillow, pyzbar, pytesseract)
- **Race Conditions**: TOCTOU vulnerabilities in temporary file operations
- **Symlink Attacks**: Improper symlink handling in download or cache paths
- **URI Injection**: Bypass of URI validator in `window.py` (homograph attacks, control characters, disallowed schemes)
- **Notification Spoofing**: Manipulation of notification content through malformed OCR text

### Areas of Concern

- `lang_code` validation (`anura/config.py`) — used as Tesseract argument
- URI handling and URL opening (`anura/window.py` → `uri_validator()`)
- Tessdata model download and writing (`anura/language_manager.py`)
- XDG Portal notification payloads (`anura/services/notification_service.py`)
- Share provider URL building (`anura/services/share_service.py`)
- TTS temporary file cleanup (`anura/services/tts.py`)
- Flatpak sandbox file access in CLI `--file` mode (`anura/main.py`)

## What NOT to Report

The following are **not** considered security vulnerabilities:

- OCR recognition accuracy issues (depends on Tesseract)
- Text recognition quality on particular images
- UI/UX issues without security impact
- Performance issues without DoS potential
- External provider functionality (Mastodon, Reddit, Telegram, X)
- Issues requiring physical access to an unlocked system

## Disclosure Process

1. **Receipt**: Acknowledgment within 48 hours
2. **Initial Assessment**: Severity and impact evaluation within 7 days
3. **Coordinated Disclosure**: Joint understanding and fix development
4. **Fix Development**: Development and testing of the fix
5. **Release**: Publication of patched version
6. **Public Disclosure**: After reasonable time for user updates (typically 7–14 days from release)

## Best Practices for Users

- **Keep Updated**: Always use the latest version of Anura OCR and Tesseract
- **Verify Sources**: Process images from trusted sources when possible
- **Check Permissions**: Flatpak version has limited filesystem access to `~/Downloads`
- **Verify Sharing**: Text is shared with third-party providers — review before sharing
- **QR Code Safety**: Validator protects from malicious redirects, but verify QR codes from untrusted sources

## Implemented Security Features

- **lang_code validation**: `LANG_CODE_PATTERN` regex prevents Tesseract argument injection
- **URI validation**: `uri_validator()` protects against homograph attacks and control characters
- **Atomic tessdata writes**: Tempfile + move prevents partial corruption
- **Thread safety**: `GLib.idle_add()` for all GObject emissions prevents race conditions
- **Flatpak sandbox**: Filesystem isolation with `--filesystem=xdg-download`
- **Atomic TTS cleanup**: Lock-protected GStreamer resource management
- **No runtime subprocess**: No shell command execution at runtime
- **Privacy by design**: No telemetry, tracking, or analytics
- **Share URL encoding**: URL parameters properly encoded to prevent injection

## Contacts

- **Security Issues**: [GitHub Security Advisories](https://github.com/d3msudo/anura/security/advisories)
- **General Issues**: [GitHub Issues](https://github.com/d3msudo/anura/issues)
- **Project**: https://github.com/d3msudo/anura

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Flatpak Security Model](https://docs.flatpak.org/en/latest/sandbox-permissions.html)
- [XDG Desktop Portal](https://flatpak.github.io/xdg-desktop-portal/)
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
