# Thai Translation Progress

This file tracks the state of the Thai (TH) language translation for the
Epson RC+ 8.0 Online Manual (`index.html`).
Update it with every translation PR so the next session can pick up exactly
where work left off.

---

## Overall Status

| Layer | Description | Status |
|---|---|---|
| **PR 1** | UI chips, buttons, topbars, 35 category/section headers | ✅ Merged |
| **PR 2a** | Command briefs — `#`, `A`, `B`, `C` (65 entries) | ✅ Merged |
| **PR 2b** | Command briefs — `D`, `E`, `F`, `G` (241 entries) | ✅ Merged |
| **PR 2c** | Command briefs — `F`(missed), `G`(missed), `H`–`O` (68 entries) | ✅ Merged |
| **PR 2d** | Command briefs — `P`, `Q`, `R` (131 entries) | ✅ Merged |
| **PR 2e** | Command briefs — `S`–`W` + lowercase fragments (136 entries) | ✅ Merged |
| **PR 3** | Structural labels — Example, See Also:, Applies to:, nav/stat labels | ✅ Merged |
| **PR 4** | `applyLang()` consolidation — cmd-brief integrated, monkey-patch removed, single init | ✅ Merged |
| **PR 5a** | See Also hyperlinks — SPEL+ section (374 entries, 433/474 sections linked, 81.6% token coverage) | ✅ Merged |
| **PR 5b** | See Also hyperlinks — GUI Builder section (100 entries, 62/100 sections linked, 24.9% token coverage*) | ✅ Merged |
| **PR 6a** | cmd-desc translations — SPEL+ A–D (89 entries) + `DESC_TRANSLATIONS` dict + `applyLang()` wiring | ✅ Merged |
| **PR 6b** | cmd-desc translations — SPEL+ E–J (72 entries) | ✅ Merged |
| **PR 6c** | cmd-desc translations — SPEL+ K–R (82 entries) | ✅ Merged |
| **PR 6d** | cmd-desc translations — SPEL+ S–Z + fragments (81 entries) | ✅ Merged |
| **PR 6e** | cmd-desc translations — GUI Builder (124 entries) | ✅ Merged |
| **PR 7a** | PDF pipeline — inject 198 English descriptions into empty SPEL+ cmd-cards (83.3% coverage) | ✅ Merged |
| **PR 7b** | Clone 57 Thai desc translations from base cards to `-2`/`-3` duplicate cards | ✅ Merged |
| **PR 8a** | Thai desc translations — newly injected SPEL+ Accel–ErrMsg (65 entries) | ✅ Merged |
| **PR 8b** | Thai desc translations — newly injected SPEL+ ErrorOn–LocalDef (45 entries) | ✅ Merged |
| **PR 8c** | Thai desc translations — newly injected SPEL+ Login–RSet (45 entries) | ✅ Merged |
| **PR 8d** | Thai desc translations — newly injected SPEL+ RShift64–XYLimDef (45 entries) | ✅ Merged |

---

## DESC_TRANSLATIONS Coverage

| Milestone | Entries | Notes |
|---|---|---|
| After PR 6a–6e | 448 | SPEL+ A–Z + GUI Builder, original descriptions only |
| After PR 7b | 505 | +57 cloned from base cards to `-2`/`-3` duplicates |
| After PR 8a (65 entries) | 570 | Accel–ErrMsg |
| After PR 8b (45 entries) | 615 | ErrorOn–LocalDef |
| After PR 8c+8d (90 entries) | 705 | Login–XYLimDef — full coverage ✅ |

---

## PR 8 Scope — ✅ Complete

All 200 newly injected SPEL+ cmd-cards now have Thai desc translations.
`DESC_TRANSLATIONS` coverage: **705 entries** — all cards with descriptions are translated.

---

## CONTENT_TRANSLATIONS Coverage

| Milestone | Translated | Total unique | % |
|---|---|---|---|
| Baseline (before PR 1) | 200 | 812 | 24.6% |
| After PR 2a | 265 | 812 | 32.6% |
| After PR 2b | 505 | 812 | 62.2% |
| After PR 2c | 568 | 812 | 69.9% |
| After PR 2d | 699 | 812 | 86.1% |
| After PR 2e | 812 | 812 | 100% ✅ |

---

## How to Resume in a New Session

1. Read this file to find the last merged PR and what's next.
2. All Thai translation work (CONTENT_TRANSLATIONS, DESC_TRANSLATIONS, SEE_ALSO_LINKS, UI labels) is **complete**.
3. All commits go directly to `main` (no feature branches).

---

*GUI coverage is lower because many GUI See Also entries reference control-type category names (`Button`, `Form`, `ComboBox`, etc.) which don't have individual `gui-ref-*` page IDs — they're category-level names in the GUI Builder architecture.

---

## Notes

- Command **names** (e.g. `Reset`, `Go`, `Move`) are code identifiers — do **not** translate.
- Code blocks inside `.cmd-syntax` and `.cmd-example` are **not** translated.
- "See Also:" and "Example" label translations are handled in **PR 3** via `applyLang()` DOM traversal.
- The `CONTENT_TRANSLATIONS` dictionary is keyed on the **exact English text** of each `.cmd-brief` element.
- `DESC_TRANSLATIONS` keys use the format `'card-id:0'` (e.g. `'spel-cmd-accel:0'`).
