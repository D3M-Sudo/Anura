# Security Policy

> Anura OCR takes security seriously. All processing happens locally — no data leaves your machine.  
> If you find a vulnerability, please follow the responsible disclosure process below.

---

## Reporting a Vulnerability

### Preferred — GitHub Security Advisories

**[Open a private Security Advisory →](https://github.com/d3msudo/anura/security/advisories/new)**

---

## Supported Versions

| Version | Supported |
| ------- | -------- |
| 0.1.x | ✅ Active |

---

## What to Report

### 🔴 High Priority

| Issue | Description |
| ------- | ----------- |
| **Tesseract Injection** | Unvalidated `lang_code` arguments passed to pytesseract or Tesseract |
| **Path Traversal** | Access to files outside intended directories (tessdata, TTS cache, downloads) |
| **Command Injection** | Insufficient sanitization of paths or user input in shell commands |
| **Flatpak Sandbox Bypass** | Circumvention of `--filesystem=xdg-download` or XDG portal restrictions |

### 🟡 Medium Priority

| Issue | Description |
| ------- | ----------- |
| **Denial of Service (DoS)** | Resource exhaustion from malformed images. Bypass of `MAX_IMAGE_SIZE_BYTES` checks. |
| **Race Conditions** | Inconsistencies in `AtomicTaskManager` execution or temporary file operations |
| **URI Injection** | Bypass of `uri_validator()` in `utils/validators.py` (homograph attacks, RTL spoofing) |
| **Text Injection** | Manipulation of terminal or UI via malformed OCR text (Control/Format character injection) |

### 🔍 Areas of Concern

| File | Area |
| ---- | ---- |
| `anura/config.py` | `lang_code` validation — used as Tesseract argument |
| `anura/utils/validators.py` | URI validation (`uri_validator`) and Text Sanitization (`sanitize_text`) |
| `anura/atomic_task_manager.py` | Concurrency and task versioning logic |
| `anura/services/screenshot_service.py` | Image size validation (DoS prevention) and Tesseract hand-off |
| `anura/language_manager.py` | Tessdata model download and atomic writing |

---

## Implemented Security Features

| Feature | Implementation |
| ------- | ------------- |
| **DoS Prevention** | Strict `MAX_IMAGE_SIZE_BYTES` checks in `ScreenshotService` before image loading. |
| **Text Sanitization** | `validators.sanitize_text` strips Unicode Control (Cc) and Format (Cf) categories. |
| **URI Validation** | `uri_validator()` blocks homograph attacks and disallowed schemes. |
| **Atomic Task Management** | `AtomicTaskManager` prevents race conditions via single-slot execution and UUID versioning. |
| **Atomic tessdata writes** | `tempfile` + `shutil.move` prevents partial file corruption. |
| **Flatpak sandbox** | Filesystem isolation with `--filesystem=xdg-download`. |
| **Privacy by design** | No telemetry, tracking, or analytics of any kind. |

---

## Contacts

| Channel | Link |
| ------- | ---- |
| Security vulnerabilities | [GitHub Security Advisories](https://github.com/d3msudo/anura/security/advisories) |
| General issues | [GitHub Issues](https://github.com/d3msudo/anura/issues) |
| Project | https://github.com/d3msudo/anura |
