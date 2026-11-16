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
