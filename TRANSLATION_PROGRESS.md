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
| **PR 5a** | See Also hyperlinks — SPEL+ section (374 entries, 433/474 sections linked, 81.6% token coverage) | ⏳ Open |
| **PR 5b** | See Also hyperlinks — GUI Builder section (100 entries, 62/100 sections linked, 24.9% token coverage*) | ✅ Merged |
| **PR 6a** | cmd-desc translations — SPEL+ A–D (89 entries) + `DESC_TRANSLATIONS` dict + `applyLang()` wiring | ⏳ Open |

---

## CONTENT_TRANSLATIONS Coverage

| Milestone | Translated | Total unique | % |
|---|---|---|---|
| Baseline (before PR 1) | 200 | 812 | 24.6% |
| After PR 2a | 265 | 812 | 32.6% |
| After PR 2b | 505 | 812 | 62.2% |
| After PR 2c | 568 | 812 | 69.9% |
| After PR 2d | 699 | 812 | 86.1% |
| After PR 2e | 812 | 812 | 100% |

---

## Alphabetical Batch Map

Each batch below lists the **first brief alphabetically** in that batch to make
it easy for a new session to locate the boundary in `CONTENT_TRANSLATIONS`.

| Batch | First entry | Last entry | Est. entries |
|---|---|---|---|
| PR 2a ✅ | `# Allows string…` | `coordinate axis in local…` | 65 |
| PR 2b ✅ | `Declare a function.` | `GShowDialog displays…` | 241 |
| PR 2c ⏳ | `Function Gripper…` (F/G missed) + `Hand_Off…` | `or choose a button…` | 68 |
| PR 2d ✅ | `Parse a string…` | `Runs an Epson RC+ dialog…` | 131 |
| PR 2e ⏳ | `Safety` | `word port contains…` | 136 |

---

## How to Resume in a New Session

1. Read this file to find the last merged PR.
2. Check `index.html` → `CONTENT_TRANSLATIONS` — the last key inserted marks the boundary.
3. Identify the next batch from the **Alphabetical Batch Map** above.
4. Fetch `/tmp/all_briefs.txt` (regenerate with the grep command below if missing):
   ```bash
   grep -o 'class="cmd-brief">[^<]*<' index.html | sed 's/class="cmd-brief">//;s/<$//' | sort -u > /tmp/all_briefs.txt
   ```
5. Run the Python diff script to find which briefs in the next batch are not yet translated:
   ```python
   import re
   with open('index.html') as f: content = f.read()
   match = re.search(r'const CONTENT_TRANSLATIONS = \{(.*?)\};', content, re.DOTALL)
   existing = set(re.findall(r"^  '([^']+)':", match.group(1), re.MULTILINE))
   with open('/tmp/all_briefs.txt') as f:
       briefs = [l.rstrip() for l in f if l.strip() and not l.startswith('812')]
   missing = [b for b in briefs if b not in existing]
   print(f"Missing: {len(missing)}")
   for b in missing[:20]: print(repr(b))
   ```
6. Write translations for the next batch, insert them into `CONTENT_TRANSLATIONS`, update this file, commit, push, and open a PR.

---

*GUI coverage is lower because many GUI See Also entries reference control-type category names (`Button`, `Form`, `ComboBox`, etc.) which don't have individual `gui-ref-*` page IDs — they're category-level names in the GUI Builder architecture.

---

## Notes

- Command **names** (e.g. `Reset`, `Go`, `Move`) are code identifiers — do **not** translate.
- Code blocks inside `.cmd-syntax` and `.cmd-example` are **not** translated.
- "See Also:" and "Example" label translations are handled in **PR 3** via `applyLang()` DOM traversal.
- The `CONTENT_TRANSLATIONS` dictionary is keyed on the **exact English text** of each `.cmd-brief` element.
