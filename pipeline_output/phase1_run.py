"""
Phase 1: Document Ingestion & Parsing Agent
============================================
Input : PDF manual file
Output: structured JSON (content_map.json) + summary report

Extracts:
  - Document metadata
  - Chapter / section hierarchy
  - Content blocks typed as: heading | body | step | table | warning | danger | note | callout
"""

import json
import re
import pdfplumber
from pathlib import Path

# â”€â”€ CONFIG â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
INPUT_PDF = r"E:\repos\reposEPSON-RC-online-manual\Manual\e_EpsonRC+UsersGuide80_r1.pdf"
OUTPUT_JSON = r"E:\repos\reposEPSON-RC-online-manual\pipeline_output\content_map.json"
OUTPUT_REPORT = r"E:\repos\reposEPSON-RC-online-manual\pipeline_output\phase1_report.txt"

# â”€â”€ HELPERS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def classify_block(text: str) -> str:
    """Heuristically classify a text block into a content type."""
    t = text.strip()
    if not t:
        return "empty"

    upper_ratio = sum(1 for c in t if c.isupper()) / max(len(t), 1)

    # Safety callouts
    if t.startswith("DANGER"):                         return "danger"
    if t.startswith("WARNING"):                        return "warning"
    if t.startswith("CAUTION"):                        return "caution"
    if t.startswith("NOTE"):                           return "note"

    # Numbered steps
    if re.match(r'^Step\s+\d+', t, re.IGNORECASE):    return "step"
    if re.match(r'^\d+\.\s', t):                       return "step"

    # Headings  (short + title-case or ALL CAPS)
    words = t.split()
    if len(words) <= 10 and (t.istitle() or upper_ratio > 0.5):
        # Chapter / section headings
        if re.match(r'^Chapter\s+\d+', t, re.IGNORECASE):  return "chapter_heading"
        if re.match(r'^\d+\.\d+', t):                       return "section_heading"
        if t == t.upper() and len(words) <= 6:              return "chapter_heading"
        return "section_heading"

    return "body"


def extract_tables_from_page(page) -> list:
    """Extract tables from a pdfplumber page object."""
    tables = []
    raw = page.extract_tables()
    for t in raw:
        if not t or len(t) < 2:
            continue
        headers = [str(c).strip() if c else "" for c in t[0]]
        rows = []
        for row in t[1:]:
            rows.append([str(c).strip() if c else "" for c in row])
        tables.append({"headers": headers, "rows": rows})
    return tables


def extract_text_blocks(page) -> list:
    """Split page text into logical blocks (split on blank lines)."""
    raw_text = page.extract_text() or ""
    # Split on double newline or lines that are just whitespace
    raw_blocks = re.split(r'\n\s*\n', raw_text)
    blocks = []
    for b in raw_blocks:
        cleaned = b.strip()
        if cleaned:
            blocks.append(cleaned)
    return blocks


# â”€â”€ MAIN AGENT â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def run_parser_agent(pdf_path: str) -> dict:
    print(f"\n{'='*60}")
    print("  Phase 1: Document Ingestion & Parsing Agent")
    print(f"{'='*60}")
    print(f"  Input : {pdf_path}")

    content_map = {
        "metadata": {},
        "stats": {},
        "pages": [],
        "structure": {
            "chapters": [],
            "all_blocks": []
        }
    }

    with pdfplumber.open(pdf_path) as pdf:

        # â”€â”€ Metadata â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        meta = pdf.metadata or {}
        content_map["metadata"] = {
            "title":    meta.get("Title", "Unknown"),
            "author":   meta.get("Author", "Unknown"),
            "creator":  meta.get("Creator", "Unknown"),
            "pages":    len(pdf.pages),
            "source_file": Path(pdf_path).name,
        }
        print(f"\n  [Metadata]")
        for k, v in content_map["metadata"].items():
            print(f"    {k:<15}: {v}")

        # â”€â”€ Per-page extraction â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        total_blocks = 0
        type_counts  = {}
        current_chapter = None

        for page_num, page in enumerate(pdf.pages, start=1):
            page_data = {
                "page_number": page_num,
                "blocks": [],
                "tables": []
            }

            # Tables
            tables = extract_tables_from_page(page)
            page_data["tables"] = tables

            # Text blocks
            text_blocks = extract_text_blocks(page)
            for raw_text in text_blocks:
                # Each raw block may contain multiple lines; handle step lists
                lines = raw_text.split('\n')
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    block_type = classify_block(line)
                    if block_type == "empty":
                        continue

                    block = {
                        "id":      f"p{page_num}_b{total_blocks:04d}",
                        "page":    page_num,
                        "type":    block_type,
                        "text":    line,
                    }

                    # Track chapter structure
                    if block_type == "chapter_heading":
                        current_chapter = {
                            "title":    line,
                            "page":     page_num,
                            "sections": [],
                            "block_id": block["id"]
                        }
                        content_map["structure"]["chapters"].append(current_chapter)
                        block["chapter"] = line

                    elif block_type == "section_heading" and current_chapter:
                        current_chapter["sections"].append({
                            "title":    line,
                            "page":     page_num,
                            "block_id": block["id"]
                        })
                        block["chapter"] = current_chapter["title"]

                    page_data["blocks"].append(block)
                    content_map["structure"]["all_blocks"].append(block)
                    type_counts[block_type] = type_counts.get(block_type, 0) + 1
                    total_blocks += 1

            content_map["pages"].append(page_data)
            print(f"  Page {page_num:>2}: {len(page_data['blocks']):>3} blocks, "
                  f"{len(tables):>1} tables")

        # â”€â”€ Stats â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        content_map["stats"] = {
            "total_pages":       len(pdf.pages),
            "total_blocks":      total_blocks,
            "total_tables":      sum(len(p["tables"]) for p in content_map["pages"]),
            "total_chapters":    len(content_map["structure"]["chapters"]),
            "block_type_counts": type_counts,
        }

    return content_map


def print_report(content_map: dict) -> str:
    lines = []
    lines.append("=" * 60)
    lines.append("  PHASE 1 PARSING REPORT")
    lines.append("=" * 60)

    m = content_map["metadata"]
    lines.append(f"\n  Document : {m['title']}")
    lines.append(f"  Source   : {m['source_file']}")
    lines.append(f"  Pages    : {m['pages']}")

    s = content_map["stats"]
    lines.append(f"\n  --- Extraction Summary ---")
    lines.append(f"  Total blocks extracted : {s['total_blocks']}")
    lines.append(f"  Total tables extracted : {s['total_tables']}")
    lines.append(f"  Chapters detected      : {s['total_chapters']}")

    lines.append(f"\n  --- Block Types ---")
    for btype, count in sorted(s["block_type_counts"].items(), key=lambda x: -x[1]):
        lines.append(f"    {btype:<20}: {count:>4}")

    lines.append(f"\n  --- Document Structure ---")
    for ch in content_map["structure"]["chapters"]:
        lines.append(f"\n  [Chapter] {ch['title']}  (page {ch['page']})")
        for sec in ch["sections"]:
            lines.append(f"    [Section] {sec['title']}  (page {sec['page']})")

    lines.append(f"\n  --- Sample Blocks by Type ---")
    shown = {}
    for block in content_map["structure"]["all_blocks"]:
        bt = block["type"]
        if bt not in shown:
            lines.append(f"\n  TYPE: {bt.upper()}")
            lines.append(f"    \"{block['text'][:120]}\"")
            shown[bt] = True
        if len(shown) >= 8:
            break

    lines.append("\n" + "=" * 60)
    lines.append("  Phase 1 Complete â€” content_map.json ready for Phase 2")
    lines.append("=" * 60)
    return "\n".join(lines)


# â”€â”€ RUN â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
if __name__ == "__main__":
    content_map = run_parser_agent(INPUT_PDF)

    # Save JSON
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(content_map, f, indent=2, ensure_ascii=False)
    print(f"\n  Saved: {OUTPUT_JSON}")

    # Save + print report
    report = print_report(content_map)
    print(report)
    with open(OUTPUT_REPORT, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"  Saved: {OUTPUT_REPORT}")

