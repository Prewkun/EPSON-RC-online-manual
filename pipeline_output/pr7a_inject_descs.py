"""
PR 7a v2: Extract descriptions from SPEL PDF and inject into index.html
- Brief fallback for sections without Description block
- Multi-command section support (Arc/Arc3, CX/CY/CZ, etc.)
- Only processes cards with truly-empty cmd-desc
Sources:  pipeline_output/spel_ref_clean.txt
Output:   patched index.html  +  pipeline_output/pr7a_injection_report.json
"""
import re, json, html as html_mod
from pathlib import Path

# ── Parse PDF text ─────────────────────────────────────────────────────────
raw_lines = Path('pipeline_output/spel_ref_clean.txt').read_text(encoding='utf-8').splitlines()

sec_hdr_pat = re.compile(r'^3\.(\d+)\.(\d+)\s+(.+)$')
all_headers = [(i, l.rstrip()) for i, l in enumerate(raw_lines) if sec_hdr_pat.match(l.strip())]

# Body sections have large line-gap vs TOC sections
body_headers = []
for idx, (line_i, title) in enumerate(all_headers):
    gap_lines = all_headers[idx + 1][0] - line_i if idx + 1 < len(all_headers) else 999
    if gap_lines > 20:
        body_headers.append((line_i, title))

print(f"Body sections: {len(body_headers)}")

STOP_MARKERS = {'Description', 'See Also', 'Note', 'Syntax', 'Parameters',
                'Return Values', 'Example', 'Reference'}

def extract_section(start_line: int, end_line: int) -> tuple[str, str]:
    """Return (brief, description) from a body section."""
    lines = [l.rstrip() for l in raw_lines[start_line:end_line]]
    clean = []
    for l in lines:
        if re.match(r'^\d+$', l):                         continue
        if '\x0c' in l:                                    continue
        if 'SPEL+ Language Reference (RC800' in l:         continue
        if l.strip() in ('Rev.1', 'Original instructions'): continue
        clean.append(l)

    # Brief: first non-blank non-marker line after the header (line 0)
    brief = ''
    for l in clean[1:]:
        if l.strip() and l.strip() not in STOP_MARKERS:
            brief = l.strip()
            break

    # Description block: text between 'Description' marker and next stop marker
    desc_lines = []
    in_desc = False
    for l in clean:
        stripped = l.strip()
        if stripped == 'Description':
            in_desc = True
            continue
        if in_desc:
            if stripped in STOP_MARKERS:
                break
            desc_lines.append(l)

    desc = re.sub(r'\n{3,}', '\n\n', '\n'.join(desc_lines)).strip()
    return brief, desc


# Build {cmd_name_lower: text} — Description preferred, brief as fallback
# Multi-command headers (e.g. "Arc, Arc3 Statements") register all names
cmd_descs: dict[str, str] = {}
for idx, (line_i, header_title) in enumerate(body_headers):
    m = re.match(r'^3\.\d+\.\d+\s+(.+)$', header_title)
    if not m:
        continue
    full_name = m.group(1).strip()

    # Strip type suffix (handles both singular and plural)
    cmd_type = 'any'
    cmd_part = full_name
    for suffix in ('Statements', 'Statement', 'Functions', 'Function', 'Operator'):
        if full_name.endswith(' ' + suffix):
            cmd_part = full_name[: -len(suffix) - 1].strip()
            cmd_type = suffix.rstrip('s').lower()
            break

    end_line = body_headers[idx + 1][0] if idx + 1 < len(body_headers) else len(raw_lines)
    brief, desc = extract_section(line_i, end_line)
    text = desc if desc else brief  # fall back to brief if no Description section

    if not text:
        continue

    # Expand compound names:
    #   "GoSub...Return" → ["GoSub", "Return"]
    #   "ParseStr Statement / ParseStr Function" → ["ParseStr", "ParseStr"]
    #   "Arc, Arc3" → ["Arc", "Arc3"]
    #   "P# (1. Point Definition)" → ["P#"]   (strip parentheticals)
    expanded: list[str] = []
    for seg in re.split(r'[,/]', cmd_part):
        for sub in re.split(r'\.\.\.', seg):
            # Strip parenthetical qualifiers like "(System status trigger)"
            sub = re.sub(r'\s*\([^)]*\)', '', sub).strip()
            # Strip trailing type words that sometimes bleed through
            for tw in ('Statement', 'Statements', 'Function', 'Functions', 'Operator'):
                if sub.endswith(' ' + tw):
                    sub = sub[: -len(tw) - 1].strip()
            if sub:
                expanded.append(sub)

    for cmd_name in expanded:
        key = cmd_name.lower().rstrip('#$').rstrip()
        if not key:
            continue
        if key not in cmd_descs or cmd_type == 'statement':
            cmd_descs[key] = text

print(f"Unique commands with text: {len(cmd_descs)}")


def get_desc(command_name: str) -> str | None:
    """Look up description for a command name (case-insensitive, strips specials)."""
    name_key = command_name.lower().rstrip('$#').rstrip()
    for variant in [name_key, name_key.replace('_', ''), name_key.replace('-', '')]:
        if variant in cmd_descs and cmd_descs[variant]:
            return cmd_descs[variant]
    return None


# ── Scan HTML for truly-empty cards ───────────────────────────────────────
html_text = Path('index.html').read_text(encoding='utf-8')
card_open_pat = re.compile(r'<div class="cmd-card" id="(spel-cmd-[^"]+)">')
card_positions = [(m.start(), m.group(1)) for m in card_open_pat.finditer(html_text)]
print(f"Total cmd-cards: {len(card_positions)}")

# Find cards that need injection: cmd-desc missing or empty
# Also build a name lookup from HTML (cmd-name element)
name_from_card: dict[str, str] = {}
name_pat = re.compile(r'<code class="cmd-name">([^<]+)</code>')

truly_empty: list[tuple[str, str]] = []  # (card_id, reason)
for i, (start, card_id) in enumerate(card_positions):
    end = card_positions[i + 1][0] if i + 1 < len(card_positions) else len(html_text)
    card_html = html_text[start:end]

    nm = name_pat.search(card_html)
    if nm:
        name_from_card[card_id] = nm.group(1)

    desc_m = re.search(r'<div class="cmd-desc">(.*?)</div>', card_html, re.DOTALL)
    if desc_m:
        txt = re.sub(r'<[^>]+>', '', desc_m.group(1)).strip()
        if not txt:
            truly_empty.append((card_id, 'empty_div'))
    else:
        truly_empty.append((card_id, 'no_div'))

print(f"Cards still empty/missing: {len(truly_empty)}")

# ── Inject ─────────────────────────────────────────────────────────────────
patches: list[tuple[int, int, str]] = []
injected = []
missed   = []

pos_map = {cid: (i, pos) for i, (pos, cid) in enumerate(card_positions)}

for card_id, reason in truly_empty:
    cmd_name = name_from_card.get(card_id, '')
    desc_text = get_desc(cmd_name) if cmd_name else None

    if not desc_text:
        missed.append({'card_id': card_id, 'cmd_name': cmd_name})
        continue

    # Clean: collapse line breaks to spaces, normalise whitespace
    desc_clean = re.sub(r'\n+', ' ', desc_text)
    desc_clean = re.sub(r'\s{2,}', ' ', desc_clean).strip()
    new_desc_div = f'<div class="cmd-desc">{html_mod.escape(desc_clean)}</div>'

    i, start = pos_map[card_id]
    end = card_positions[i + 1][0] if i + 1 < len(card_positions) else len(html_text)
    card_html = html_text[start:end]

    if reason == 'empty_div':
        old_div = re.search(r'<div class="cmd-desc">.*?</div>', card_html, re.DOTALL).group(0)
        new_card = card_html.replace(old_div, new_desc_div, 1)
    else:  # no_div — insert after cmd-syntax or after cmd-body
        syntax_m = re.search(r'<div class="cmd-syntax">.*?</div>', card_html, re.DOTALL)
        if syntax_m:
            insert_at = syntax_m.end()
        else:
            body_m = re.search(r'<div class="cmd-body">', card_html)
            if not body_m:
                missed.append({'card_id': card_id, 'cmd_name': cmd_name, 'reason': 'no_body'})
                continue
            insert_at = body_m.end()
        new_card = card_html[:insert_at] + new_desc_div + card_html[insert_at:]

    patches.append((start, end, new_card))
    injected.append({'card_id': card_id, 'cmd_name': cmd_name, 'desc_len': len(desc_clean)})

print(f"\n✓ Will inject: {len(injected)}")
print(f"✗ Not found:   {len(missed)}")

# Apply patches in reverse order so positions stay valid
patches.sort(key=lambda p: p[0], reverse=True)
html_chars = list(html_text)
for start, end, replacement in patches:
    html_chars[start:end] = list(replacement)
new_html = ''.join(html_chars)

Path('index.html').write_text(new_html, encoding='utf-8')
print(f"index.html updated ({len(new_html):,} bytes)")

# ── Save report ─────────────────────────────────────────────────────────────
report = {
    'run': 'v2',
    'injected_count': len(injected),
    'missed_count': len(missed),
    'pdf_coverage': len(cmd_descs),
    'injected': injected,
    'missed': missed,
}
Path('pipeline_output/pr7a_injection_report.json').write_text(
    json.dumps(report, ensure_ascii=False, indent=2))

print(f"\nSample (first 20):")
for e in injected[:20]:
    print(f"  {e['card_id']:<45} {e['cmd_name']:<25} len={e['desc_len']}")
if missed:
    print(f"\nStill missing (first 20):")
    for e in missed[:20]:
        print(f"  {e['card_id']:<45} {e.get('cmd_name', '?')}")
