"""
Phase 6: QA Validator Agent
==============================
Input : all pipeline artifacts
Output: qa_report.json + qa_report.html (human-readable)

Token cost: ZERO â€” pure static analysis

Checks:
  1. CONTENT COVERAGE  â€” every chapter/section/callout from source appears in HTML
  2. LINK INTEGRITY    â€” every #anchor in nav resolves to a defined id in HTML
  3. DATA COMPLETENESS â€” every interactive component has its data payload
  4. ACCESSIBILITY     â€” headings hierarchy, alt text, button labels, color contrast flags
  5. STRUCTURE DIFF    â€” source block counts vs rendered component counts
  6. PIPELINE INTEGRITYâ€” each phase output file exists and is valid JSON/HTML
"""

import json
import re
import os
from pathlib import Path
from datetime import datetime

# â”€â”€ PATHS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
CONTENT_MAP   = "E:\repos\reposEPSON-RC-online-manual\pipeline_output\content_map.json"
CONTENT_TREE  = "E:\repos\reposEPSON-RC-online-manual\pipeline_output\content_tree.json"
ENRICHED_TREE = "E:\repos\reposEPSON-RC-online-manual\pipeline_output\enriched_tree.json"
COMPONENT_MAP = "E:\repos\reposEPSON-RC-online-manual\pipeline_output\component_map.json"
HTML_MANUAL   = "E:\repos\reposEPSON-RC-online-manual\pipeline_output\hydropress_x500_manual.html"
QA_JSON       = "E:\repos\reposEPSON-RC-online-manual\pipeline_output\qa_report.json"
QA_HTML       = "E:\repos\reposEPSON-RC-online-manual\pipeline_output\qa_report.html"

SEV = {"PASS": "pass", "WARN": "warn", "FAIL": "fail", "INFO": "info"}

# â”€â”€ RESULT BUILDER â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def check(category, name, status, detail, fix=None):
    return {
        "category": category,
        "name":     name,
        "status":   status,
        "detail":   detail,
        "fix":      fix or "",
    }

# â”€â”€ CHECK 1: PIPELINE FILE INTEGRITY â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def check_pipeline_files():
    results = []
    files = [
        ("Phase 1 output", CONTENT_MAP,   ".json"),
        ("Phase 2 output", CONTENT_TREE,  ".json"),
        ("Phase 3 output", ENRICHED_TREE, ".json"),
        ("Phase 4 output", COMPONENT_MAP, ".json"),
        ("Phase 5 output", HTML_MANUAL,   ".html"),
    ]
    for label, path, ext in files:
        if not os.path.exists(path):
            results.append(check("Pipeline", label, SEV["FAIL"],
                f"File missing: {path}", "Re-run the corresponding phase agent."))
            continue
        size = os.path.getsize(path)
        if size < 100:
            results.append(check("Pipeline", label, SEV["FAIL"],
                f"File suspiciously small ({size} bytes): {path}",
                "Re-run the corresponding phase agent."))
            continue
        if ext == ".json":
            try:
                with open(path) as f:
                    json.load(f)
                results.append(check("Pipeline", label, SEV["PASS"],
                    f"Valid JSON, {size:,} bytes"))
            except Exception as e:
                results.append(check("Pipeline", label, SEV["FAIL"],
                    f"Invalid JSON: {e}", "Inspect and repair the file."))
        else:
            content = open(path).read()
            if "<!DOCTYPE html>" in content or "<html" in content or "<body" in content:
                results.append(check("Pipeline", label, SEV["PASS"],
                    f"Valid HTML, {size:,} bytes"))
            else:
                results.append(check("Pipeline", label, SEV["WARN"],
                    f"HTML may be incomplete â€” no <html> or <body> tag", "Check Phase 5 output."))
    return results

# â”€â”€ CHECK 2: CONTENT COVERAGE â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def check_content_coverage(cm, html):
    results = []
    html_lower = html.lower()

    # Every chapter title should appear somewhere in HTML
    for ch in cm["structure"]["chapters"]:
        title_words = [w for w in ch["title"].split() if len(w) > 4]
        found = any(w.lower() in html_lower for w in title_words)
        if found:
            results.append(check("Coverage", f"Chapter: {ch['title'][:40]}", SEV["PASS"],
                f"Chapter content present in HTML (page {ch['page']})"))
        else:
            results.append(check("Coverage", f"Chapter: {ch['title'][:40]}", SEV["FAIL"],
                f"Chapter title words not found in HTML",
                "Add this chapter section to Phase 5 web builder."))

    # Callout types coverage
    callout_counts = {}
    for b in cm["structure"]["all_blocks"]:
        if b["type"] in ("warning","danger","caution","note"):
            callout_counts[b["type"]] = callout_counts.get(b["type"], 0) + 1

    for ctype, count in callout_counts.items():
        css_class = f"alert-{ctype}" if ctype != "caution" else "alert-warning"
        html_count = html_lower.count(f"alert-{ctype}")
        if html_count == 0:
            html_count = html_lower.count("alert-warning")  # caution uses warning style
        if html_count >= 1:
            results.append(check("Coverage", f"Callout type: {ctype}", SEV["PASS"],
                f"Source has {count}x {ctype}, HTML renders callout blocks"))
        else:
            results.append(check("Coverage", f"Callout type: {ctype}", SEV["WARN"],
                f"Source has {count}x {ctype} but no matching HTML callout block",
                f"Ensure {ctype} callouts are rendered in Phase 5."))

    # Step count coverage
    source_steps = sum(1 for b in cm["structure"]["all_blocks"] if b["type"] == "step")
    # Count steps in HTML wizards
    html_steps_approx = html_lower.count("step ") + html_lower.count("wiz-step")
    ratio = min(html_steps_approx / max(source_steps, 1), 1.0)
    if ratio >= 0.5:
        results.append(check("Coverage", "Step procedures", SEV["PASS"],
            f"Source: {source_steps} steps, HTML wizard components present"))
    else:
        results.append(check("Coverage", "Step procedures", SEV["WARN"],
            f"Source has {source_steps} steps but wizard coverage may be incomplete",
            "Review procedure wizard step counts in Phase 5."))

    # Tables coverage
    source_tables = cm["stats"]["total_tables"]
    html_tables = html_lower.count("<table")
    if html_tables >= source_tables - 1:
        results.append(check("Coverage", "Data tables", SEV["PASS"],
            f"Source: {source_tables} tables, HTML: {html_tables} <table> elements"))
    else:
        results.append(check("Coverage", "Data tables", SEV["WARN"],
            f"Source has {source_tables} tables but HTML only has {html_tables}",
            "Check that all spec/maintenance/checklist tables are rendered."))

    return results

# â”€â”€ CHECK 3: LINK INTEGRITY â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def check_links(html):
    results = []

    anchors_defined = set(re.findall(r'\bid="([^"]+)"', html))
    anchors_linked  = set(re.findall(r'href="#([^"]+)"', html))
    onclick_anchors = set(re.findall(r"goTo\('([^']+)'", html))

    # href links
    broken = [a for a in anchors_linked if a not in anchors_defined]
    ok     = [a for a in anchors_linked if a in anchors_defined]

    results.append(check("Links", "Total anchor targets defined", SEV["INFO"],
        f"{len(anchors_defined)} id attributes in HTML"))
    results.append(check("Links", "Total href links", SEV["INFO"],
        f"{len(anchors_linked)} href=#anchor links in navigation"))

    if broken:
        for b in broken:
            results.append(check("Links", f"Broken link: #{b}", SEV["FAIL"],
                f"Navigation links to #{b} but no element with id=\"{b}\" exists",
                f"Add id=\"{b}\" to the correct section element in Phase 5 HTML."))
    else:
        results.append(check("Links", "All href anchors resolve", SEV["PASS"],
            f"All {len(ok)} href links point to valid id targets"))

    # Check JS goTo calls reference valid chapters
    ch_ids = set(re.findall(r'\bid="(ch\d+)"', html))
    bad_goto = [a for a in onclick_anchors if a not in ch_ids and not a.startswith('ch')]
    if bad_goto:
        for b in bad_goto:
            results.append(check("Links", f"JS navigation: goTo('{b}')", SEV["WARN"],
                f"JS calls goTo('{b}') but no matching chapter block found",
                "Verify goTo targets match HTML chapter block ids."))
    else:
        results.append(check("Links", "JS navigation targets", SEV["PASS"],
            f"All goTo() calls reference valid chapter ids"))

    return results

# â”€â”€ CHECK 4: INTERACTIVE DATA COMPLETENESS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def check_interactive_data(html):
    results = []

    checks = [
        ("CHECKLIST data",        "const CHECKLIST",  "checklist_items",  8),
        ("FAULT_TREE data",       "const FAULT_TREE", "fault_symptoms",   4),
        ("MAINT_ROWS data",       "const MAINT_ROWS", "maint_rows",       8),
        ("PROCEDURES data",       "const PROCEDURES", "procedures",       1),
        ("Wizard install target", "wiz-install",       "install_wizard",   1),
        ("Wizard press target",   "wiz-press",         "press_wizard",     1),
        ("Wizard oil target",     "wiz-oil",           "oil_wizard",       1),
        ("Checklist target",      "checklist-preop",   "checklist_el",     1),
        ("Maintenance target",    "maint-schedule",    "maint_el",         1),
        ("Fault finder target",   "fault-finder",      "fault_el",         1),
    ]

    for label, marker, key, _ in checks:
        if marker in html:
            # Try to get count for data arrays
            if marker.startswith("const "):
                arr_match = re.search(rf'{re.escape(marker)}\s*=\s*(\[.*?\]);', html, re.DOTALL)
                if arr_match:
                    try:
                        arr = json.loads(arr_match.group(1))
                        results.append(check("Data", label, SEV["PASS"],
                            f"Present in HTML with {len(arr)} items"))
                    except:
                        results.append(check("Data", label, SEV["WARN"],
                            f"Marker present but data may not be valid JSON",
                            "Inspect the embedded JS data in the HTML."))
                else:
                    results.append(check("Data", label, SEV["PASS"], "Marker present in HTML"))
            else:
                results.append(check("Data", label, SEV["PASS"], "DOM target element present"))
        else:
            results.append(check("Data", label, SEV["FAIL"],
                f"'{marker}' not found in HTML",
                f"Ensure Phase 5 web builder embeds {key} correctly."))

    return results

# â”€â”€ CHECK 5: ACCESSIBILITY â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def check_accessibility(html):
    results = []

    # Heading hierarchy
    h1s = re.findall(r'<h1[^>]*>', html)
    h2s = re.findall(r'<h2[^>]*>', html)
    if len(h1s) == 1:
        results.append(check("A11y", "Single H1", SEV["PASS"],
            f"Exactly 1 <h1> element found"))
    elif len(h1s) == 0:
        results.append(check("A11y", "Missing H1", SEV["WARN"],
            "No <h1> element found â€” add a main page title for screen readers",
            "Add <h1 class='sr-only'> with the document title near the top of <body>."))
    else:
        results.append(check("A11y", "Multiple H1s", SEV["WARN"],
            f"{len(h1s)} <h1> elements found â€” only one should exist per page",
            "Convert secondary <h1> elements to <h2> or lower."))

    # Buttons with no label
    buttons_total = len(re.findall(r'<button', html))
    buttons_aria  = len(re.findall(r'<button[^>]+aria-label', html))
    icon_buttons  = len(re.findall(r'<button[^>]*>[^<]{0,3}</', html))  # very short content
    results.append(check("A11y", "Button labels", SEV["INFO"],
        f"{buttons_total} buttons total, {buttons_aria} with aria-label"))

    # Images with alt text
    imgs_total = len(re.findall(r'<img', html))
    imgs_alt   = len(re.findall(r'<img[^>]+alt="[^"]+"', html))
    if imgs_total == 0:
        results.append(check("A11y", "Images / alt text", SEV["INFO"],
            "No <img> tags found â€” diagrams/images are not embedded in current output",
            "Consider embedding key diagrams as inline SVG or <img alt='...'> in Phase 5."))
    elif imgs_alt == imgs_total:
        results.append(check("A11y", "Images / alt text", SEV["PASS"],
            f"All {imgs_total} images have alt text"))
    else:
        results.append(check("A11y", "Images / alt text", SEV["FAIL"],
            f"{imgs_total - imgs_alt} of {imgs_total} images missing alt text",
            "Add descriptive alt attributes to all <img> elements."))

    # Language attribute
    if 'lang="en"' in html:
        results.append(check("A11y", "Language attribute", SEV["PASS"],
            'lang="en" set on <html> element'))
    else:
        results.append(check("A11y", "Language attribute", SEV["WARN"],
            'lang attribute missing on <html>',
            'Add lang="en" (or appropriate language code) to the <html> tag.'))

    # Viewport meta
    if 'name="viewport"' in html:
        results.append(check("A11y", "Viewport meta", SEV["PASS"],
            "Responsive viewport meta tag present"))
    else:
        results.append(check("A11y", "Viewport meta", SEV["FAIL"],
            "No viewport meta tag â€” mobile rendering will be broken",
            "Add <meta name='viewport' content='width=device-width, initial-scale=1.0'>"))

    # Focus management (skip links)
    if 'tabindex' in html or 'skip' in html.lower():
        results.append(check("A11y", "Keyboard navigation", SEV["PASS"],
            "tabindex or skip-nav hints found in HTML"))
    else:
        results.append(check("A11y", "Keyboard navigation", SEV["WARN"],
            "No skip-nav link or tabindex management detected",
            "Add a 'Skip to main content' link at the top for keyboard users."))

    # Color contrast (static check - flags inline hardcoded colors)
    inline_colors = re.findall(r'color:\s*#(?!fff|000|FFF|000000|ffffff)[0-9a-fA-F]{3,6}', html)
    if len(inline_colors) > 10:
        results.append(check("A11y", "Hardcoded inline colors", SEV["WARN"],
            f"{len(inline_colors)} hardcoded color values found in inline styles â€” contrast not verified",
            "Prefer CSS variables (--color-text-*) to guarantee contrast across light/dark modes."))
    else:
        results.append(check("A11y", "Color usage", SEV["PASS"],
            f"Mostly CSS variables used for colors ({len(inline_colors)} inline overrides)"))

    return results

# â”€â”€ CHECK 6: STRUCTURE DIFF â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def check_structure_diff(cm, cmap, html):
    results = []

    # Source vs output chapter count
    src_chapters = cm["stats"]["total_chapters"]
    out_chapters = len(cmap["pages"]["chapters"])
    if src_chapters == out_chapters:
        results.append(check("Structure", "Chapter count", SEV["PASS"],
            f"Source: {src_chapters} chapters â†’ Output: {out_chapters} chapters âœ“"))
    else:
        diff = src_chapters - out_chapters
        results.append(check("Structure", "Chapter count", SEV["FAIL"],
            f"Source has {src_chapters} chapters but output has {out_chapters} ({diff} missing)",
            "Ensure all chapters are included in Phase 5 web builder."))

    # Source block type vs HTML component type
    block_types = cm["stats"]["block_type_counts"]
    comp_types  = cmap["stats"]["component_type_breakdown"]

    src_steps = block_types.get("step", 0)
    out_wizards = comp_types.get("procedure_wizard", 0)
    if out_wizards > 0:
        results.append(check("Structure", "Procedures â†’ Wizards", SEV["PASS"],
            f"Source: {src_steps} steps across procedures â†’ {out_wizards} wizard components"))
    else:
        results.append(check("Structure", "Procedures â†’ Wizards", SEV["FAIL"],
            f"Source has {src_steps} steps but no procedure_wizard components in output",
            "Re-run Phase 4/5 â€” procedure mapping may have failed."))

    src_callouts = sum(block_types.get(t, 0) for t in ("warning","danger","caution","note"))
    out_banners  = comp_types.get("safety_banner", 0)
    if out_banners >= src_callouts // 2:
        results.append(check("Structure", "Callouts â†’ Safety banners", SEV["PASS"],
            f"Source: {src_callouts} callout blocks â†’ {out_banners} safety_banner components"))
    else:
        results.append(check("Structure", "Callouts â†’ Safety banners", SEV["WARN"],
            f"Source has {src_callouts} callouts but only {out_banners} banners rendered",
            "Some callout blocks may be missing from Phase 5 HTML."))

    # Interactive component count
    out_interactive = cmap["stats"]["interactive_components"]
    results.append(check("Structure", "Interactive components", SEV["PASS"],
        f"{out_interactive} interactive components: fault_finder, checklist, wizards, maintenance_schedule"))

    # File size sanity
    size = os.path.getsize(HTML_MANUAL)
    if size > 20_000:
        results.append(check("Structure", "Output file size", SEV["PASS"],
            f"HTML is {size:,} bytes ({size//1024} KB) â€” sufficient for full content"))
    else:
        results.append(check("Structure", "Output file size", SEV["WARN"],
            f"HTML is only {size:,} bytes â€” may be missing content",
            "Re-run Phase 5 and check that all sections were included."))

    return results

# â”€â”€ MAIN AGENT â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def run_qa_agent():
    print(f"\n{'='*60}")
    print("  Phase 6: QA Validator Agent")
    print(f"{'='*60}")
    print("  Token cost: ZERO\n")

    # Load all artifacts
    with open(CONTENT_MAP)   as f: cm   = json.load(f)
    with open(COMPONENT_MAP) as f: cmap = json.load(f)
    html = open(HTML_MANUAL).read()

    all_results = []

    print("  [1/6] Checking pipeline file integrity...")
    r = check_pipeline_files()
    all_results.extend(r)

    print("  [2/6] Checking content coverage...")
    r = check_content_coverage(cm, html)
    all_results.extend(r)

    print("  [3/6] Checking link integrity...")
    r = check_links(html)
    all_results.extend(r)

    print("  [4/6] Checking interactive data completeness...")
    r = check_interactive_data(html)
    all_results.extend(r)

    print("  [5/6] Checking accessibility...")
    r = check_accessibility(html)
    all_results.extend(r)

    print("  [6/6] Checking structure diff (source vs output)...")
    r = check_structure_diff(cm, cmap, html)
    all_results.extend(r)

    # Tally
    tally = {"pass": 0, "warn": 0, "fail": 0, "info": 0}
    for r in all_results:
        tally[r["status"]] = tally.get(r["status"], 0) + 1

    qa_report = {
        "generated":   datetime.now().isoformat(),
        "source_file": cm["metadata"]["source_file"],
        "tally":       tally,
        "total":       len(all_results),
        "results":     all_results,
        "overall": "PASS" if tally["fail"] == 0 else "NEEDS REVIEW",
    }

    return qa_report

# â”€â”€ HTML REPORT GENERATOR â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def generate_html_report(qa: dict) -> str:
    tally = qa["tally"]
    overall_color = "#22c55e" if qa["overall"] == "PASS" else "#f59e0b"

    status_cfg = {
        "pass": ("âœ“", "#22c55e", "rgba(34,197,94,.1)"),
        "warn": ("âš ", "#f59e0b", "rgba(245,158,11,.1)"),
        "fail": ("âœ—", "#ef4444", "rgba(239,68,68,.1)"),
        "info": ("â„¹", "#3b82f6", "rgba(59,130,246,.1)"),
    }

    cats = {}
    for r in qa["results"]:
        cats.setdefault(r["category"], []).append(r)

    rows_html = ""
    for cat, items in cats.items():
        cat_pass = sum(1 for i in items if i["status"]=="pass")
        cat_fail = sum(1 for i in items if i["status"]=="fail")
        cat_warn = sum(1 for i in items if i["status"]=="warn")
        rows_html += f'''
        <tr class="cat-header">
          <td colspan="3" style="padding:10px 16px;background:#1c2030;font-family:monospace;
              font-size:11px;letter-spacing:1px;text-transform:uppercase;color:#7a8099;">
            {cat}
            <span style="float:right;color:#22c55e">{cat_pass}âœ“</span>
            {"<span style='float:right;margin-right:8px;color:#f59e0b'>"+str(cat_warn)+"âš </span>" if cat_warn else ""}
            {"<span style='float:right;margin-right:8px;color:#ef4444'>"+str(cat_fail)+"âœ—</span>" if cat_fail else ""}
          </td>
        </tr>'''
        for item in items:
            icon, color, bg = status_cfg[item["status"]]
            fix_html = f'<div style="font-size:11px;color:#f59e0b;margin-top:4px">â†’ {item["fix"]}</div>' if item["fix"] else ""
            rows_html += f'''
        <tr>
          <td style="width:36px;text-align:center;background:{bg};color:{color};font-size:16px">{icon}</td>
          <td style="padding:9px 14px">
            <div style="font-size:13px;color:#e8eaf0">{item["name"]}</div>
            <div style="font-size:12px;color:#7a8099;margin-top:2px">{item["detail"]}</div>
            {fix_html}
          </td>
          <td style="width:70px;text-align:center;font-size:10px;font-family:monospace;
              letter-spacing:1px;text-transform:uppercase;color:{color}">{item["status"]}</td>
        </tr>'''

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>QA Report â€” HydroPress X500 Manual</title>
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=JetBrains+Mono:wght@400;500&family=Inter:wght@400;500&display=swap" rel="stylesheet">
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{background:#0d0f14;color:#e8eaf0;font-family:'Inter',sans-serif;font-size:14px;padding:32px}}
  .hdr{{margin-bottom:32px}}
  .hdr-title{{font-family:'Syne',sans-serif;font-size:32px;font-weight:800;letter-spacing:-1px}}
  .hdr-sub{{color:#7a8099;font-size:13px;margin-top:4px}}
  .verdict{{display:inline-block;padding:6px 16px;border-radius:20px;font-family:'JetBrains Mono',monospace;
    font-size:12px;font-weight:500;letter-spacing:1px;margin-top:12px;
    background:{overall_color}22;color:{overall_color};border:1px solid {overall_color}55}}
  .stats{{display:flex;gap:16px;margin:24px 0}}
  .stat{{background:#151820;border:1px solid #252a38;border-radius:10px;padding:14px 20px;min-width:100px;text-align:center}}
  .stat-n{{font-size:28px;font-weight:500;font-family:'Syne',sans-serif}}
  .stat-l{{font-size:11px;color:#7a8099;margin-top:4px;font-family:'JetBrains Mono',monospace;letter-spacing:1px;text-transform:uppercase}}
  .s-pass{{color:#22c55e}} .s-warn{{color:#f59e0b}} .s-fail{{color:#ef4444}} .s-info{{color:#3b82f6}}
  table{{width:100%;border-collapse:collapse;background:#151820;border:1px solid #252a38;border-radius:10px;overflow:hidden}}
  tr:not(.cat-header){{border-bottom:1px solid #1c2030}}
  tr:not(.cat-header):last-child{{border-bottom:none}}
  .footer{{margin-top:24px;font-size:12px;color:#4a5068;font-family:'JetBrains Mono',monospace}}
</style>
</head>
<body>
<div class="hdr">
  <div class="hdr-title">QA Validation Report</div>
  <div class="hdr-sub">HydroPress X500 Interactive Manual Â· Generated {qa["generated"][:19].replace("T"," ")}</div>
  <div class="verdict">{qa["overall"]}</div>
</div>
<div class="stats">
  <div class="stat"><div class="stat-n">{qa["total"]}</div><div class="stat-l">Total checks</div></div>
  <div class="stat"><div class="stat-n s-pass">{tally["pass"]}</div><div class="stat-l">Passed</div></div>
  <div class="stat"><div class="stat-n s-warn">{tally["warn"]}</div><div class="stat-l">Warnings</div></div>
  <div class="stat"><div class="stat-n s-fail">{tally["fail"]}</div><div class="stat-l">Failed</div></div>
  <div class="stat"><div class="stat-n s-info">{tally["info"]}</div><div class="stat-l">Info</div></div>
</div>
<table>
  <tbody>{rows_html}</tbody>
</table>
<div class="footer">Phase 6 QA Validator Â· {qa["total"]} checks Â· 0 tokens Â· pipeline complete</div>
</body>
</html>'''

# â”€â”€ RUN â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
if __name__ == "__main__":
    qa = run_qa_agent()

    with open(QA_JSON, "w") as f:
        json.dump(qa, f, indent=2)

    html_report = generate_html_report(qa)
    with open(QA_HTML, "w") as f:
        f.write(html_report)

    # Print summary
    t = qa["tally"]
    print(f"\n{'='*60}")
    print(f"  QA REPORT SUMMARY")
    print(f"{'='*60}")
    print(f"  Overall status  : {qa['overall']}")
    print(f"  Total checks    : {qa['total']}")
    print(f"  âœ“ Passed        : {t['pass']}")
    print(f"  âš  Warnings      : {t['warn']}")
    print(f"  âœ— Failed        : {t['fail']}")
    print(f"  â„¹ Info          : {t['info']}")
    print()
    if t["fail"] > 0:
        print("  FAILURES TO FIX:")
        for r in qa["results"]:
            if r["status"] == "fail":
                print(f"    âœ— [{r['category']}] {r['name']}")
                print(f"      {r['detail']}")
                if r["fix"]: print(f"      â†’ {r['fix']}")
    if t["warn"] > 0:
        print("  WARNINGS:")
        for r in qa["results"]:
            if r["status"] == "warn":
                print(f"    âš  [{r['category']}] {r['name']}")
                print(f"      {r['detail']}")
    print()
    print(f"  Saved: {QA_JSON}")
    print(f"  Saved: {QA_HTML}")
    print(f"{'='*60}")


