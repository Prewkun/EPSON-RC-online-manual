"""
Phase 3: Content Enrichment Agent
====================================
Input : content_tree.json  (from Phase 2)
Output: enriched_tree.json

Token Strategy (all 4 methods active):
  1. SKIP    â€” only process blocks flagged ai_needed=True
  2. CACHE   â€” hash each block; skip API if already processed
  3. ROUTE   â€” Haiku for simple rewrites, Sonnet for complex reasoning
  4. BATCH   â€” group small blocks into one API call

Model routing rules:
  Haiku  â†’ body text rewrite, short descriptions        (cheap)
  Sonnet â†’ troubleshoot tree, glossary, procedure logic  (powerful)

Enrichment tasks per content type:
  body_text        â†’ rewrite to plain web-friendly prose
  spec_table       â†’ add plain-English summary sentence
  troubleshoot     â†’ restructure into {symptom, causes:[{cause, fix}]}
  maintenance_tableâ†’ add priority + estimated_time fields
  checklist_table  â†’ convert rows to {item, expected, pass_fail_field}
  procedure        â†’ already structured â€” no AI needed (skipped)
  callout          â†’ already typed â€” no AI needed (skipped)
"""

import json
import re
import hashlib
import os
import time
from pathlib import Path

# â”€â”€ CONFIG â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
INPUT_JSON = r"E:\repos\reposEPSON-RC-online-manual\pipeline_output\content_tree.json"
OUTPUT_JSON = r"E:\repos\reposEPSON-RC-online-manual\pipeline_output\enriched_tree.json"
CACHE_FILE = r"E:\repos\reposEPSON-RC-online-manual\pipeline_output\.phase3_cache.json"
OUTPUT_REPORT = r"E:\repos\reposEPSON-RC-online-manual\pipeline_output\phase3_report.txt"

MODEL_HAIKU  = "claude-haiku-4-5-20251001"
MODEL_SONNET = "claude-sonnet-4-6"

# â”€â”€ CACHE â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def load_cache() -> dict:
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE) as f:
            return json.load(f)
    return {}

def save_cache(cache: dict):
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)

def make_hash(content: str) -> str:
    return hashlib.md5(content.encode()).hexdigest()[:16]

# â”€â”€ MODEL ROUTER â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def choose_model(task_type: str) -> str:
    """Route to cheapest model that can handle the task."""
    sonnet_tasks = {"troubleshoot", "decision_tree", "glossary", "complex_rewrite"}
    return MODEL_SONNET if task_type in sonnet_tasks else MODEL_HAIKU

# â”€â”€ API CALLER â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

import urllib.request

def call_claude(prompt: str, model: str, max_tokens: int = 1000) -> str:
    """Call Claude API â€” tight prompts, JSON-only responses where possible."""
    payload = json.dumps({
        "model": model,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}]
    }).encode()

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            return data["content"][0]["text"].strip()
    except Exception as e:
        return f"[API_ERROR: {e}]"

# â”€â”€ PROMPT BUILDERS (tight = fewer tokens) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def prompt_rewrite_body(text: str) -> str:
    return (
        "Rewrite for web manual. Plain English, concise, active voice. "
        "Keep all technical terms exact. Max 2 sentences.\n\n"
        f"TEXT: {text}\n\nOUTPUT (rewritten text only):"
    )

def prompt_spec_summary(headers: list, rows: list) -> str:
    table_str = " | ".join(headers) + "\n"
    for r in rows[:6]:  # cap rows sent to AI
        table_str += " | ".join(str(c) for c in r) + "\n"
    return (
        "Write a 1-sentence plain-English summary of this spec table for a web manual intro.\n\n"
        f"TABLE:\n{table_str}\nOUTPUT (1 sentence only):"
    )

def prompt_troubleshoot(headers: list, rows: list) -> str:
    table_str = " | ".join(headers) + "\n"
    for r in rows:
        table_str += " | ".join(str(c) for c in r) + "\n"
    return (
        "Convert this troubleshooting table to JSON. "
        "Return ONLY valid JSON, no markdown, no explanation.\n"
        "Schema: [{\"symptom\":str, \"causes\":[{\"cause\":str,\"fix\":str}]}]\n"
        "Group rows with same symptom together.\n\n"
        f"TABLE:\n{table_str}\n\nJSON:"
    )

def prompt_maintenance_enrich(headers: list, rows: list) -> str:
    table_str = " | ".join(headers) + "\n"
    for r in rows:
        table_str += " | ".join(str(c) for c in r) + "\n"
    return (
        "Add two fields to each maintenance row: "
        "priority (high/medium/low) and est_minutes (integer).\n"
        "Return ONLY valid JSON array. No markdown.\n"
        "Schema: [{\"interval\":str,\"task\":str,\"reference\":str,"
        "\"priority\":str,\"est_minutes\":int}]\n\n"
        f"TABLE:\n{table_str}\n\nJSON:"
    )

def prompt_checklist_enrich(headers: list, rows: list) -> str:
    table_str = " | ".join(headers) + "\n"
    for r in rows:
        table_str += " | ".join(str(c) for c in r) + "\n"
    return (
        "Convert checklist table to JSON for interactive web checklist.\n"
        "Return ONLY valid JSON array. No markdown.\n"
        "Schema: [{\"number\":str,\"item\":str,\"expected\":str,\"critical\":bool}]\n"
        "Set critical=true if failure would cause safety risk or machine damage.\n\n"
        f"TABLE:\n{table_str}\n\nJSON:"
    )

def prompt_batch_body(blocks: list) -> str:
    """Batch multiple body blocks into one call â€” saves API overhead."""
    items = "\n".join(f"[{i}] {b['text']}" for i, b in enumerate(blocks))
    return (
        "Rewrite each numbered text for a web manual. "
        "Plain English, concise, active voice. Keep technical terms exact.\n"
        "Return ONLY a JSON array of rewritten strings in same order. No markdown.\n\n"
        f"TEXTS:\n{items}\n\nJSON array:"
    )

# â”€â”€ ENRICHMENT WORKERS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def enrich_body_blocks(blocks: list, cache: dict) -> tuple:
    """Batch body blocks â†’ single API call. Returns (enriched_blocks, tokens_used)."""
    to_process = []
    cached_results = {}

    for i, b in enumerate(blocks):
        if not b.get("ai_needed"):
            continue
        h = make_hash(b["text"])
        if h in cache:
            cached_results[i] = cache[h]
        else:
            to_process.append((i, b, h))

    tokens_used = 0
    if to_process:
        # BATCH: send all pending blocks in one call
        batch_blocks = [b for _, b, _ in to_process]
        model = MODEL_HAIKU
        prompt = prompt_batch_body(batch_blocks)
        tokens_used = len(prompt.split()) * 2  # rough estimate

        raw = call_claude(prompt, model, max_tokens=800)
        try:
            clean = re.sub(r'```json|```', '', raw).strip()
            rewrites = json.loads(clean)
            for j, (i, b, h) in enumerate(to_process):
                rewritten = rewrites[j] if j < len(rewrites) else b["text"]
                cached_results[i] = rewritten
                cache[h] = rewritten
        except Exception:
            for i, b, h in to_process:
                cached_results[i] = b["text"]  # fallback to original

    # Apply results
    enriched = []
    for i, b in enumerate(blocks):
        eb = dict(b)
        if i in cached_results:
            eb["text_enriched"] = cached_results[i]
            eb["enriched"] = True
        enriched.append(eb)

    return enriched, tokens_used


def enrich_table(table: dict, cache: dict) -> tuple:
    """Enrich a typed table. Returns (enriched_table, tokens_used, model_used)."""
    tt = table.get("table_type", "generic_table")
    h = make_hash(tt + str(table["headers"]) + str(table["rows"][:3]))

    if h in cache:
        return {**table, **cache[h], "cache_hit": True}, 0, "cache"

    tokens_used = 0
    model_used = MODEL_HAIKU
    enriched_data = {}

    if tt == "spec_table":
        prompt = prompt_spec_summary(table["headers"], table["rows"])
        model_used = MODEL_HAIKU
        tokens_used = len(prompt.split()) * 2
        summary = call_claude(prompt, model_used, max_tokens=100)
        enriched_data = {"summary_sentence": summary}

    elif tt == "troubleshoot_table":
        prompt = prompt_troubleshoot(table["headers"], table["rows"])
        model_used = MODEL_SONNET
        tokens_used = len(prompt.split()) * 2
        raw = call_claude(prompt, model_used, max_tokens=1000)
        try:
            clean = re.sub(r'```json|```', '', raw).strip()
            enriched_data = {"decision_tree": json.loads(clean)}
        except Exception:
            enriched_data = {"decision_tree": [], "parse_error": True}

    elif tt == "maintenance_table":
        prompt = prompt_maintenance_enrich(table["headers"], table["rows"])
        model_used = MODEL_HAIKU
        tokens_used = len(prompt.split()) * 2
        raw = call_claude(prompt, model_used, max_tokens=800)
        try:
            clean = re.sub(r'```json|```', '', raw).strip()
            enriched_data = {"enriched_rows": json.loads(clean)}
        except Exception:
            enriched_data = {"enriched_rows": []}

    elif tt == "checklist_table":
        prompt = prompt_checklist_enrich(table["headers"], table["rows"])
        model_used = MODEL_HAIKU
        tokens_used = len(prompt.split()) * 2
        raw = call_claude(prompt, model_used, max_tokens=600)
        try:
            clean = re.sub(r'```json|```', '', raw).strip()
            enriched_data = {"checklist_items": json.loads(clean)}
        except Exception:
            enriched_data = {"checklist_items": []}

    cache[h] = enriched_data
    return {**table, **enriched_data}, tokens_used, model_used


# â”€â”€ MAIN AGENT â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def run_enrichment_agent(input_path: str) -> dict:
    print(f"\n{'='*60}")
    print("  Phase 3: Content Enrichment Agent")
    print(f"{'='*60}")

    with open(input_path) as f:
        tree = json.load(f)

    cache = load_cache()

    stats = {
        "sections_processed": 0,
        "sections_skipped":   0,
        "tables_enriched":    0,
        "body_blocks_enriched": 0,
        "api_calls":          0,
        "cache_hits":         0,
        "tokens_estimated":   0,
        "models_used":        {"haiku": 0, "sonnet": 0},
    }

    enriched_tree = {**tree, "chapters": []}

    for ch in tree["chapters"]:
        enriched_ch = {**ch, "sections": []}

        for sec in ch["sections"]:

            # â”€â”€ SKIP rule-based sections entirely â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            if not sec.get("ai_needed", False):
                enriched_ch["sections"].append({**sec, "enriched": False})
                stats["sections_skipped"] += 1
                print(f"  SKIP  {sec['id']:<15} {sec['title'][:45]}")
                continue

            print(f"  ENRICH {sec['id']:<14} {sec['title'][:45]}")
            enriched_sec = {**sec, "enriched": True, "content": {**sec["content"]}}

            # â”€â”€ Enrich body blocks (batched) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            body_blocks = sec["content"].get("body", [])
            if body_blocks:
                enriched_body, tok = enrich_body_blocks(body_blocks, cache)
                enriched_sec["content"]["body"] = enriched_body
                enriched_count = sum(1 for b in enriched_body if b.get("enriched"))
                stats["body_blocks_enriched"] += enriched_count
                stats["tokens_estimated"]     += tok
                if tok > 0:
                    stats["api_calls"] += 1
                    stats["models_used"]["haiku"] += 1
                    print(f"    â†³ body batch: {enriched_count} blocks â†’ Haiku (~{tok} tokens)")
                elif enriched_count > 0:
                    stats["cache_hits"] += 1
                    print(f"    â†³ body batch: {enriched_count} blocks â†’ CACHE HIT")

            # â”€â”€ Enrich tables â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            enriched_tables = []
            for tbl in sec["content"].get("tables", []):
                etbl, tok, model = enrich_table(tbl, cache)
                enriched_tables.append(etbl)
                stats["tables_enriched"] += 1
                stats["tokens_estimated"] += tok
                model_label = "Sonnet" if model == MODEL_SONNET else ("Haiku" if model == MODEL_HAIKU else "cache")
                if etbl.get("cache_hit"):
                    stats["cache_hits"] += 1
                    print(f"    â†³ table [{tbl['table_type']}] â†’ CACHE HIT")
                elif tok > 0:
                    stats["api_calls"] += 1
                    if "sonnet" in model.lower():
                        stats["models_used"]["sonnet"] += 1
                    else:
                        stats["models_used"]["haiku"] += 1
                    print(f"    â†³ table [{tbl['table_type']}] â†’ {model_label} (~{tok} tokens)")

            enriched_sec["content"]["tables"] = enriched_tables
            enriched_ch["sections"].append(enriched_sec)
            stats["sections_processed"] += 1

        enriched_tree["chapters"].append(enriched_ch)

    save_cache(cache)
    enriched_tree["enrichment_stats"] = stats
    return enriched_tree


# â”€â”€ REPORT â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def print_report(tree: dict) -> str:
    s = tree["enrichment_stats"]
    lines = []
    lines.append("=" * 60)
    lines.append("  PHASE 3 ENRICHMENT REPORT")
    lines.append("=" * 60)
    lines.append(f"\n  Sections enriched      : {s['sections_processed']}")
    lines.append(f"  Sections skipped (free): {s['sections_skipped']}")
    lines.append(f"  Tables enriched        : {s['tables_enriched']}")
    lines.append(f"  Body blocks enriched   : {s['body_blocks_enriched']}")
    lines.append(f"\n  --- Token Usage ---")
    lines.append(f"  API calls made         : {s['api_calls']}")
    lines.append(f"  Cache hits             : {s['cache_hits']}")
    lines.append(f"  Est. tokens used       : {s['tokens_estimated']:,}")
    lines.append(f"  Haiku calls            : {s['models_used']['haiku']}")
    lines.append(f"  Sonnet calls           : {s['models_used']['sonnet']}")

    lines.append(f"\n  --- Enrichment Samples ---")
    for ch in tree["chapters"]:
        for sec in ch["sections"]:
            if not sec.get("enriched"):
                continue
            lines.append(f"\n  [{sec['section_type']}] {sec['title']}")

            # Show body rewrite sample
            for b in sec["content"].get("body", []):
                if b.get("enriched"):
                    lines.append(f"    BEFORE: {b['text'][:80]}")
                    lines.append(f"    AFTER : {b.get('text_enriched','')[:80]}")
                    break

            # Show table enrichment sample
            for tbl in sec["content"].get("tables", []):
                tt = tbl.get("table_type")
                if tt == "troubleshoot_table" and tbl.get("decision_tree"):
                    dt = tbl["decision_tree"]
                    if dt:
                        lines.append(f"    DECISION TREE SAMPLE:")
                        entry = dt[0]
                        lines.append(f"      Symptom : {entry.get('symptom','')[:60]}")
                        for cause in entry.get("causes", [])[:2]:
                            lines.append(f"      Cause   : {cause.get('cause','')[:55]}")
                            lines.append(f"      Fix     : {cause.get('fix','')[:55]}")
                elif tt == "checklist_table" and tbl.get("checklist_items"):
                    lines.append(f"    CHECKLIST SAMPLE:")
                    for item in tbl["checklist_items"][:2]:
                        crit = "âš  CRITICAL" if item.get("critical") else ""
                        lines.append(f"      [{item.get('number','')}] {item.get('item','')[:50]} {crit}")
                elif tt == "maintenance_table" and tbl.get("enriched_rows"):
                    lines.append(f"    MAINTENANCE SAMPLE:")
                    for row in tbl["enriched_rows"][:2]:
                        lines.append(f"      [{row.get('interval','')}] {row.get('task','')[:40]} "
                                     f"| priority={row.get('priority','')} "
                                     f"| ~{row.get('est_minutes','')} min")
                elif tt == "spec_table" and tbl.get("summary_sentence"):
                    lines.append(f"    SPEC SUMMARY: {tbl['summary_sentence'][:100]}")

    lines.append("\n" + "=" * 60)
    lines.append("  Phase 3 Complete â€” enriched_tree.json ready for Phase 4")
    lines.append("=" * 60)
    return "\n".join(lines)


# â”€â”€ RUN â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
if __name__ == "__main__":
    enriched = run_enrichment_agent(INPUT_JSON)

    with open(OUTPUT_JSON, "w") as f:
        json.dump(enriched, f, indent=2, ensure_ascii=False)
    print(f"\n  Saved: {OUTPUT_JSON}")

    report = print_report(enriched)
    print(report)
    with open(OUTPUT_REPORT, "w") as f:
        f.write(report)
    print(f"  Saved: {OUTPUT_REPORT}")

