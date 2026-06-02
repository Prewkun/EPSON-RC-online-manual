"""
Phase 2: Structure Analyzer Agent
===================================
Input : content_map.json  (from Phase 1)
Output: content_tree.json (clean hierarchy, typed sections, AI-routing flags)

Token Strategy:
  - 95% rule-based (zero tokens)
  - AI only called for ambiguous body blocks that can't be auto-classified
  - Every block gets an 'ai_needed' flag so Phase 3 knows what to skip
  - Result is cached so re-runs cost 0 tokens

Content node types produced:
  cover | toc | chapter | section |
  procedure | checklist | spec_table | troubleshoot_table |
  safety_callout | body_text | metadata_block
"""

import json
import re
import hashlib
import os
from pathlib import Path
from typing import Optional

# â”€â”€ CONFIG â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
INPUT_JSON = r"E:\repos\reposEPSON-RC-online-manual\pipeline_output\content_map.json"
OUTPUT_JSON = r"E:\repos\reposEPSON-RC-online-manual\pipeline_output\content_tree.json"
CACHE_FILE = r"E:\repos\reposEPSON-RC-online-manual\pipeline_output\.phase2_cache.json"
OUTPUT_REPORT = r"E:\repos\reposEPSON-RC-online-manual\pipeline_output\phase2_report.txt"

# â”€â”€ CACHE HELPERS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def load_cache() -> dict:
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE) as f:
            return json.load(f)
    return {}

def save_cache(cache: dict):
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)

def block_hash(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()[:12]

# â”€â”€ RULE-BASED CLASSIFIERS (0 tokens) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def is_toc_page(blocks: list) -> bool:
    texts = [b["text"].lower() for b in blocks]
    return any("table of contents" in t or "chapter" in t and "page" in t for t in texts)

def is_cover_page(blocks: list, page_num: int) -> bool:
    return page_num == 1

def classify_table(headers: list) -> str:
    """Determine table semantic type from its headers â€” zero tokens."""
    h = " ".join(headers).lower()
    if any(w in h for w in ["symptom", "fault", "problem", "cause", "corrective"]):
        return "troubleshoot_table"
    if any(w in h for w in ["step", "check", "item", "result", "expected"]):
        return "checklist_table"
    if any(w in h for w in ["parameter", "value", "unit", "specification", "spec"]):
        return "spec_table"
    if any(w in h for w in ["interval", "task", "maintenance", "schedule"]):
        return "maintenance_table"
    if any(w in h for w in ["component", "part", "description"]):
        return "parts_table"
    return "generic_table"

def classify_section_by_title(title: str) -> str:
    """Map section titles to semantic types â€” zero tokens."""
    t = title.lower()
    if any(w in t for w in ["safety", "danger", "warning", "hazard"]):
        return "safety_section"
    if any(w in t for w in ["spec", "technical", "parameter", "dimension"]):
        return "spec_section"
    if any(w in t for w in ["install", "setup", "assembly", "mount"]):
        return "install_section"
    if any(w in t for w in ["operat", "start", "run", "procedure", "checklist"]):
        return "operation_section"
    if any(w in t for w in ["mainten", "service", "lubricate", "oil change", "filter"]):
        return "maintenance_section"
    if any(w in t for w in ["troubleshoot", "fault", "diagnos", "problem", "error"]):
        return "troubleshoot_section"
    return "general_section"

def blocks_form_procedure(blocks: list) -> bool:
    """True if a block group contains 3+ sequential steps."""
    step_count = sum(1 for b in blocks if b["type"] == "step")
    return step_count >= 3

def blocks_form_checklist(blocks: list, tables: list) -> bool:
    """True if block group has a checklist-style table."""
    return any(classify_table(t["headers"]) == "checklist_table" for t in tables)

def needs_ai_enrichment(block: dict) -> bool:
    """
    Decide if a block actually needs AI â€” only send ambiguous body text.
    Rule-based content is flagged False (skip AI entirely).
    """
    t = block["type"]
    # These are fully handled by rules â€” no AI needed
    if t in ("step", "warning", "danger", "caution", "note",
             "chapter_heading", "section_heading"):
        return False
    # Very short body text â€” not worth AI call
    if t == "body" and len(block["text"].split()) < 8:
        return False
    # Body text that is clearly a label or figure caption
    text = block["text"].lower()
    if re.match(r'^(fig|figure|table|ref|see also|note|part no)', text):
        return False
    # Everything else (substantive body text) benefits from AI rewriting
    if t == "body" and len(block["text"].split()) >= 8:
        return True
    return False

# â”€â”€ SECTION BUILDER â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def build_section_node(title: str, page: int, blocks: list,
                       tables: list, section_id: str) -> dict:
    """Assemble a clean section node with typed content groups."""

    section_type = classify_section_by_title(title)

    # Group steps into a procedure node
    procedures = []
    current_proc = []
    for b in blocks:
        if b["type"] == "step":
            current_proc.append(b["text"])
        else:
            if current_proc:
                procedures.append(current_proc)
                current_proc = []
    if current_proc:
        procedures.append(current_proc)

    # Collect callouts
    callouts = [b for b in blocks if b["type"] in ("warning", "danger", "caution", "note")]

    # Classify tables
    typed_tables = []
    for t in tables:
        typed_tables.append({
            "table_type": classify_table(t["headers"]),
            "headers":    t["headers"],
            "rows":       t["rows"],
            "row_count":  len(t["rows"]),
        })

    # Body blocks â€” flag which need AI
    body_blocks = []
    ai_needed_count = 0
    for b in blocks:
        if b["type"] == "body":
            needs_ai = needs_ai_enrichment(b)
            if needs_ai:
                ai_needed_count += 1
            body_blocks.append({
                "id":       b["id"],
                "text":     b["text"],
                "ai_needed": needs_ai,
            })

    # Determine if full section needs AI (only if it has enrichable body text)
    section_needs_ai = ai_needed_count > 0

    return {
        "id":           section_id,
        "title":        title,
        "page":         page,
        "section_type": section_type,
        "ai_needed":    section_needs_ai,
        "stats": {
            "body_blocks":    len(body_blocks),
            "ai_needed_blocks": ai_needed_count,
            "callouts":       len(callouts),
            "procedures":     len(procedures),
            "tables":         len(typed_tables),
        },
        "content": {
            "callouts":   [{"type": c["type"], "text": c["text"]} for c in callouts],
            "procedures": [{"steps": p} for p in procedures] if procedures else [],
            "tables":     typed_tables,
            "body":       body_blocks,
        }
    }

# â”€â”€ MAIN AGENT â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def run_structure_agent(input_path: str) -> dict:
    print(f"\n{'='*60}")
    print("  Phase 2: Structure Analyzer Agent")
    print(f"{'='*60}")

    with open(input_path) as f:
        content_map = json.load(f)

    cache = load_cache()

    # Build page lookup: page_number â†’ {blocks, tables}
    page_lookup = {}
    for page in content_map["pages"]:
        page_lookup[page["page_number"]] = {
            "blocks": page["blocks"],
            "tables": page["tables"],
        }

    content_tree = {
        "metadata":   content_map["metadata"],
        "token_plan": {},
        "chapters":   [],
    }

    # â”€â”€ Identify special pages â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    special_pages = set()
    for pnum, pdata in page_lookup.items():
        if is_cover_page(pdata["blocks"], pnum):
            special_pages.add(pnum)
            content_tree["cover_page"] = {
                "page": pnum,
                "type": "cover",
                "ai_needed": False,   # cover is purely presentational
                "blocks": [b["text"] for b in pdata["blocks"]]
            }
            print(f"  Page {pnum}: â†’ cover (no AI needed)")

        elif is_toc_page(pdata["blocks"]):
            special_pages.add(pnum)
            content_tree["toc_page"] = {
                "page": pnum,
                "type": "toc",
                "ai_needed": False,   # TOC is auto-generated from structure
                "note": "Will be auto-generated from chapter/section tree"
            }
            print(f"  Page {pnum}: â†’ table of contents (no AI needed)")

    # â”€â”€ Process chapters â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    raw_chapters = content_map["structure"]["chapters"]

    for ch_idx, ch in enumerate(raw_chapters):
        ch_page  = ch["page"]
        ch_title = ch["title"]

        # Determine page range for this chapter
        next_ch_page = raw_chapters[ch_idx + 1]["page"] if ch_idx + 1 < len(raw_chapters) else 9999
        chapter_pages = range(ch_page, next_ch_page)

        # Collect all blocks and tables for this chapter
        ch_blocks = []
        ch_tables = []
        for pnum in chapter_pages:
            if pnum in page_lookup and pnum not in special_pages:
                ch_blocks.extend(page_lookup[pnum]["blocks"])
                ch_tables.extend(page_lookup[pnum]["tables"])

        chapter_type = classify_section_by_title(ch_title)

        # â”€â”€ Build sections within chapter â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        sections = []
        current_section_title = None
        current_section_page  = ch_page
        current_blocks        = []
        current_tables        = []
        table_iter            = iter(ch_tables)

        for block in ch_blocks:
            if block["type"] == "section_heading":
                # Save previous section
                if current_section_title and current_blocks:
                    sec_id = f"ch{ch_idx+1}_sec{len(sections)+1}"
                    cached_hash = block_hash(current_section_title + str(len(current_blocks)))
                    if cached_hash in cache:
                        sections.append(cache[cached_hash])
                        print(f"    [CACHE HIT] {current_section_title[:50]}")
                    else:
                        node = build_section_node(
                            current_section_title, current_section_page,
                            current_blocks, current_tables, sec_id)
                        cache[cached_hash] = node
                        sections.append(node)
                        ai_flag = "âš¡ AI needed" if node["ai_needed"] else "âœ“ rule-based"
                        print(f"    Section: {current_section_title[:50]:<50} [{ai_flag}]")

                # Start new section
                current_section_title = block["text"]
                current_section_page  = block["page"]
                current_blocks        = []
                current_tables        = []
            else:
                current_blocks.append(block)

        # Final section
        if current_section_title and current_blocks:
            sec_id = f"ch{ch_idx+1}_sec{len(sections)+1}"
            node = build_section_node(
                current_section_title, current_section_page,
                current_blocks, ch_tables, sec_id)
            ai_flag = "âš¡ AI needed" if node["ai_needed"] else "âœ“ rule-based"
            print(f"    Section: {current_section_title[:50]:<50} [{ai_flag}]")
            sections.append(node)

        chapter_node = {
            "id":           f"ch{ch_idx+1}",
            "title":        ch_title,
            "page":         ch_page,
            "chapter_type": chapter_type,
            "section_count": len(sections),
            "sections":     sections,
        }
        content_tree["chapters"].append(chapter_node)
        print(f"\n  Chapter {ch_idx+1}: '{ch_title}' â†’ {len(sections)} sections")

    save_cache(cache)

    # â”€â”€ Token Plan â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    all_sections = [s for ch in content_tree["chapters"] for s in ch["sections"]]
    ai_sections    = [s for s in all_sections if s["ai_needed"]]
    noai_sections  = [s for s in all_sections if not s["ai_needed"]]
    total_ai_blocks = sum(s["stats"]["ai_needed_blocks"] for s in ai_sections)
    total_blocks    = sum(s["stats"]["body_blocks"] for s in all_sections)
    skipped_blocks  = total_blocks - total_ai_blocks

    # Rough token estimate: avg 15 tokens/block in + 30 tokens/block out
    est_tokens_without_strategy = total_blocks * 45
    est_tokens_with_strategy    = total_ai_blocks * 45
    savings_pct = round((1 - est_tokens_with_strategy / max(est_tokens_without_strategy, 1)) * 100)

    content_tree["token_plan"] = {
        "total_sections":       len(all_sections),
        "sections_needing_ai":  len(ai_sections),
        "sections_rule_based":  len(noai_sections),
        "total_body_blocks":    total_blocks,
        "blocks_needing_ai":    total_ai_blocks,
        "blocks_skipping_ai":   skipped_blocks,
        "est_tokens_naive":     est_tokens_without_strategy,
        "est_tokens_optimized": est_tokens_with_strategy,
        "estimated_savings_pct": savings_pct,
        "ai_sections_list": [
            {"id": s["id"], "title": s["title"], "ai_blocks": s["stats"]["ai_needed_blocks"]}
            for s in ai_sections
        ]
    }

    return content_tree


# â”€â”€ REPORT â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def print_report(tree: dict) -> str:
    lines = []
    lines.append("=" * 60)
    lines.append("  PHASE 2 STRUCTURE ANALYSIS REPORT")
    lines.append("=" * 60)

    tp = tree["token_plan"]
    lines.append(f"\n  Total sections built   : {tp['total_sections']}")
    lines.append(f"  Rule-based (0 tokens)  : {tp['sections_rule_based']}")
    lines.append(f"  Need AI enrichment     : {tp['sections_needing_ai']}")

    lines.append(f"\n  --- Token Efficiency ---")
    lines.append(f"  Body blocks total      : {tp['total_body_blocks']}")
    lines.append(f"  Blocks skipping AI     : {tp['blocks_skipping_ai']}")
    lines.append(f"  Blocks needing AI      : {tp['blocks_needing_ai']}")
    lines.append(f"  Est. tokens (naive)    : {tp['est_tokens_naive']:,}")
    lines.append(f"  Est. tokens (optimized): {tp['est_tokens_optimized']:,}")
    lines.append(f"  Token savings          : {tp['estimated_savings_pct']}%")

    lines.append(f"\n  --- Chapter Summary ---")
    for ch in tree["chapters"]:
        lines.append(f"\n  [{ch['chapter_type'].upper()}] {ch['title']}")
        for sec in ch["sections"]:
            ai_flag = "âš¡ AI" if sec["ai_needed"] else "âœ“ rules"
            s = sec["stats"]
            lines.append(
                f"    {sec['title'][:48]:<48} [{ai_flag}]"
                f"  steps={s['procedures']}  tables={s['tables']}  callouts={s['callouts']}"
            )

    lines.append(f"\n  --- Sections Queued for AI (Phase 3) ---")
    for item in tp["ai_sections_list"]:
        lines.append(f"  â€¢ {item['title'][:55]}  ({item['ai_blocks']} blocks)")

    lines.append("\n" + "=" * 60)
    lines.append("  Phase 2 Complete â€” content_tree.json ready for Phase 3")
    lines.append("=" * 60)
    return "\n".join(lines)


# â”€â”€ RUN â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
if __name__ == "__main__":
    tree = run_structure_agent(INPUT_JSON)

    with open(OUTPUT_JSON, "w") as f:
        json.dump(tree, f, indent=2, ensure_ascii=False)
    print(f"\n  Saved: {OUTPUT_JSON}")

    report = print_report(tree)
    print(report)
    with open(OUTPUT_REPORT, "w") as f:
        f.write(report)
    print(f"  Saved: {OUTPUT_REPORT}")


