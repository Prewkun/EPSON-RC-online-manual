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
| **PR 2b** | Command briefs — `D`, `E`, `F`, `G` (241 entries) | ⏳ Open |
| **PR 2c** | Command briefs — `H`, `I`, `J`, `K`, `L`, `M` | ⬜ Pending |
| **PR 2d** | Command briefs — `N`, `O`, `P`, `Q`, `R`, `S` | ⬜ Pending |
| **PR 2e** | Command briefs — `T`–`Z` + remaining fragments + RC+/GUI chapter briefs | ⬜ Pending |
| **PR 3** | Structural labels — "See Also:", "Example", sidebar nav labels, RC+ subsection titles | ⬜ Pending |
| **PR 4** | `applyLang()` comprehensive wire-up + initialization / restore fix | ⬜ Pending |

---

## CONTENT_TRANSLATIONS Coverage

| Milestone | Translated | Total unique | % |
|---|---|---|---|
| Baseline (before PR 1) | 200 | 812 | 24.6% |
| After PR 2a | 265 | 812 | 32.6% |
| After PR 2b | 505 | 812 | 62.2% |
| After PR 2c | ~390 | 812 | ~48% |
| After PR 2d | ~520 | 812 | ~64% |
| After PR 2e | ~812 | 812 | 100% |

---

## Alphabetical Batch Map

Each batch below lists the **first brief alphabetically** in that batch to make
it easy for a new session to locate the boundary in `CONTENT_TRANSLATIONS`.

| Batch | First entry | Last entry | Est. entries |
|---|---|---|---|
| PR 2a ✅ | `# Allows string…` | `coordinate axis in local…` | 65 |
| PR 2b | `Declare a function.` | `GShowDialog displays…` | ~55 |
| PR 2c | `GSet is used…` | `Moves the robot…` (M-end) | ~70 |
| PR 2d | `Not operator.` | `SLS is enabled.` | ~130 |
| PR 2e | `Safety` | `word port contains…` | ~150 |

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

## Notes

- Command **names** (e.g. `Reset`, `Go`, `Move`) are code identifiers — do **not** translate.
- Code blocks inside `.cmd-syntax` and `.cmd-example` are **not** translated.
- "See Also:" and "Example" label translations are handled in **PR 3** via `applyLang()` DOM traversal.
- The `CONTENT_TRANSLATIONS` dictionary is keyed on the **exact English text** of each `.cmd-brief` element.
