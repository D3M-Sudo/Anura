# Anura UI design conventions

**Status:** M1-02 implementation baseline  
**Toolkit:** GTK 4 / Libadwaita  
**Brand identity:** existing green/teal palette retained

## Typography

Use Libadwaita semantic typography classes as the default hierarchy:

| Role | GTK/Libadwaita convention |
|---|---|
| Primary page title | `title-1` |
| Secondary title | `title-2` / `title-3` |
| Group heading | `heading` |
| Body copy | `body` |
| Secondary copy | `dim-label` |
| Caption / metadata | `caption` |

Application-authored font-size overrides are exceptions, not a parallel type scale. The Welcome hero keeps its existing `title-1` semantic class with a 1.15em emphasis. Downloaded-language text retains bold emphasis as a state cue. Do not override system font settings or native widget typography globally.

## Spacing

The shared application-authored spacing scale is:

| Token name | Value | Typical role |
|---|---:|---|
| `space-1` | 4 px | Tight internal grouping |
| `space-2` | 8 px | Compact controls and icon/text gaps |
| `space-3` | 12 px | Standard component spacing |
| `space-4` | 16 px | Group separation |
| `space-5` | 24 px | Larger section/surface padding |

Blueprint layout properties and GTK CSS margin/padding declarations use these values. Existing 6 px spacing was normalized to 8 px; 20 px CSS padding was normalized to 24 px. Zero remains valid for explicit resets. Width/height requests, border widths, icon sizes and animation distances are not spacing tokens.

## Corner radii

| Token name | Value | Status |
|---|---:|---|
| `radius-small` | 6 px | Reserved; not applied without a component need |
| `radius-medium` | 12 px | Existing custom text/drop surfaces |
| `radius-pill` | 9999 px | Intentionally circular History empty-state icon |

Prefer native GTK/Libadwaita radii for native controls. Do not apply application radii globally.

## GTK CSS implementation constraint

GTK CSS is not browser CSS and does not provide standard CSS custom properties for arbitrary numeric dimensions. Do not use `var(--space-*)` or invent unsupported at-rules. The numeric conventions are documented here and guarded by static regression tests over Blueprint spacing, stylesheet margin/padding and custom corner radii. If GTK adds a supported numeric-token mechanism in a future version, reassess centralization without adding a preprocessor dependency by default.

## Control hierarchy and exceptions

Prefer native semantic styles such as `suggested-action`, `flat`, `pill`, `boxed-list` and `card`. Keep application-specific styles limited to brand/state treatment and custom surfaces. Existing component geometry and native preferences-page patterns remain authoritative unless a concrete inconsistency or defect is demonstrated.

## Theme compatibility

Preserve the existing `default`, `force-light` and `force-dark` behavior and green palette. Spacing and radius conventions are scheme-independent; color/state rules must continue to use the existing light/dark-aware treatments.

## Validation

`tests/test_ui_palette.py` checks the palette, semantic typography exception, spacing values in every Blueprint file and GTK stylesheet, and custom radius values. Full execution is performed by GitHub Actions; static checks do not claim manual visual, Orca/AT-SPI or manual keyboard verification.


## Semantic color roles and downloaded-language state

- The downloaded-language state is expressed by the `downloaded` CSS class on the language-row widget. `LanguageRow.update_ui()` adds the class when the language is installed and removes it when it is not installed (including the special English row); the existing light/dark label colors remain in place.
- The Libadwaita `.success` class was evaluated but not adopted: it changes the widget accent and does not itself establish adequate contrast on the application's resolved light/dark surfaces. GTK's deprecated style-context color getter is not used as a new runtime contrast-test dependency.
- Keep the app-owned fallback pair `#0F7650` (light) and `#21B77A` (dark). Repeated identical literals are retained where they serve distinct semantic roles (downloaded text, History empty-state icon, focus indicator); do not consolidate across roles.
- `default`, `force-light` and `force-dark` theme transitions are covered by GTK tests for the setting callback and affected language/History/focus CSS classes. These tests verify class/state continuity, not rendered-pixel contrast under every desktop theme.
- The UI color scanner in `tests/ui_color_scanner.py` discovers new supported UI source files and flags unclassified color literals; intentional exceptions require path-specific rationale.


## Existing typography class usage requiring caution

The following existing Blueprint classes are documented for traceability; they are not new conventions to copy into new UI:

- `heading` is a documented Libadwaita typography style for standard UI headings at the default text size. It is the supported semantic class on the Languages section label.
- `title` on the `LanguageRow` label expresses a title-like intent in the current template, but it is not one of the documented Adwaita typography utility classes. The class name alone does not guarantee a standard title size or hierarchy; no matching application rule is defined in `data/style.css`.
- `h4` is also present on the Languages section label alongside `heading`. It is not part of the documented Adwaita typography utility set and does not establish an Adwaita heading level. Treat it as a legacy/unverified styling hook, not as a semantic heading token.

Libadwaita documents the title hierarchy as `title-1` through `title-4`, plus `heading`, `body`, `caption-heading` and `caption` (alongside other utility classes). GTK permits arbitrary widget CSS classes, but arbitrary names acquire visual meaning only when a stylesheet defines them. See the [Libadwaita style-class reference](https://gnome.pages.gitlab.gnome.org/libadwaita/doc/1-latest/style-classes.html) and [GTK CSS overview](https://docs.gtk.org/gtk4/css-overview.html).

No Blueprint class was changed as part of this documentation-only F4 resolution. A future visual review may decide whether `title` should become `title-4` or `heading`, and whether `h4` should be removed; that requires a separately scoped change with rendered UI review.
