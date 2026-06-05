"""
PR 9a: Extract example blocks from spel_ref_clean.txt and overwrite
cmd-example divs in index.html for all SPEL+ cmd-cards.

Pattern: Each command section ends with a line like:
  "CommandName [Statement|Function|Operator] Example"
followed by the example code up to the next section header.

Strategy:
  1. Scan spel_ref_clean.txt for all "X Example" header lines.
  2. Extract example content: lines from header+1 until next 3.X.Y section.
  3. Build {cmd_name_lower: example_text} dict.
  4. For each cmd-card in index.html, overwrite cmd-example div.
     - If PDF has example → inject full content.
     - If no PDF match → keep existing content unchanged.
"""
import re, json, html as html_mod
from pathlib import Path

# ── Parse spel_ref_clean.txt ──────────────────────────────────────────────────
raw_lines = Path('pipeline_output/spel_ref_clean.txt').read_text(encoding='utf-8').splitlines()
sec_hdr_pat = re.compile(r'^\s*3\.\d+\.\d+\s+')
# Inline "X Example" header pattern
ex_hdr_pat = re.compile(r'^.+\s+Example\s*$')

NOISE = re.compile(r'^\d+$')   # lone page numbers

def is_noise(line: str) -> bool:
    s = line.strip()
    if NOISE.match(s): return True
    if '\x0c' in line: return True
    if 'SPEL+ Language Reference (RC800' in line: return True
    if s in ('Rev.1', 'Original instructions'): return True
    return False

def extract_example(start_idx: int) -> str:
    """Extract example content starting one line after the 'X Example' header."""
    out = []
    for j in range(start_idx + 1, len(raw_lines)):
        l = raw_lines[j]
        # Stop at next command section header
        if sec_hdr_pat.match(l.strip()):
            break
        # Stop at next "X Example" (next command's example header)
        if ex_hdr_pat.match(l.strip()) and j != start_idx:
            break
        if is_noise(l):
            continue
        out.append(l.rstrip())
    # Strip trailing blank lines
    while out and not out[-1].strip():
        out.pop()
    return '\n'.join(out)


# Scan all "X Example" header lines
example_headers: list[tuple[int, str]] = []
for i, l in enumerate(raw_lines):
    s = l.strip()
    if ex_hdr_pat.match(s) and len(s) > 7:
        example_headers.append((i, s))

print(f"Example headers found: {len(example_headers)}")

# Build cmd_name → example_text dict
# "AccelS Statement Example" → cmd_part = "AccelS"
# "#define Example"          → cmd_part = "#define"
cmd_examples: dict[str, str] = {}

def normalise(name: str) -> str:
    return name.lower().rstrip('#$').rstrip()

for idx_h, (line_i, header) in enumerate(example_headers):
    # Strip trailing " Example" (plus optional Type words before it)
    # e.g. "AccelS Statement Example" → "AccelS Statement"
    #      "#define Example"          → "#define"
    base = re.sub(r'\s+Example\s*$', '', header).strip()
    # Strip type suffix
    for sfx in ('Statement', 'Statements', 'Function', 'Functions', 'Operator'):
        if base.endswith(' ' + sfx):
            base = base[: -len(sfx) - 1].strip()
            break

    # Expand compound names ("Arc, Arc3", "GoSub...Return", "ParseStr / ParseStr")
    expanded: list[str] = []
    for seg in re.split(r'[,/]', base):
        for sub in re.split(r'\.\.\.', seg):
            sub = re.sub(r'\s*\([^)]*\)', '', sub).strip()
            for tw in ('Statement', 'Statements', 'Function', 'Functions', 'Operator'):
                if sub.endswith(' ' + tw):
                    sub = sub[: -len(tw) - 1].strip()
            if sub:
                expanded.append(sub)

    text = extract_example(line_i)
    if not text:
        continue

    for name in expanded:
        key = normalise(name)
        if not key:
            continue
        # Prefer first occurrence (body) over later duplicates
        if key not in cmd_examples:
            cmd_examples[key] = text

print(f"Unique commands with examples: {len(cmd_examples)}")


def lookup_example(cmd_name: str) -> str | None:
    key = normalise(cmd_name)
    for variant in [key, key.replace('_', ''), key.replace('-', ''), key.replace('#', '')]:
        if variant in cmd_examples:
            return cmd_examples[variant]
    return None


def find_div_end(html: str, open_pos: int) -> int:
    """Return the index just after the </div> that closes the div opened at open_pos."""
    depth = 0
    i = open_pos
    while i < len(html):
        if html[i:i+4] == '<div':
            depth += 1
            j = html.find('>', i)
            i = j + 1 if j >= 0 else len(html)
        elif html[i:i+6] == '</div>':
            depth -= 1
            i += 6
            if depth == 0:
                return i
        else:
            i += 1
    return len(html)


# ── Process index.html ────────────────────────────────────────────────────────
html_text = Path('index.html').read_text(encoding='utf-8')
card_open_pat = re.compile(r'<div class="cmd-card" id="(spel-cmd-[^"]+)">')
card_positions = [(m.start(), m.group(1)) for m in card_open_pat.finditer(html_text)]
name_pat = re.compile(r'<code class="cmd-name">([^<]+)</code>')
print(f"Total cmd-cards: {len(card_positions)}")

# Build patches list
patches: list[tuple[int, int, str]] = []
injected = []
not_found = []

EX_LABEL = '<div class="example-label">Example</div>'
ex_open_pat = re.compile(r'<div class="cmd-example">')

for i, (start, card_id) in enumerate(card_positions):
    end = card_positions[i + 1][0] if i + 1 < len(card_positions) else len(html_text)
    card_html = html_text[start:end]

    nm = name_pat.search(card_html)
    cmd_name = nm.group(1) if nm else ''

    pdf_text = lookup_example(cmd_name) if cmd_name else None

    if not pdf_text:
        not_found.append({'card_id': card_id, 'cmd_name': cmd_name})
        continue

    # Escape for HTML
    escaped = html_mod.escape(pdf_text)
    new_ex_div = f'<div class="cmd-example">{EX_LABEL}<pre><code>{escaped}</code></pre></div>'

    # Find the complete cmd-example div using depth-counting
    ex_m = ex_open_pat.search(card_html)
    if ex_m:
        ex_open = ex_m.start()
        ex_close = find_div_end(card_html, ex_open)
        new_card = card_html[:ex_open] + new_ex_div + card_html[ex_close:]
    else:
        # No cmd-example div — insert before closing </div></div> of the card
        ins_pat = re.search(r'(</div>\s*</div>\s*)$', card_html.rstrip())
        if ins_pat:
            new_card = card_html[:ins_pat.start()] + new_ex_div + card_html[ins_pat.start():]
        else:
            not_found.append({'card_id': card_id, 'cmd_name': cmd_name, 'reason': 'no_body'})
            continue

    patches.append((start, end, new_card))
    injected.append({'card_id': card_id, 'cmd_name': cmd_name, 'example_len': len(pdf_text)})

print(f"\n✓ Will inject/overwrite: {len(injected)}")
print(f"✗ No PDF match:          {len(not_found)}")

# Apply patches in reverse order
patches.sort(key=lambda p: p[0], reverse=True)
html_chars = list(html_text)
for start, end, replacement in patches:
    html_chars[start:end] = list(replacement)
new_html = ''.join(html_chars)

Path('index.html').write_text(new_html, encoding='utf-8')
print(f"index.html updated ({len(new_html):,} bytes)")

# ── Save report ───────────────────────────────────────────────────────────────
report = {
    'run': 'pr9a',
    'example_headers_in_pdf': len(example_headers),
    'unique_cmd_examples': len(cmd_examples),
    'injected_count': len(injected),
    'not_found_count': len(not_found),
    'injected': injected,
    'not_found': not_found,
}
Path('pipeline_output/pr9a_inject_report.json').write_text(
    json.dumps(report, ensure_ascii=False, indent=2))

print("\nSample injected (first 15):")
for e in injected[:15]:
    print(f"  {e['card_id']:<45} {e['cmd_name']:<25} len={e['example_len']}")
print("\nNot found (first 20):")
for e in not_found[:20]:
    print(f"  {e['card_id']:<45} {e.get('cmd_name', '?')}")
