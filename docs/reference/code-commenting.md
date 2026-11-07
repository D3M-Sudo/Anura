# Code comments and docstrings

This document defines the maintenance standard for comments and docstrings in Anura.
It applies to application code, tests, build configuration, and CI workflows.

## Comments

- Explain intent, constraints, ownership, lifecycle, security properties, or non-obvious trade-offs. Do not restate the operation immediately below the comment.
- Describe the behaviour and invariant that must remain true, not the history of how a defect was discovered or fixed.
- Keep issue identifiers when they provide useful traceability for a regression or a non-obvious safeguard. Remove identifiers that add no maintenance value.
- Keep comments adjacent to the code they qualify. Consolidate repeated explanations without removing distinct constraints.
- Remove speculative future plans, abandoned implementation notes, stale examples, and commented-out code after confirming that the referenced implementation is unused.
- In tests, explain setup constraints, isolation boundaries, mocks, and the behaviour under test. Avoid comments that merely repeat an assertion.
- In configuration and CI files, document the current requirement, trust boundary, or ordering constraint. Do not retain incident narratives as operational documentation.

## Python docstrings

Use Google style when a docstring needs structured sections. Keep short, self-explanatory methods concise; do not add empty or redundant sections.

Use the following conventions:

- Start with an imperative summary for functions and methods, or a concise description for classes and modules.
- Add a blank line before extended details.
- Use `Args:`, `Returns:`, and `Raises:` only when they add information not already clear from the signature or implementation.
- Keep parameter names and descriptions aligned with the function signature.
- Describe observable behaviour, side effects, ownership, and failure conditions where callers need to know them.
- Prefer type annotations for types; do not duplicate them in prose unless needed to explain a constraint.
- Avoid implementation walkthroughs, duplicated comments, historical bug narratives, and speculative promises.

Example:

```python
def load_model(language: str, destination: Path) -> Path:
    """Install a verified OCR model for the requested language.

    Args:
        language: Supported Tesseract language code.
        destination: Directory in which to install the model.

    Returns:
        Path to the installed model.

    Raises:
        ModelIntegrityError: If the downloaded model fails checksum validation.
    """
```

## Review checklist

Before adding or changing a comment or docstring, verify that it:

1. Describes a current behaviour or invariant.
2. Adds information that is not obvious from the code.
3. Uses precise terminology and avoids conversational or promotional phrasing.
4. Remains accurate when nearby implementation details change.
5. Preserves security, concurrency, lifecycle, and regression context that future maintainers need.
