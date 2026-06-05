# CLAUDE.md — Epson RC+ 8.0 Online Manual

## Project Overview

A fully self-contained, interactive **single-file HTML reference manual** for Epson RC+ 8.0. The output (`index.html`, ~1.6 MB) is opened directly in a browser — no server, no npm, no build step required. It was generated from three official Epson PDFs via a multi-phase Python pipeline and is actively maintained with new features and translations.

---

## Repository Layout

```
/
├── index.html               # The entire application (HTML + CSS + JS, ~18,900 lines, ~1.6 MB)
├── README.md                # User-facing project overview
├── TRANSLATION_PROGRESS.md  # Tracks Thai (TH) translation PR state
├── Manual/
│   └── e_EpsonRC+UsersGuide80_r1.pdf  # Source PDF (25 MB)
└── pipeline_output/         # Build artifacts from the conversion pipeline
    ├── phase1_run.py        # Phase 1: PDF ingestion & parsing
    ├── phase2_run.py        # Phase 2: Structure analysis & content tree
    ├── phase3_run.py        # Phase 3: AI-assisted content enrichment
    ├── phase4_run.py        # Phase 4: Interactivity / component mapping
    ├── phase5_run.py        # Phase 5: HTML generation from component map
    ├── phase6_run.py        # Phase 6: RC+ Users Guide tab injection
    ├── inject_tab3.py       # Utility: inject tab3 section into index.html
    ├── pr7a_inject_descs.py # PR 7a: inject English descriptions from SPEL+ PDF
    ├── content_map.json     # Phase 1 output (raw extracted content, 6.4 MB)
    ├── content_tree.json    # Phase 2 output (structured hierarchy, 3.8 MB)
    ├── enriched_tree.json   # Phase 3 output (AI-enriched, 4.8 MB)
    ├── component_map.json   # Phase 4 output (interactive components, 2.9 MB)
    ├── chapters.json        # RC+ Users Guide chapter metadata
    ├── tab3_content.html    # Injected RC+ Users Guide content fragment
    ├── tab3_sidebar.html    # Injected RC+ Users Guide sidebar fragment
    ├── spel_ref.txt         # Raw pdftotext of SPEL+ reference PDF (1.2 MB)
    ├── spel_ref_clean.txt   # spel_ref.txt with "Syntax Error" lines removed (1.2 MB)
    ├── pr7a_injection_report.json   # PR 7a result: 198 injected, 116 missed
    ├── pr8_batches.json     # PR 8 work batches: 200 cards needing Thai desc translation
    ├── translation_gap_report.json  # Coverage audit: empty descs + dup-card clone candidates
    ├── manual.html          # Intermediate HTML fragment (pipeline artifact)
    ├── .phase2_cache.json   # Incremental build cache for phase 2
    ├── .phase3_cache.json   # Incremental build cache for phase 3
    └── phase*_report.txt    # Human-readable phase diagnostics
```

---

## index.html Architecture

The entire application lives in `index.html`. It has three sections:

### 1. CSS (`<style>` block, ~200 lines)

- CSS custom properties (design tokens) at `:root` level
- Accent colours: `--accent` (SPEL+, blue), `--gui-accent` (GUI, green), `--rc-accent` (RC+ Guide, purple)
- Light mode override via `:root[data-theme="light"]`
- Mobile breakpoint at `768px` (sidebar collapses to hamburger)

### 2. HTML Body — Four-Tab Interface

| Tab | `id` | Content |
|---|---|---|
| SPEL+ Language Reference | `tab-spel` | 734 commands in 21 categories |
| GUI Builder Reference | `tab-gui` | 17 controls, 87 props, 9 events, 5 SPEL+ stmts |
| RC+ Users Guide | `tab-rc` | 23 chapters (742 pages), 10 topic groups |
| A–Z Index | `tab-idx` | Alphabetical index across SPEL+ and GUI |

Each tab has a matching sidebar with `id` `spel-nav`, `gui-nav`, `rc-nav`, `idx-nav`.

**Command card structure (SPEL+):**
```html
<div class="cmd-card" id="spel-cmd-{name}">
  <div class="cmd-header">
    <span class="cmd-name">{NAME}</span>
    <span class="cmd-brief">{one-line English description}</span>
    <span class="cmd-brief-th" style="display:none">{Thai translation}</span>
  </div>
  <div class="cmd-body">
    <div class="cmd-syntax"><pre><code>…</code></pre></div>
    <div class="cmd-desc">…</div>
    <div class="cmd-example">…</div>
    <div class="see-also">See Also: …</div>
  </div>
</div>
```

**GUI Builder card structure:**
```html
<div class="gui-ref-card" id="gui-ref-{name}">
  <!-- similar structure with gui-brief, gui-brief-th, gui-body -->
</div>
```

### 3. JavaScript (`<script>` block, ~6,500+ lines)

Key data structures:

| Variable | Purpose |
|---|---|
| `CONTENT_TRANSLATIONS` | `{englishBrief: thaiTranslation}` — 812 entries for `.cmd-brief` text (100% coverage) |
| `DESC_TRANSLATIONS` | `{'card-id:0': thaiTranslation}` — 705 entries for `.cmd-desc` paragraphs (100% coverage) |
| `SEE_ALSO_LINKS` | `{sectionId: [{text, target}]}` — resolved hyperlink targets for See Also |
| `UI_TRANSLATIONS` | `{key: {en, th}}` — all UI labels keyed by `data-i18n` attribute value |

Key functions:

| Function | Purpose |
|---|---|
| `applyLang(lang)` | Sets language; swaps `data-i18n` text, toggles `-th` elements, applies `CONTENT_TRANSLATIONS` and `DESC_TRANSLATIONS` |
| `toggleLang()` | Switches between `en` and `th`, persists to `localStorage` |
| `toggleTheme()` | Switches dark/light, sets `data-theme` on `<html>`, persists to `localStorage` |
| `switchToGui(id)` | Navigates to a GUI Builder card by ID |
| `switchToSpel(id)` | Navigates to a SPEL+ command by ID |
| `searchCmds(query, tab)` | Live search filtering for SPEL+ or GUI cards |
| `filterSpelCat(cat, el)` | Category chip filter for SPEL+ |
| `filterGuiType(type, el)` | Type chip filter for GUI Builder |
| `filterNav(query)` | Live filter for SPEL+ sidebar nav |
| `filterGuiNav(query)` | Live filter for GUI Builder sidebar nav |
| `filterRcNav(query)` | Live filter for RC+ Users Guide sidebar nav |
| `expandAll(tab)` / `collapseAll(tab)` | Expand/collapse all cards in a tab |

---

## Internationalization (i18n) System

The app supports English (`en`) and Thai (`th`). Language preference is persisted via `localStorage`.

**How to add a UI string translation:**
1. Add `data-i18n="your-key"` to the HTML element.
2. Add `"your-key": { en: "...", th: "..." }` to `UI_TRANSLATIONS`.
3. `applyLang()` will swap the text on language change.

**How to add a command brief translation:**
- Add to `CONTENT_TRANSLATIONS`: `'Exact English brief text': 'Thai translation'`
- Keys must exactly match the text content of `.cmd-brief` elements.
- Command **names** (e.g. `Reset`, `Go`, `Move`) are code identifiers — do **not** translate.
- Code blocks inside `.cmd-syntax` and `.cmd-example` are **never** translated.

**How to add a command description translation:**
- Add to `DESC_TRANSLATIONS`: `'spel-cmd-CARDID:0': 'Thai translation'`
- Keys use the card's HTML `id` attribute plus `:0` (e.g. `'spel-cmd-reset:0'`).
- These are longer paragraph strings from `.cmd-desc` elements.

**How to add a See Also hyperlink:**
- Add to `SEE_ALSO_LINKS`: `'section-id': [{ text: 'CommandName', target: 'spel-cmd-commandname' }]`
- Targets use the prefix `spel-cmd-` for SPEL+ and `gui-ref-` for GUI Builder entries.

---

## Translation Progress (Thai)

See `TRANSLATION_PROGRESS.md` for the full PR-by-PR breakdown. **All translation work is complete.**

| Dictionary | Coverage | Entries |
|---|---|---|
| `CONTENT_TRANSLATIONS` | **100%** (812/812) | All `.cmd-brief` one-liners |
| `DESC_TRANSLATIONS` | **100%** (705/705) | All `.cmd-desc` paragraphs with content |
| `SEE_ALSO_LINKS` SPEL+ | **81.6%** (433/474 sections) | Cross-ref hyperlinks |
| `SEE_ALSO_LINKS` GUI | **100%** (62/100 entries linked) | GUI Builder cross-refs |
| UI labels | **100%** | Buttons, chips, nav, status bar |

No further translation PRs are planned. If new commands or descriptions are added, follow the conventions in this file to add entries to the appropriate dictionary.

---

## Development Workflow

### No build step required

`index.html` is edited directly. Open it in a browser to verify changes. There is no npm, no webpack, no TypeScript — just HTML, CSS, and vanilla JavaScript.

### Git workflow

All development happens directly on `main`. Commit and push to `main` for every change.

- **PR 1–PR 8d**: 20+ numbered phases of the Thai translation + content pipeline (all merged to main)
- Each PR has a descriptive title and updates `TRANSLATION_PROGRESS.md`
- Other merged work: mobile view improvements (responsive hamburger nav), 111 broken cross-ref fixes, 102 duplicate ID deduplication, 29 phantom card removals

Current working branch: `main`

### Making changes to index.html

Because the file is large (~18,800 lines), use targeted edits:

- Use `grep -n` or the Grep tool to locate elements by class name, ID, or text
- When inserting into `CONTENT_TRANSLATIONS` or `DESC_TRANSLATIONS`, maintain alphabetical order within the dictionary to keep diffs readable
- After any JavaScript change, verify in a browser that `applyLang('en')` and `applyLang('th')` both work without console errors

### Pipeline (for regenerating content)

The pipeline is in `pipeline_output/` and is run only when the source PDFs change or new content extraction is needed. The pipeline is **not** part of normal development — do not run it for translation or UI work.

```
phase1_run.py  →  content_map.json
phase2_run.py  →  content_tree.json
phase3_run.py  →  enriched_tree.json
phase4_run.py  →  component_map.json
phase5_run.py  →  (HTML fragments)
phase6_run.py  →  (final index.html)
inject_tab3.py →  injects RC+ Users Guide tab into index.html
```

Dependencies: `pdfplumber` (Phase 1), Claude API (Phases 2–4 AI fallback).

---

## Key Conventions

1. **Never translate command names** — `Reset`, `Go`, `Move`, etc. are code identifiers that appear in `.cmd-name` elements and code blocks. Only `.cmd-brief`, `.cmd-desc`, and UI labels are translated.

2. **Preserve exact key text** — `CONTENT_TRANSLATIONS` keys must match the exact string content of `.cmd-brief` elements (including punctuation, capitalisation, and trailing periods).

3. **ID naming**
   - SPEL+ commands: `spel-cmd-{lowercase-name}` (e.g., `spel-cmd-reset`)
   - GUI Builder entries: `gui-ref-{lowercase-name}` (e.g., `gui-ref-button`)
   - RC+ chapters: `rc-ch{N}` (e.g., `rc-ch5`)

4. **CSS token usage** — use `var(--accent)`, `var(--gui-accent)`, `var(--rc-accent)` for tab-consistent colouring rather than hard-coded hex values.

5. **Single-file discipline** — all styles, scripts, and content stay in `index.html`. Do not create separate `.css` or `.js` files.

6. **Update TRANSLATION_PROGRESS.md** on every translation PR — it is the handoff document between sessions.

---

## Source Content

| File | Description |
|---|---|
| `e_SPEL_Ref80_r1` | Epson RC+ 8.0 SPEL+ Language Reference Rev.1 |
| `e_GUIBuilder80_r1` | Epson RC+ 8.0 GUI Builder 8.0 Rev.1 |
| `e_EpsonRC+UsersGuide80_r1` | Epson RC+ 8.0 User's Guide Rev.1 (742 pages) |

© Seiko Epson Corporation 2024
