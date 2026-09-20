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
| 0.2.x | ✅ Active |

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
| `anura/core/atomic_task_manager.py` | Concurrency and task versioning logic |
| `anura/services/screenshot_service.py` | Image size validation (DoS prevention) and Tesseract hand-off |
| `anura/services/language_manager.py` | Tessdata model download and atomic writing |
| `anura/services/share_service.py` | Dynamic URI scheme validation and Pango markup sanitization |
| `anura/services/notification_service.py` | Pango markup injection prevention in notifications |
| `anura/widgets/extracted_page.py` + `Gtk.FileLauncher` | External editor handoff — `external-editor` GSettings key (default `xed`) launches a desktop app with exported OCR text; validate the executable/app id before launch |
| `anura/services/history_service.py` + `$XDG_DATA_HOME/anura/history/history.json` | Local extraction history — opt-in newest-first JSON store (`history-enabled`, `history-limit` keys); atomic writes, corruption quarantine, no image retention |
| `anura/utils/export_files.py` | Hardened external-editor export files (F3): `$XDG_RUNTIME_DIR` location, mode `0600`, random names, boot-time cleanup of stale exports |
| `anura/utils/tessdata_integrity.py` + `anura/data/tessdata_checksums.json` | Tessdata model integrity verification (F1): pinned git-blob SHA-1 manifest, fail-closed digest check before install — see `docs/reference/tessdata-integrity.md` |
| `anura/services/screenshot/legacy_provider.py` | Command building for the bundled `scrot` fallback, including group/world-writable binary rejection (F5) |

---

## Implemented Security Features

| Feature | Implementation |
| ------- | ------------- |
| **DoS & OOM Prevention** | Strict `MAX_IMAGE_SIZE_BYTES` checks AND dynamic `Resource Guards` that block high-res processing if free RAM < 15% or available RAM < 500MB. |
| **Transactional Worker I/O** | All OCR worker artifacts are isolated in a `tempfile.TemporaryDirectory` with environment-level redirection (`TMPDIR`, `TEMP`, `TMP`) to prevent data leakage. |
| **Text Sanitization** | `validators.sanitize_text` strips Unicode Control (Cc), Format (Cf), Private Use (Co), and Surrogate (Cs) categories to prevent terminal injection and RTL spoofing. |
| **URI Validation** | `uri_validator()` blocks homograph attacks (mixed-script) and disallowed schemes before any browser launch. |
| **Pango Markup Injection Prevention** | Hardened notifications against Pango markup injection attacks to prevent UI spoofing. |
| **Local Storage Permission Hardening** | Enhanced directory permissions for sensitive data storage to prevent unauthorized access. |
| **Config Layer Leakage Protection** | Prevents unintended exposure of internal configuration through lifecycle-scoped access controls. |
| **Hierarchical ID Collision Prevention** | Guards against identifier conflicts that could lead to OCR pipeline instability and data cross-contamination. |
| **Dynamic URI Scheme Validation** | ShareService implements dynamic URI scheme validation to prevent protocol injection attacks. |
| **Atomic Task Management** | `AtomicTaskManager` prevents race conditions via single-slot execution and UUID versioning with `BrokenProcessPool` recovery. |
| **Secure Logging** | Offline rotary logging system with strict rotation and retention policies; strictly zero-telemetry. |
| **Automated Lifecycle** | Native GObject destruction hooks ensure complete signal disconnection and resource teardown. |
| **Hardened OCR export files (F3)** | External-editor hand-off files are created in `$XDG_RUNTIME_DIR/anura/exports` (per-user, per-session) via `tempfile.mkstemp()` with mode `0600` and random names; stale export files are cleaned on boot (never in the world-readable shared `/tmp`). |
| **X11 Fallback Security** | Bundled `scrot` fallback used only when Portals fail on X11 (never on Wayland); self-contained in the sandbox, no host tools required. The provider rejects group/world-writable scrot binaries (F5) and cleans up leaked temporary screenshots on spawn failure (F4). |
| **External Editor Handoff** | `Gtk.FileLauncher` opens exported text in the configured external editor (`external-editor` key); editor preferences (line numbers, highlight, wrap mode) stored in GSettings. |
| **Local History Storage** | Opt-in extraction history in `$XDG_DATA_HOME/anura/history/` with atomic writes + `fsync`, corruption quarantine (`history.json.corrupt-*`), and bounded entry limit. |
| **Atomic tessdata install (F1/F2)** | Downloads land in `*.tmp` files and are installed via atomic `os.replace()`, so a crash mid-install can never leave a truncated `*.traineddata`; before installation the model digest is verified against the pinned git-blob SHA-1 manifest (`anura/data/tessdata_checksums.json`) and a mismatch **fails closed** (model rejected). See `docs/reference/tessdata-integrity.md`. |
| **Flatpak sandbox** | Filesystem isolation with restricted XDG directory access. |
| **Privacy by design** | No telemetry, tracking, or analytics of any kind. |

---

## Contacts

| Channel | Link |
| ------- | ---- |
| Security vulnerabilities | [GitHub Security Advisories](https://github.com/d3msudo/anura/security/advisories) |
| General issues | [GitHub Issues](https://github.com/d3msudo/anura/issues) |
| Project | https://github.com/d3msudo/anura |
