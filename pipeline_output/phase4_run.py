"""
Phase 4: Interactivity Builder Agent
=======================================
Input : enriched_tree.json  (from Phase 3)
Output: component_map.json  (UI blueprint for Phase 5)

Token cost: ZERO â€” pure rule-based mapping.

What it does:
  - Assigns a UI component type to every content node
  - Defines props/config each component needs
  - Builds the full page navigation structure
  - Flags any component needing client-side interactivity

Component catalogue:
  cover_hero          â†’ title, subtitle, model badge, doc info
  toc_nav             â†’ auto-generated sidebar + in-page nav
  safety_banner       â†’ colour-coded danger/warning/caution/note
  spec_table          â†’ sortable table + plain-English summary
  procedure_wizard    â†’ step-by-step with Next/Back + progress bar
  interactive_checklist â†’ tappable checklist with pass/fail + reset
  maintenance_schedule  â†’ filterable by interval, sortable by priority
  fault_finder          â†’ symptom search â†’ decision tree
  generic_table         â†’ plain responsive table
  body_section          â†’ richtext prose block
"""

import json
from pathlib import Path

INPUT_JSON = r"E:\repos\reposEPSON-RC-online-manual\pipeline_output\enriched_tree.json"
OUTPUT_JSON = r"E:\repos\reposEPSON-RC-online-manual\pipeline_output\component_map.json"
OUTPUT_REPORT = r"E:\repos\reposEPSON-RC-online-manual\pipeline_output\phase4_report.txt"

# â”€â”€ COMPONENT DEFINITIONS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

COMPONENT_REGISTRY = {
    "cover_hero": {
        "description": "Full-width cover with title, model number, revision badge",
        "interactive": False,
        "css_class": "comp-cover-hero",
    },
    "toc_nav": {
        "description": "Sticky sidebar navigation auto-built from chapter/section tree",
        "interactive": True,
        "css_class": "comp-toc-nav",
    },
    "safety_banner": {
        "description": "Colour-coded alert block (red=danger, amber=warning, blue=note)",
        "interactive": False,
        "css_class": "comp-safety-banner",
    },
    "spec_table": {
        "description": "Two-column responsive spec table with summary sentence header",
        "interactive": False,
        "css_class": "comp-spec-table",
    },
    "procedure_wizard": {
        "description": "Numbered step-by-step wizard with Next/Back and progress bar",
        "interactive": True,
        "css_class": "comp-procedure-wizard",
    },
    "interactive_checklist": {
        "description": "Tappable checklist with pass/fail toggle, critical highlights, reset",
        "interactive": True,
        "css_class": "comp-interactive-checklist",
    },
    "maintenance_schedule": {
        "description": "Filterable maintenance table by interval and priority, with time estimates",
        "interactive": True,
        "css_class": "comp-maintenance-schedule",
    },
    "fault_finder": {
        "description": "Symptom search box â†’ expandable cause/fix decision tree",
        "interactive": True,
        "css_class": "comp-fault-finder",
    },
    "generic_table": {
        "description": "Plain responsive table for reference data",
        "interactive": False,
        "css_class": "comp-generic-table",
    },
    "body_section": {
        "description": "Prose block with optional collapsible toggle",
        "interactive": False,
        "css_class": "comp-body-section",
    },
    "chapter_header": {
        "description": "Chapter title with icon and type badge",
        "interactive": False,
        "css_class": "comp-chapter-header",
    },
}

# Chapter type â†’ icon mapping
CHAPTER_ICONS = {
    "safety_section":       "shield-alert",
    "spec_section":         "clipboard-list",
    "install_section":      "wrench",
    "operation_section":    "play-circle",
    "maintenance_section":  "calendar-check",
    "troubleshoot_section": "search",
    "general_section":      "file-text",
}

# Callout type â†’ visual variant
CALLOUT_VARIANTS = {
    "danger":  {"color": "red",    "icon": "alert-octagon",  "label": "DANGER"},
    "warning": {"color": "amber",  "icon": "alert-triangle", "label": "WARNING"},
    "caution": {"color": "orange", "icon": "alert-circle",   "label": "CAUTION"},
    "note":    {"color": "blue",   "icon": "info",           "label": "NOTE"},
}

# â”€â”€ COMPONENT MAPPERS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def map_callout(callout: dict) -> dict:
    variant = CALLOUT_VARIANTS.get(callout["type"], CALLOUT_VARIANTS["note"])
    return {
        "component": "safety_banner",
        "props": {
            "variant":  callout["type"],
            "color":    variant["color"],
            "icon":     variant["icon"],
            "label":    variant["label"],
            "text":     callout["text"],
        },
        "interactive": False,
    }


def map_table(table: dict) -> dict:
    tt = table.get("table_type", "generic_table")

    if tt == "spec_table":
        return {
            "component": "spec_table",
            "props": {
                "summary":  table.get("summary_sentence", ""),
                "headers":  table["headers"],
                "rows":     table["rows"],
            },
            "interactive": False,
        }

    if tt == "troubleshoot_table":
        return {
            "component": "fault_finder",
            "props": {
                "decision_tree":    table.get("decision_tree", []),
                "search_placeholder": "Describe the problem (e.g. 'ram not moving')...",
                "symptom_count":    len(table.get("decision_tree", [])),
            },
            "interactive": True,
        }

    if tt in ("checklist_table",):
        return {
            "component": "interactive_checklist",
            "props": {
                "checklist_items": table.get("checklist_items", []),
                "title":  "Pre-Operation Checklist",
                "show_reset_button": True,
                "show_progress_bar": True,
                "critical_count": sum(
                    1 for i in table.get("checklist_items", []) if i.get("critical")
                ),
            },
            "interactive": True,
        }

    if tt == "maintenance_table":
        rows = table.get("enriched_rows", table.get("rows", []))
        intervals = sorted(set(
            r.get("interval", r[0] if isinstance(r, list) else "")
            for r in rows
        ))
        return {
            "component": "maintenance_schedule",
            "props": {
                "rows":              rows,
                "filter_options":    intervals,
                "default_filter":    "All",
                "sortable_columns":  ["interval", "priority", "est_minutes"],
                "show_time_estimates": True,
            },
            "interactive": True,
        }

    # fallback
    return {
        "component": "generic_table",
        "props": {
            "headers": table.get("headers", []),
            "rows":    table.get("rows", []),
        },
        "interactive": False,
    }


def map_procedure(procedure: dict, section_title: str) -> dict:
    steps = procedure.get("steps", [])
    return {
        "component": "procedure_wizard",
        "props": {
            "title":        section_title,
            "steps":        steps,
            "step_count":   len(steps),
            "show_progress":  True,
            "show_print_btn": True,
            "allow_step_check": True,
        },
        "interactive": True,
    }


def map_body_blocks(body_blocks: list) -> list:
    """Merge consecutive body blocks into prose sections."""
    components = []
    buffer = []
    for b in body_blocks:
        text = b.get("text_enriched") or b.get("text", "")
        if text.strip():
            buffer.append(text)
    if buffer:
        components.append({
            "component": "body_section",
            "props": {
                "paragraphs":  buffer,
                "collapsible": len(buffer) > 3,
            },
            "interactive": False,
        })
    return components


def map_section(sec: dict) -> dict:
    """Convert one enriched section into an ordered list of component nodes."""
    components = []
    content = sec.get("content", {})

    # 1. Callouts first (safety first!)
    for callout in content.get("callouts", []):
        components.append(map_callout(callout))

    # 2. Body prose
    body_comps = map_body_blocks(content.get("body", []))
    components.extend(body_comps)

    # 3. Tables (each typed independently)
    for tbl in content.get("tables", []):
        components.append(map_table(tbl))

    # 4. Procedures (step wizards)
    for proc in content.get("procedures", []):
        if proc.get("steps"):
            components.append(map_procedure(proc, sec.get("title", "Procedure")))

    return {
        "id":           sec["id"],
        "title":        sec["title"],
        "section_type": sec.get("section_type", "general_section"),
        "anchor":       sec["id"],
        "components":   components,
        "interactive_count": sum(1 for c in components if c.get("interactive")),
        "component_count":   len(components),
    }


# â”€â”€ NAVIGATION BUILDER â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def build_navigation(chapters: list) -> dict:
    nav = {"chapters": []}
    for ch in chapters:
        ch_nav = {
            "id":    ch["id"],
            "title": ch["title"],
            "icon":  CHAPTER_ICONS.get(ch.get("chapter_type", ""), "file-text"),
            "anchor": ch["id"],
            "sections": []
        }
        for sec in ch.get("sections", []):
            ch_nav["sections"].append({
                "id":     sec["id"],
                "title":  sec["title"],
                "anchor": sec["id"],
                "has_interactive": sec.get("interactive_count", 0) > 0,
            })
        nav["chapters"].append(ch_nav)
    return nav


# â”€â”€ MAIN AGENT â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def run_interactivity_agent(input_path: str) -> dict:
    print(f"\n{'='*60}")
    print("  Phase 4: Interactivity Builder Agent")
    print(f"{'='*60}")
    print("  Token cost: ZERO (pure rule-based mapping)\n")

    with open(input_path) as f:
        tree = json.load(f)

    component_map = {
        "metadata":   tree["metadata"],
        "navigation": {},
        "pages": {
            "cover": None,
            "chapters": []
        },
        "component_registry": COMPONENT_REGISTRY,
        "stats": {}
    }

    # Cover page
    component_map["pages"]["cover"] = {
        "type": "cover",
        "components": [{
            "component": "cover_hero",
            "props": {
                "title":    "HydroPress X500",
                "subtitle": "Industrial Hydraulic Press",
                "model":    "HPX-500",
                "revision": "Rev 3.2",
                "date":     "2024-01",
                "badges":   ["User Manual", "Service Manual"],
            },
            "interactive": False,
        }]
    }

    total_components  = 1  # cover
    total_interactive = 0
    comp_type_counts  = {}

    # Map each chapter
    for ch in tree["chapters"]:
        ch_page = {
            "id":           ch["id"],
            "title":        ch["title"],
            "chapter_type": ch.get("chapter_type", "general_section"),
            "icon":         CHAPTER_ICONS.get(ch.get("chapter_type", ""), "file-text"),
            "header_component": {
                "component": "chapter_header",
                "props": {
                    "title": ch["title"],
                    "icon":  CHAPTER_ICONS.get(ch.get("chapter_type", ""), "file-text"),
                    "type_label": ch.get("chapter_type", "").replace("_", " ").title(),
                },
                "interactive": False,
            },
            "sections": []
        }

        print(f"  Chapter: {ch['title']}")

        for sec in ch["sections"]:
            mapped_sec = map_section(sec)
            ch_page["sections"].append(mapped_sec)

            for comp in mapped_sec["components"]:
                ct = comp["component"]
                comp_type_counts[ct] = comp_type_counts.get(ct, 0) + 1
                total_components += 1
                if comp.get("interactive"):
                    total_interactive += 1

            flag = "âš¡" if mapped_sec["interactive_count"] else "  "
            print(f"    {flag} [{sec['section_type'][:18]:<18}] "
                  f"{sec['title'][:40]:<40} "
                  f"â†’ {mapped_sec['component_count']} components "
                  f"({mapped_sec['interactive_count']} interactive)")

        component_map["pages"]["chapters"].append(ch_page)

    # Navigation tree
    component_map["navigation"] = build_navigation(
        component_map["pages"]["chapters"]
    )

    component_map["stats"] = {
        "total_components":    total_components,
        "interactive_components": total_interactive,
        "static_components":   total_components - total_interactive,
        "component_type_breakdown": comp_type_counts,
        "chapters": len(component_map["pages"]["chapters"]),
        "token_cost": 0,
    }

    return component_map


# â”€â”€ REPORT â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def print_report(cmap: dict) -> str:
    lines = []
    s = cmap["stats"]
    lines.append("=" * 60)
    lines.append("  PHASE 4 INTERACTIVITY REPORT")
    lines.append("=" * 60)
    lines.append(f"\n  Total UI components    : {s['total_components']}")
    lines.append(f"  Interactive components : {s['interactive_components']}")
    lines.append(f"  Static components     : {s['static_components']}")
    lines.append(f"  Token cost            : {s['token_cost']} âœ“")

    lines.append(f"\n  --- Component Breakdown ---")
    for comp, count in sorted(s["component_type_breakdown"].items(), key=lambda x: -x[1]):
        reg  = cmap["component_registry"].get(comp, {})
        flag = "âš¡ interactive" if reg.get("interactive") else "  static"
        lines.append(f"    {comp:<28} x{count:<3}  [{flag}]")

    lines.append(f"\n  --- Navigation Tree ---")
    for ch in cmap["navigation"]["chapters"]:
        lines.append(f"\n  [{ch['icon']}] {ch['title']}")
        for sec in ch["sections"]:
            flag = " âš¡" if sec["has_interactive"] else ""
            lines.append(f"      #{sec['anchor']:<18}  {sec['title']}{flag}")

    lines.append(f"\n  --- Interactive Components Summary ---")
    for ch in cmap["pages"]["chapters"]:
        for sec in ch["sections"]:
            for comp in sec["components"]:
                if comp.get("interactive"):
                    lines.append(f"  âš¡ {comp['component']:<28} in '{sec['title'][:40]}'")

    lines.append("\n" + "=" * 60)
    lines.append("  Phase 4 Complete â€” component_map.json ready for Phase 5")
    lines.append("=" * 60)
    return "\n".join(lines)


# â”€â”€ RUN â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
if __name__ == "__main__":
    cmap = run_interactivity_agent(INPUT_JSON)

    with open(OUTPUT_JSON, "w") as f:
        json.dump(cmap, f, indent=2, ensure_ascii=False)
    print(f"\n  Saved: {OUTPUT_JSON}")

    report = print_report(cmap)
    print(report)
    with open(OUTPUT_REPORT, "w") as f:
        f.write(report)
    print(f"  Saved: {OUTPUT_REPORT}")


