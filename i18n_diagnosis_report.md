# i18n Diagnosis Report: Mixed Language Issue (Italian)

## Summary
The mixed language issue (Italian and English) is primarily a **translation coverage and status issue**, not a technical bug in the i18n implementation. The application successfully loads the Italian translation catalog, as evidenced by some strings (e.g., "Benvenuto") appearing correctly. However, many new or refactored strings are either untranslated, marked as "fuzzy", or use new contexts that haven't been filled yet.

## Findings

### 1. Translation Coverage (po/it.po)
- **Missing Translations**: Several key UI strings introduced in recent refactors have empty `msgstr` values.
    - `Words: %d | Characters: %d` (Status bar)
    - `Drop image file here` (Welcome page)
    - Most Text-to-Speech (TTS) related strings (e.g., `Listen to text`, `Stop listening`).
- **Fuzzy Strings**: The application name `Anura` and other strings are marked as `#, fuzzy`. Gettext ignores fuzzy translations by default, causing them to fall back to English.
- **Contextual Strings**: Many strings in the UI now use contexts (`C_("Extracted screen", ...)`). These are present in the `.po` file but most have empty `msgstr`.
- **Plural Forms**: Statistics for emails and phone numbers found in text have empty plural definitions.

### 2. Technical Verification
- **Domain Matching**: The `APP_ID` (`com.github.d3msudo.anura`) correctly matches the gettext domain used in `anura/main.py` and `po/meson.build`.
- **I18n Setup**: `anura/main.py` correctly searches for locale directories. In a development environment, it successfully looks into `../po` and `../builddir/po`.
- **Loading Test**: A manual test confirmed that if a compiled `.mo` file is placed in `po/it/LC_MESSAGES/`, the application (via Python's `gettext`) correctly retrieves the translated strings.
- **UI Wrappers**: All strings in `.blp` and `.py` files are correctly wrapped in `_()`, `C_()`, or `ngettext()`.

## Conclusion
There is no technical bug preventing translations from loading. To fix the "Mixed Language" problem, the `po/it.po` file needs to be updated:
1. Fill in the empty `msgstr` for all new strings.
2. Review and remove the `#, fuzzy` markers.
3. Ensure plural forms are correctly translated.

## Recommendations
- Run a translation synchronization to ensure `po/it.po` is up to date with the latest `POTFILES`.
- Use a translation tool (like Poedit or GNOME Translation Editor) to fill in the missing Italian strings.
- Regenerate the `.mo` files after updating the `.po` files.
