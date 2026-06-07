# Bug Hunt Progress Report
Generated: 2026-06-07T14:00:00Z

## Statistics
- Files analyzed: 309/309 (100.0%)
- Bugs Found: 8 (Fixed: 2, Addressed: 3, Open: 1, Deferred: 1, Invalid: 1)
- Tools Executed: ruff, mypy, bandit, vulture, pytest

## Validation Summary (2026-06-07)

| ID | File | Severity | Status | Notes |
|----|------|----------|--------|-------|
| NEW-017 | `anura/services/language_manager.py:288` | MEDIUM | ✅ FIXED | .tmp cleanup with 1h age threshold |
| NEW-018 | `anura/transformers/models.py:39` | MEDIUM | ❌ INVALID | Mypy false positive — local variable type inference noise |
| NEW-019 | `anura/core/silent_runner.py:33` | LOW | ✅ FIXED | Unused `_frame` parameter in signal handler |
| NEW-020 | `anura/controllers/ocr_controller.py:95` | MEDIUM | ⏸ DEFERRED | Double MagicProcessor — fix in progress (PR #258) |
| NEW-021 | `anura/transformers/models.py:39` | LOW | 🔓 OPEN | Mypy type mismatch on `keys` in `_count_unique_sections` — no runtime impact |
| NEW-022 | `anura/transformers/magic_processor.py:56` | LOW | ✔ ADDRESSED | Stale finding — redundant OcrResult wrapping was already eliminated; remaining wrapping is a required adapter |
| NEW-023 | `anura/core/atomic_task_manager.py:158` | MEDIUM | ✔ ADDRESSED | `InterruptedError ⊆ OSError ⊆ Exception` — already caught by generic handler; clarity issue only |
| NEW-024 | `anura/services/clipboard_service.py:286` | LOW | ✔ ADDRESSED | Stale-cancellable check under `_state_lock` already prevents double-action on race |

## Open Finding Detail

### NEW-021 — Mypy type mismatch in `_count_unique_sections`
**File:** `anura/transformers/models.py:39`  
**Severity:** LOW | **Runtime impact:** None  
**Description:** Mypy infers `keys: Set[tuple[Any]]` from the first branch and then
flags the second (`Set[tuple[Any, Any]]`) and third (`Set[tuple[Any, Any, Any]]`) branches
as incompatible. No explicit type annotation exists on `keys`.  
**Fix:** Annotate `keys: set[tuple[Any, ...]]` to use variadic tuple syntax, satisfying mypy without changing runtime behaviour.

## Static Analysis Results
- **Ruff:** 0 issues (clean)
- **Bandit:** 0 issues (no security concerns)
- **Mypy:** errors limited to gi/GObject stubs (not installed in CI) + NEW-021 type annotation
- **Vulture:** 60% confidence false positives only (public API methods, GTK signal handlers)
