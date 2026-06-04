# Adapting Input Formats

## DOCX (Word Documents)

Replace the Phase 1 extraction block with `python-docx`:

```python
from docx import Document
from docx.shared import Pt

def extract_from_docx(path: str) -> dict:
    doc = Document(path)
    blocks = []
    tables = []

    for elem in doc.element.body:
        tag = elem.tag.split('}')[-1]

        if tag == 'p':
            para = elem
            text = ''.join(r.text for r in para.findall('.//{}r'))
            style = para.find('.//{}pStyle')
            style_val = style.get('{}val','') if style is not None else ''

            # Map Word styles to block types
            if 'Heading1' in style_val:
                btype = 'chapter_heading'
            elif 'Heading2' in style_val or 'Heading3' in style_val:
                btype = 'section_heading'
            elif text.strip().startswith(('WARNING','DANGER','CAUTION','NOTE')):
                btype = text.strip().split()[0].lower()
            elif re.match(r'^Step\s+\d+', text.strip(), re.IGNORECASE):
                btype = 'step'
            else:
                btype = 'body'

            if text.strip():
                blocks.append({'type': btype, 'text': text.strip()})

        elif tag == 'tbl':
            # Extract table rows
            rows = []
            for row in elem.findall('.//{}tr'):
                cells = [
                    ''.join(r.text or '' for r in cell.findall('.//{}r'))
                    for cell in row.findall('.//{}tc')
                ]
                rows.append(cells)
            if rows:
                tables.append({'headers': rows[0], 'rows': rows[1:]})

    return {'blocks': blocks, 'tables': tables}
```

The rest of the pipeline is unchanged — feed the same `content_map.json` schema into Phase 2 onwards.

**Install**: `pip install python-docx --break-system-packages`

---

## Scanned PDFs (Image-based)

Add a Tesseract OCR pre-pass before Phase 1:

```python
import pytesseract
from pdf2image import convert_from_path
from PIL import Image

def ocr_pdf(path: str) -> list[str]:
    """Returns list of page text strings."""
    pages = convert_from_path(path, dpi=300)
    texts = []
    for page_img in pages:
        text = pytesseract.image_to_string(page_img, lang='eng')
        texts.append(text)
    return texts
```

Then pass the extracted text into Phase 1's block classifier instead of `pdfplumber`. Layout reconstruction (columns, tables) is less reliable from OCR — consider using `pytesseract.image_to_data()` for bounding-box-aware extraction on complex layouts.

**Install**:

```
pip install pytesseract pdf2image Pillow --break-system-packages
apt-get install -y tesseract-ocr poppler-utils
```

---

## Multi-Volume Manuals

Run Phase 1 on each volume, then merge before Phase 2:

```python
import json

volumes = [
    'content_map_vol1.json',
    'content_map_vol2.json',
    'content_map_vol3.json',
]

merged = json.load(open(volumes[0]))
page_offset = merged['metadata']['pages']

for vol_path in volumes[1:]:
    vol = json.load(open(vol_path))

    # Offset page numbers to avoid collisions
    for page in vol['pages']:
        page['page_number'] += page_offset
        for block in page['blocks']:
            block['page'] = block.get('page', 0) + page_offset

    merged['pages'].extend(vol['pages'])
    merged['structure']['chapters'].extend(vol['structure']['chapters'])
    merged['structure']['all_blocks'].extend(vol['structure']['all_blocks'])

    # Update stats
    for k, v in vol['stats']['block_type_counts'].items():
        merged['stats']['block_type_counts'][k] = \
            merged['stats']['block_type_counts'].get(k, 0) + v
    merged['stats']['total_pages']  += vol['metadata']['pages']
    merged['stats']['total_blocks'] += vol['stats']['total_blocks']
    merged['stats']['total_tables'] += vol['stats']['total_tables']
    merged['stats']['total_chapters'] += vol['stats']['total_chapters']
    page_offset += vol['metadata']['pages']

json.dump(merged, open('content_map_merged.json', 'w'), indent=2)
```

Then run Phase 2–6 on `content_map_merged.json` as normal.

---

## HTML / Markdown Source Documents

For documents already in HTML or Markdown format:

```python
# Markdown
import re

def extract_from_markdown(path: str) -> list[dict]:
    text = open(path).read()
    blocks = []
    for line in text.split('\n'):
        line = line.strip()
        if not line: continue
        if line.startswith('# '):
            blocks.append({'type': 'chapter_heading', 'text': line[2:]})
        elif line.startswith('## ') or line.startswith('### '):
            blocks.append({'type': 'section_heading', 'text': line.lstrip('#').strip()})
        elif re.match(r'^\d+\.\s', line) or re.match(r'^Step\s+\d+', line, re.I):
            blocks.append({'type': 'step', 'text': line})
        elif line.upper().startswith(('WARNING', 'DANGER', 'CAUTION', '> ⚠', '> 🔴')):
            btype = next((t for t in ['danger','warning','caution','note']
                         if t in line.lower()), 'note')
            blocks.append({'type': btype, 'text': line})
        else:
            blocks.append({'type': 'body', 'text': line})
    return blocks
```

---

## Token Budget by Document Size

| Pages | Est. words | AI tokens (optimised) | Est. cost |
|-------|------------|----------------------|-----------|
| 50    | 15,000     | ~15,000              | ~$0.04    |
| 200   | 60,000     | ~60,000              | ~$0.18    |
| 500   | 150,000    | ~150,000             | ~$0.45    |
| 1,000 | 300,000    | ~300,000             | ~$0.90    |

Assumes ~30–40% of body text blocks flagged for AI, Haiku for most, Sonnet only for troubleshooting tables. Cached re-runs on unchanged content: ~0 tokens.
