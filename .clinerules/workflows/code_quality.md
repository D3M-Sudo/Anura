# Code Quality — Cascade Workflow Command

## Trigger
`code quality` 

---

## Prompt

You are an expert Python engineer performing a **systematic code quality audit and refactoring** of this project. Your mission: make the codebase cleaner, more maintainable, and fully aligned with Python best practices — **without breaking any existing functionality**.

---

### Phase 1 — Reconnaissance 🔍

Before touching a single line, map the battlefield:

1. Identify all Python files and their responsibilities.
2. Note the tech stack (frameworks, dependencies, entry points).
3. Run any existing tests to establish a **green baseline** (`pytest`, `unittest`, etc.). If no tests exist, note it.
4. Identify the most critical paths (API routes, core business logic, data models).

---

### Phase 2 — Static Analysis 🧪

Scan for issues across these dimensions:

| Dimension | What to look for |
|---|---|
| **Complexity** | Functions > 20 lines, cyclomatic complexity, deeply nested logic |
| **Naming** | Non-descriptive vars (`x`, `data2`, `tmp`), inconsistent casing |
| **Type safety** | Missing type hints on public functions and methods |
| **Duplication** | Copy-pasted blocks, logic that should be extracted |
| **Dead code** | Unused imports, unreachable branches, commented-out blocks |
| **Error handling** | Bare `except:`, swallowed exceptions, no logging |
| **Magic values** | Hardcoded strings/numbers that should be constants or config |
| **Imports** | Wildcard imports, wrong ordering (PEP 8), circular dependencies |

---

### Phase 3 — Refactoring Execution 🔧

Apply fixes **iteratively and safely**, in this priority order:

#### 3.1 — Structure & Readability
- Enforce PEP 8 formatting (spacing, line length ≤ 88 chars, blank lines).
- Fix import order: stdlib → third-party → local (use `isort` convention).
- Remove all dead code and unused imports.
- Replace magic values with named constants or config entries.

#### 3.2 — Naming & Clarity
- Rename variables, functions, and classes to be self-documenting.
- Use verbs for functions (`get_user`, `calculate_total`), nouns for classes.
- Boolean variables/functions should read naturally (`is_valid`, `has_permission`).

#### 3.3 — Functions & Classes
- Break down any function > 20 lines into focused, single-responsibility units.
- Apply the **Single Responsibility Principle** to classes.
- Prefer composition over inheritance where it reduces coupling.
- Use `@dataclass` or `NamedTuple` for simple data containers.

#### 3.4 — Type Hints & Docstrings
- Add type hints to all public function signatures.
- Add a concise docstring to every public function, class, and module (Google style).
- Use `Optional[T]` / `T | None` consistently (prefer `X | Y` for Python 3.10+).

#### 3.5 — Error Handling & Logging
- Replace bare `except:` with specific exception types.
- Ensure errors are logged with context (`logger.error("...", exc_info=True)`).
- Add meaningful error messages — never silently swallow exceptions.

#### 3.6 — Pythonic Patterns
- Replace manual loops with list/dict/set comprehensions where appropriate.
- Use `enumerate()`, `zip()`, `any()`, `all()` instead of manual counters.
- Prefer f-strings over `.format()` or `%` formatting.
- Use context managers (`with`) for all resource handling (files, DB, HTTP).
- Replace `if x == None` with `if x is None`.

#### 3.7 — Performance & Safety (non-breaking only)
- Replace inefficient patterns (e.g., `+` string concatenation in loops → `join()`).
- Use generators over lists when only iteration is needed.
- Flag (but don't auto-fix) any thread-safety or concurrency concerns.

---

### Phase 4 — Verification ✅

After every meaningful change:

1. Re-run the full test suite — **zero regressions allowed**.
2. If no tests exist, manually verify the critical paths identified in Phase 1.
3. Do a final diff review: confirm every change is intentional and correct.

---

### Phase 5 — Report 📋

Produce a concise summary structured as:

```
## Code Quality Report

### Files Modified
- `path/to/file.py` — brief reason

### Key Improvements
- [Category] Description of change and why it matters

### Metrics (before → after)
- Functions refactored: N
- Type hints added: N
- Dead code removed: N lines
- Complexity hotspots resolved: N

### Remaining Technical Debt
- [Priority: High/Med/Low] Description — recommended next step

### No Changes Made To
- List of files intentionally left untouched and why
```

---

### Hard Constraints

- ❌ Never change **public API signatures** (routes, exported functions, CLI args) in a breaking way.
- ❌ Never remove functionality — only restructure how it's implemented.
- ❌ Never introduce new dependencies without explicit user approval.
- ✅ If a refactor is risky, **propose it with explanation** instead of applying it silently.
- ✅ When in doubt about intent, **ask before refactoring**.

---

### Style Reference

- **Formatter**: Black (line length 88)
- **Linter**: Ruff or Flake8
- **Type checker**: mypy (strict mode preferred)
- **Import sorter**: isort
- **Docstring style**: Google
- **Python target**: match the project's existing version (check `pyproject.toml`, `setup.cfg`, or `.python-version`)
