# Security Policy

> Anura OCR takes security seriously. All processing happens locally — no data leaves your machine.  
> If you find a vulnerability, please follow the responsible disclosure process below.

---

## Reporting a Vulnerability

### Preferred — GitHub Security Advisories

**[Open a private Security Advisory →](https://github.com/d3msudo/anura/security/advisories/new)**

This enables:
- Private disclosure and discussion before any public exposure
- Coordinated vulnerability disclosure timeline
- CVE assignment through GitHub
- Draft advisories reviewed before publication

### Alternative — GitHub Issues

For non-sensitive security questions or general inquiries, open a [GitHub Issue](https://github.com/d3msudo/anura/issues).  
**Do NOT report sensitive vulnerabilities publicly** — use Security Advisories for those.

---

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x | ✅ Active |

This policy will be updated as the project matures.

---

## What to Report

### 🔴 High Priority

| Issue | Description |
|-------|-------------|
| **Tesseract Injection** | Unvalidated `lang_code` arguments passed to pytesseract or Tesseract |
| **Path Traversal** | Access to files outside intended directories (tessdata, TTS cache, downloads) |
| **Command Injection** | Insufficient sanitization of paths or user input in shell commands |
| **Data Exposure** | OCR text exposed to unintended third-party services without sanitization |
| **Flatpak Sandbox Bypass** | Circumvention of `--filesystem=xdg-download` or XDG portal restrictions |

### 🟡 Medium Priority

| Issue | Description |
|-------|-------------|
| **Denial of Service** | Crashes or resource exhaustion from malformed images (Pillow, pyzbar, pytesseract) |
| **Race Conditions** | TOCTOU vulnerabilities in temporary file operations |
| **Symlink Attacks** | Improper symlink handling in download or cache paths |
| **URI Injection** | Bypass of `uri_validator()` in `utils/validators.py` (homograph attacks, control chars, disallowed schemes) |
| **Notification Spoofing** | Manipulation of notification content through malformed OCR text |

### 🔍 Areas of Concern

| File | Area |
|------|------|
| `anura/config.py` | `lang_code` validation — used as Tesseract argument |
| `anura/utils/validators.py` | URI validation → `uri_validator()` |
| `anura/language_manager.py` | Tessdata model download and writing |
| `anura/services/notification_service.py` | XDG Portal notification payloads |
| `anura/services/share_service.py` | Share provider URL building |
| `anura/services/tts.py` | TTS temporary file cleanup |
| `anura/main.py` | Flatpak sandbox file access in CLI `--file` mode |

---

## What NOT to Report

The following are **not** considered security vulnerabilities:

- OCR recognition accuracy (depends on Tesseract engine)
- Text recognition quality on particular images
- UI/UX issues without security impact
- Performance issues without DoS potential
- External provider functionality (Mastodon, Reddit, Telegram, X)
- Issues requiring physical access to an unlocked system

---

## Disclosure Process

```
1. Receipt          → Acknowledgment within 48 hours
2. Assessment       → Severity and impact evaluation within 7 days
3. Coordination     → Joint understanding and fix development
4. Fix Development  → Development and testing of the patch
5. Release          → Publication of patched version
6. Public Disclosure→ 7–14 days after release
```

---

## Implemented Security Features

| Feature | Implementation |
|---------|----------------|
| **lang_code validation** | `LANG_CODE_PATTERN` regex prevents Tesseract argument injection |
| **URI validation** | `uri_validator()` blocks homograph attacks, control characters, disallowed schemes |
| **Atomic tessdata writes** | `tempfile` + `shutil.move` prevents partial file corruption |
| **Thread safety** | `GLib.idle_add()` for all GObject emissions prevents race conditions |
| **Flatpak sandbox** | Filesystem isolation with `--filesystem=xdg-download` |
| **Atomic TTS cleanup** | Lock-protected GStreamer resource management |
| **No subprocess at runtime** | No shell command execution during normal operation |
| **Privacy by design** | No telemetry, tracking, or analytics of any kind |
| **Share URL encoding** | URL parameters properly encoded to prevent injection |

---

## Best Practices for Users

- **Keep updated** — always use the latest release of Anura OCR and Tesseract
- **Verify sources** — process images from trusted sources when possible
- **Check permissions** — the Flatpak version has filesystem access limited to `~/Downloads`
- **Review before sharing** — text is sent to third-party providers when using the Share feature
- **QR code safety** — the URI validator protects against malicious redirects, but verify QR codes from untrusted sources

---

## Contacts

| Channel | Link |
|---------|------|
| Security vulnerabilities | [GitHub Security Advisories](https://github.com/d3msudo/anura/security/advisories) |
| General issues | [GitHub Issues](https://github.com/d3msudo/anura/issues) |
| Project | https://github.com/d3msudo/anura |

---

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Flatpak Security Model](https://docs.flatpak.org/en/latest/sandbox-permissions.html)
- [XDG Desktop Portal](https://flatpak.github.io/xdg-desktop-portal/)
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
