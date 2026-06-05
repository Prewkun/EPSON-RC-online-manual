"""
PR 9b: Remove artifact stub cmd-cards from index.html.

Stubs are pipeline fragments where cmd-name is an all-lowercase common
English word with no Syntax and no Description content (e.g. "text",
"at", "coordinate", "but", "motion", "tracking", etc.).

These were incorrectly generated as command cards by the original pipeline
when it parsed section prose as command entries.

Criteria for removal:
  - cmd-name matches ^[a-z][a-z ]+$  (all lowercase, no digits/specials)
  - cmd-name length < 20 characters
  - Has NO cmd-desc content  (empty or missing)
  - Has NO cmd-syntax content (empty or missing)

Exceptions kept (have real content despite lowercase name):
  - spel-cmd-on-2, spel-cmd-speed-2, spel-cmd-speed-3
    (duplicate entries of real commands — reviewed manually)
"""
import re, json
from pathlib import Path

html_text = Path('index.html').read_text(encoding='utf-8')
card_open_pat = re.compile(r'<div class="cmd-card" id="(spel-cmd-[^"]+)">')
card_positions = [(m.start(), m.group(1)) for m in card_open_pat.finditer(html_text)]
name_pat  = re.compile(r'<code class="cmd-name">([^<]+)</code>')
desc_pat  = re.compile(r'<div class="cmd-desc">(.*?)</div>', re.DOTALL)
syntax_pat = re.compile(r'<div class="cmd-syntax">(.*?)</div>', re.DOTALL)

print(f"Total cmd-cards before removal: {len(card_positions)}")

# Cards to keep even though they look like stubs
KEEP_EXCEPTIONS = {'spel-cmd-on-2', 'spel-cmd-speed-2', 'spel-cmd-speed-3'}

stubs_to_remove: list[tuple[int, int, str]] = []  # (start, end, card_id)

for i, (start, card_id) in enumerate(card_positions):
    if card_id in KEEP_EXCEPTIONS:
        continue
    end = card_positions[i + 1][0] if i + 1 < len(card_positions) else len(html_text)
    seg = html_text[start:end]

    nm = name_pat.search(seg)
    if not nm:
        continue
    cmd = nm.group(1).strip()

    # Only target all-lowercase words
    if not re.match(r'^[a-z][a-z ]+$', cmd) or len(cmd) >= 20:
        continue

    # Confirm: no desc content
    dm = desc_pat.search(seg)
    desc_text = re.sub(r'<[^>]+>', '', dm.group(1)).strip() if dm else ''

    # Confirm: no syntax content
    sm = syntax_pat.search(seg)
    syn_text = re.sub(r'<[^>]+>', '', sm.group(1)).strip() if sm else ''

    if desc_text or syn_text:
        print(f"  SKIP (has content): {card_id!r} name={cmd!r}")
        continue

    stubs_to_remove.append((start, end, card_id))

print(f"Stub cards to remove: {len(stubs_to_remove)}")
for _, _, cid in stubs_to_remove:
    print(f"  {cid}")

# Remove in reverse order
stubs_to_remove.sort(key=lambda x: x[0], reverse=True)
html_chars = list(html_text)
for start, end, _ in stubs_to_remove:
    del html_chars[start:end]
new_html = ''.join(html_chars)

# Verify count
remaining = len(card_open_pat.findall(new_html))
print(f"\nCards remaining after removal: {remaining}")
print(f"Removed: {len(card_positions) - remaining}")

Path('index.html').write_text(new_html, encoding='utf-8')
print(f"index.html updated ({len(new_html):,} bytes)")

# Save report
report = {
    'run': 'pr9b',
    'original_count': len(card_positions),
    'removed_count': len(stubs_to_remove),
    'remaining_count': remaining,
    'removed': [cid for _, _, cid in stubs_to_remove],
}
Path('pipeline_output/pr9b_stub_removal_report.json').write_text(
    json.dumps(report, ensure_ascii=False, indent=2))
print("Report saved to pipeline_output/pr9b_stub_removal_report.json")
