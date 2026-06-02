#!/usr/bin/env python3
"""
Phase 5: Web Builder Agent
============================
Input : component_map.json  (from Phase 4)
Output: hydropress_x500_manual.html  (fully self-contained interactive web manual)
Token cost: ZERO
"""

import json

INPUT_JSON = r"E:\repos\reposEPSON-RC-online-manual\pipeline_output\component_map.json"
OUTPUT_HTML = r"E:\repos\reposEPSON-RC-online-manual\pipeline_output\manual.html"

with open(INPUT_JSON) as f:
    cmap = json.load(f)

# â”€â”€ Pull live data from component_map â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
nav_chapters = cmap["navigation"]["chapters"]

# Gather interactive component data
checklist_items  = []
fault_tree       = []
maint_rows       = []
procedures       = {}   # section_id â†’ {title, steps}

for ch in cmap["pages"]["chapters"]:
    for sec in ch["sections"]:
        for comp in sec["components"]:
            if comp["component"] == "interactive_checklist":
                checklist_items = comp["props"]["checklist_items"]
            elif comp["component"] == "fault_finder":
                fault_tree = comp["props"]["decision_tree"]
            elif comp["component"] == "maintenance_schedule":
                maint_rows = comp["props"]["rows"]
            elif comp["component"] == "procedure_wizard":
                sid = sec["id"]
                if sid not in procedures:
                    procedures[sid] = {"title": sec["title"], "steps": []}
                procedures[sid]["steps"].extend(comp["props"]["steps"])

checklist_json = json.dumps(checklist_items)
fault_json     = json.dumps(fault_tree)
maint_json     = json.dumps(maint_rows)
proc_json      = json.dumps(procedures)

# Build nav HTML
def nav_html():
    html = ""
    icons = {
        "shield-alert":    "âš ",
        "clipboard-list":  "ðŸ“‹",
        "wrench":          "ðŸ”§",
        "play-circle":     "â–¶",
        "calendar-check":  "ðŸ“…",
        "search":          "ðŸ”",
    }
    for i, ch in enumerate(nav_chapters):
        icon = icons.get(ch["icon"], "ðŸ“„")
        secs = ""
        for sec in ch["sections"]:
            badge = '<span class="nav-badge">âš¡</span>' if sec["has_interactive"] else ""
            secs += f'<a href="#{sec["anchor"]}" class="nav-sec">{sec["title"]}{badge}</a>\n'
        html += f'''
        <div class="nav-chapter">
          <button class="nav-ch-btn" onclick="toggleNav(this)">
            <span class="nav-icon">{icon}</span>
            <span>{ch["title"].replace("Chapter "+str(i+1)+": ","")}</span>
            <span class="nav-chevron">â€º</span>
          </button>
          <div class="nav-secs">{secs}</div>
        </div>'''
    return html

HTML = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>HydroPress X500 â€” Interactive Manual</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=JetBrains+Mono:wght@400;500&family=Inter:wght@300;400;500&display=swap" rel="stylesheet">
<style>
/* â”€â”€ DESIGN TOKENS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
:root {{
  --bg:        #0d0f14;
  --surface:   #151820;
  --surface2:  #1c2030;
  --border:    #252a38;
  --accent:    #e8a020;
  --accent2:   #3b82f6;
  --danger:    #ef4444;
  --warning:   #f59e0b;
  --caution:   #f97316;
  --note:      #3b82f6;
  --success:   #22c55e;
  --text:      #e8eaf0;
  --text-dim:  #7a8099;
  --text-muted:#4a5068;
  --font-head: 'Syne', sans-serif;
  --font-mono: 'JetBrains Mono', monospace;
  --font-body: 'Inter', sans-serif;
  --nav-w:     280px;
  --radius:    10px;
  --shadow:    0 4px 24px rgba(0,0,0,.4);
}}

/* â”€â”€ RESET & BASE â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
html {{ scroll-behavior: smooth; }}
body {{
  background: var(--bg);
  color: var(--text);
  font-family: var(--font-body);
  font-size: 15px;
  line-height: 1.7;
  display: flex;
  min-height: 100vh;
}}

/* â”€â”€ SIDEBAR NAV â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
#sidebar {{
  width: var(--nav-w);
  min-width: var(--nav-w);
  background: var(--surface);
  border-right: 1px solid var(--border);
  height: 100vh;
  position: sticky;
  top: 0;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  z-index: 100;
}}
.sidebar-logo {{
  padding: 24px 20px 16px;
  border-bottom: 1px solid var(--border);
}}
.sidebar-logo .model {{
  font-family: var(--font-head);
  font-size: 20px;
  font-weight: 800;
  color: var(--accent);
  letter-spacing: -0.5px;
}}
.sidebar-logo .sub {{
  font-size: 11px;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 1.5px;
  margin-top: 2px;
}}
.nav-chapter {{ border-bottom: 1px solid var(--border); }}
.nav-ch-btn {{
  width: 100%;
  background: none;
  border: none;
  color: var(--text);
  font-family: var(--font-head);
  font-size: 13px;
  font-weight: 600;
  padding: 12px 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  text-align: left;
  transition: background .15s;
}}
.nav-ch-btn:hover {{ background: var(--surface2); }}
.nav-icon {{ font-size: 16px; }}
.nav-chevron {{ margin-left: auto; transition: transform .2s; font-size: 18px; color: var(--text-muted); }}
.nav-ch-btn.open .nav-chevron {{ transform: rotate(90deg); }}
.nav-secs {{ display: none; padding: 0 0 8px 0; }}
.nav-secs.open {{ display: block; }}
.nav-sec {{
  display: block;
  padding: 6px 16px 6px 40px;
  font-size: 12px;
  color: var(--text-dim);
  text-decoration: none;
  transition: color .15s, background .15s;
  border-left: 2px solid transparent;
}}
.nav-sec:hover {{
  color: var(--accent);
  background: rgba(232,160,32,.05);
  border-left-color: var(--accent);
}}
.nav-badge {{
  display: inline-block;
  font-size: 9px;
  background: var(--accent2);
  color: white;
  border-radius: 4px;
  padding: 1px 4px;
  margin-left: 4px;
  vertical-align: middle;
}}

/* â”€â”€ MAIN CONTENT â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
#main {{
  flex: 1;
  overflow-y: auto;
  padding: 0;
}}

/* â”€â”€ COVER HERO â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
#cover {{
  background: linear-gradient(135deg, #0d0f14 0%, #151c2e 50%, #0d1420 100%);
  border-bottom: 1px solid var(--border);
  padding: 80px 64px 64px;
  position: relative;
  overflow: hidden;
}}
#cover::before {{
  content:'';
  position: absolute;
  top: -40%;
  right: -10%;
  width: 600px; height: 600px;
  background: radial-gradient(circle, rgba(232,160,32,.08) 0%, transparent 70%);
  pointer-events: none;
}}
#cover::after {{
  content:'';
  position: absolute;
  bottom: 0; left: 0; right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--accent), transparent);
}}
.cover-eyebrow {{
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--accent);
  letter-spacing: 3px;
  text-transform: uppercase;
  margin-bottom: 16px;
}}
.cover-title {{
  font-family: var(--font-head);
  font-size: clamp(40px, 6vw, 72px);
  font-weight: 800;
  line-height: 1;
  letter-spacing: -2px;
  color: var(--text);
  margin-bottom: 8px;
}}
.cover-title span {{ color: var(--accent); }}
.cover-subtitle {{
  font-family: var(--font-head);
  font-size: 20px;
  font-weight: 400;
  color: var(--text-dim);
  margin-bottom: 32px;
}}
.cover-badges {{
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}}
.badge {{
  font-family: var(--font-mono);
  font-size: 11px;
  padding: 5px 12px;
  border-radius: 20px;
  font-weight: 500;
  letter-spacing: .5px;
}}
.badge-gold  {{ background: rgba(232,160,32,.15); color: var(--accent); border: 1px solid rgba(232,160,32,.3); }}
.badge-blue  {{ background: rgba(59,130,246,.15); color: #60a5fa; border: 1px solid rgba(59,130,246,.3); }}
.badge-dim   {{ background: var(--surface2); color: var(--text-dim); border: 1px solid var(--border); }}

/* â”€â”€ PAGE SECTIONS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
.chapter-block {{
  padding: 48px 64px;
  border-bottom: 1px solid var(--border);
}}
.chapter-header {{
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 32px;
}}
.chapter-icon {{
  font-size: 28px;
  width: 52px; height: 52px;
  background: var(--surface2);
  border: 1px solid var(--border);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}}
.chapter-title {{
  font-family: var(--font-head);
  font-size: 26px;
  font-weight: 700;
  letter-spacing: -0.5px;
}}
.chapter-type-badge {{
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--text-muted);
  letter-spacing: 1px;
  text-transform: uppercase;
  margin-top: 2px;
}}
.section-block {{
  margin-bottom: 40px;
  scroll-margin-top: 24px;
}}
.section-title {{
  font-family: var(--font-head);
  font-size: 17px;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border);
}}

/* â”€â”€ SAFETY BANNERS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
.safety-banner {{
  border-radius: var(--radius);
  padding: 14px 18px;
  margin: 16px 0;
  display: flex;
  gap: 12px;
  align-items: flex-start;
  border-left: 4px solid;
}}
.safety-banner.danger  {{ background:rgba(239,68,68,.08);  border-color:var(--danger);  }}
.safety-banner.warning {{ background:rgba(245,158,11,.08); border-color:var(--warning); }}
.safety-banner.caution {{ background:rgba(249,115,22,.08); border-color:var(--caution); }}
.safety-banner.note    {{ background:rgba(59,130,246,.08); border-color:var(--note);    }}
.safety-icon {{ font-size: 18px; margin-top: 1px; }}
.safety-label {{
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 500;
  letter-spacing: 1.5px;
  text-transform: uppercase;
  margin-bottom: 4px;
}}
.danger  .safety-label {{ color: var(--danger);  }}
.warning .safety-label {{ color: var(--warning); }}
.caution .safety-label {{ color: var(--caution); }}
.note    .safety-label {{ color: var(--note);    }}
.safety-text {{ font-size: 14px; color: var(--text-dim); }}

/* â”€â”€ SPEC TABLE â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
.spec-table-wrap {{ overflow-x: auto; margin-top: 8px; }}
.spec-summary {{
  font-size: 13px;
  color: var(--text-dim);
  background: var(--surface2);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 10px 14px;
  margin-bottom: 12px;
  font-style: italic;
}}
table.spec {{
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}}
table.spec th {{
  background: var(--surface2);
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 500;
  letter-spacing: 1px;
  text-transform: uppercase;
  color: var(--text-dim);
  padding: 10px 14px;
  text-align: left;
  border-bottom: 1px solid var(--border);
}}
table.spec td {{
  padding: 9px 14px;
  border-bottom: 1px solid rgba(37,42,56,.6);
  color: var(--text);
}}
table.spec tr:last-child td {{ border-bottom: none; }}
table.spec tr:hover td {{ background: rgba(255,255,255,.02); }}

/* â”€â”€ BODY TEXT â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
.body-prose {{ color: var(--text-dim); font-size: 14px; line-height: 1.8; }}
.body-prose p {{ margin-bottom: 10px; }}

/* â”€â”€ PROCEDURE WIZARD â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
.wizard {{
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
  margin-top: 8px;
}}
.wizard-header {{
  background: var(--surface2);
  padding: 14px 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--border);
}}
.wizard-title {{
  font-family: var(--font-head);
  font-size: 14px;
  font-weight: 600;
}}
.wizard-progress {{
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--accent);
}}
.wizard-bar-wrap {{
  height: 3px;
  background: var(--border);
}}
.wizard-bar {{
  height: 100%;
  background: var(--accent);
  transition: width .3s ease;
}}
.wizard-body {{ padding: 24px 20px; }}
.wizard-step-num {{
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--accent);
  letter-spacing: 1px;
  text-transform: uppercase;
  margin-bottom: 8px;
}}
.wizard-step-text {{
  font-size: 15px;
  color: var(--text);
  line-height: 1.7;
}}
.wizard-controls {{
  padding: 16px 20px;
  border-top: 1px solid var(--border);
  display: flex;
  gap: 10px;
  justify-content: space-between;
  align-items: center;
}}
.wizard-dots {{ display: flex; gap: 6px; }}
.wizard-dot {{
  width: 6px; height: 6px;
  border-radius: 50%;
  background: var(--border);
  transition: background .2s;
}}
.wizard-dot.active {{ background: var(--accent); }}
.wizard-dot.done   {{ background: var(--success); }}
.btn {{
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 500;
  letter-spacing: .5px;
  padding: 8px 18px;
  border-radius: 6px;
  border: none;
  cursor: pointer;
  transition: opacity .15s, transform .1s;
}}
.btn:hover {{ opacity: .85; transform: translateY(-1px); }}
.btn:active {{ transform: translateY(0); }}
.btn-primary  {{ background: var(--accent); color: #000; }}
.btn-ghost    {{ background: var(--surface2); color: var(--text-dim); border: 1px solid var(--border); }}
.btn-success  {{ background: var(--success); color: #000; }}
.wizard-done {{
  text-align: center;
  padding: 24px;
  color: var(--success);
  font-family: var(--font-head);
  font-size: 18px;
  font-weight: 700;
}}

/* â”€â”€ CHECKLIST â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
.checklist {{
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
  margin-top: 8px;
}}
.checklist-header {{
  background: var(--surface2);
  padding: 14px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--border);
}}
.checklist-title {{
  font-family: var(--font-head);
  font-size: 14px;
  font-weight: 600;
}}
.checklist-progress {{
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--success);
}}
.checklist-bar-wrap {{ height: 3px; background: var(--border); }}
.checklist-bar {{ height:100%; background: var(--success); transition: width .3s; }}
.checklist-item {{
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 14px 20px;
  border-bottom: 1px solid var(--border);
  cursor: pointer;
  transition: background .15s;
}}
.checklist-item:last-child {{ border-bottom: none; }}
.checklist-item:hover {{ background: rgba(255,255,255,.02); }}
.checklist-item.checked {{ opacity: .55; }}
.checklist-cb {{
  width: 20px; height: 20px;
  border: 2px solid var(--border);
  border-radius: 5px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-top: 1px;
  transition: all .15s;
}}
.checklist-item.checked .checklist-cb {{
  background: var(--success);
  border-color: var(--success);
  color: #000;
}}
.checklist-item-body {{ flex: 1; }}
.checklist-item-name {{
  font-size: 14px;
  font-weight: 500;
  color: var(--text);
  display: flex;
  align-items: center;
  gap: 8px;
}}
.crit-badge {{
  font-family: var(--font-mono);
  font-size: 9px;
  background: rgba(239,68,68,.15);
  color: var(--danger);
  border: 1px solid rgba(239,68,68,.3);
  border-radius: 4px;
  padding: 1px 5px;
  letter-spacing: .5px;
}}
.checklist-item-expected {{
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 3px;
}}
.checklist-footer {{
  padding: 12px 20px;
  border-top: 1px solid var(--border);
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}}

/* â”€â”€ MAINTENANCE SCHEDULE â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
.maint-wrap {{
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
  margin-top: 8px;
}}
.maint-filters {{
  padding: 14px 20px;
  background: var(--surface2);
  border-bottom: 1px solid var(--border);
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  align-items: center;
}}
.filter-label {{
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-muted);
  letter-spacing: 1px;
  text-transform: uppercase;
  margin-right: 4px;
}}
.filter-btn {{
  font-family: var(--font-mono);
  font-size: 11px;
  padding: 4px 12px;
  border-radius: 20px;
  border: 1px solid var(--border);
  background: none;
  color: var(--text-dim);
  cursor: pointer;
  transition: all .15s;
}}
.filter-btn.active, .filter-btn:hover {{
  background: var(--accent);
  color: #000;
  border-color: var(--accent);
}}
.maint-table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
.maint-table th {{
  font-family: var(--font-mono);
  font-size: 11px;
  letter-spacing: 1px;
  text-transform: uppercase;
  color: var(--text-muted);
  padding: 10px 16px;
  text-align: left;
  border-bottom: 1px solid var(--border);
  background: var(--surface);
}}
.maint-table td {{ padding: 11px 16px; border-bottom: 1px solid rgba(37,42,56,.5); }}
.maint-table tr:last-child td {{ border-bottom: none; }}
.maint-table tr:hover td {{ background: rgba(255,255,255,.015); }}
.prio-badge {{
  font-family: var(--font-mono);
  font-size: 10px;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 500;
}}
.prio-high   {{ background:rgba(239,68,68,.15);  color:var(--danger);  }}
.prio-medium {{ background:rgba(245,158,11,.15); color:var(--warning); }}
.prio-low    {{ background:rgba(34,197,94,.15);  color:var(--success); }}
.time-chip {{
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-muted);
  background: var(--surface2);
  padding: 2px 8px;
  border-radius: 4px;
}}

/* â”€â”€ FAULT FINDER â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
.fault-finder {{
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
  margin-top: 8px;
}}
.fault-search-wrap {{
  padding: 16px 20px;
  background: var(--surface2);
  border-bottom: 1px solid var(--border);
}}
.fault-search {{
  width: 100%;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 10px 16px;
  color: var(--text);
  font-family: var(--font-body);
  font-size: 14px;
  outline: none;
  transition: border-color .15s;
}}
.fault-search:focus {{ border-color: var(--accent); }}
.fault-search::placeholder {{ color: var(--text-muted); }}
.fault-results {{ padding: 8px 0; }}
.fault-symptom {{
  border-bottom: 1px solid var(--border);
  overflow: hidden;
}}
.fault-symptom:last-child {{ border-bottom: none; }}
.fault-symptom-btn {{
  width: 100%;
  background: none;
  border: none;
  padding: 14px 20px;
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  text-align: left;
  color: var(--text);
  font-family: var(--font-body);
  font-size: 14px;
  font-weight: 500;
  transition: background .15s;
}}
.fault-symptom-btn:hover {{ background: rgba(255,255,255,.02); }}
.fault-symptom-btn .arrow {{
  margin-left: auto;
  color: var(--text-muted);
  transition: transform .2s;
  font-size: 18px;
}}
.fault-symptom-btn.open .arrow {{ transform: rotate(90deg); color: var(--accent); }}
.fault-causes {{ display: none; background: rgba(0,0,0,.2); }}
.fault-causes.open {{ display: block; }}
.fault-cause {{
  padding: 12px 20px 12px 44px;
  border-bottom: 1px solid rgba(37,42,56,.5);
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px 20px;
}}
.fault-cause:last-child {{ border-bottom: none; }}
.cause-label, .fix-label {{
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: 1px;
  text-transform: uppercase;
  margin-bottom: 3px;
}}
.cause-label {{ color: var(--warning); }}
.fix-label   {{ color: var(--success); }}
.cause-text  {{ font-size: 13px; color: var(--text-dim); }}
.fix-text    {{ font-size: 13px; color: var(--text-dim); }}
.fault-empty {{
  padding: 32px;
  text-align: center;
  color: var(--text-muted);
  font-size: 14px;
}}

/* â”€â”€ SCROLLBAR â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
::-webkit-scrollbar {{ width: 6px; height: 6px; }}
::-webkit-scrollbar-track {{ background: var(--bg); }}
::-webkit-scrollbar-thumb {{ background: var(--border); border-radius: 3px; }}
::-webkit-scrollbar-thumb:hover {{ background: var(--text-muted); }}

/* â”€â”€ RESPONSIVE â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
@media(max-width:768px) {{
  body {{ flex-direction: column; }}
  #sidebar {{ width:100%; min-width:unset; height:auto; position:relative; }}
  .chapter-block {{ padding: 32px 20px; }}
  #cover {{ padding: 48px 20px 40px; }}
  .fault-cause {{ grid-template-columns: 1fr; }}
}}
</style>
</head>
<body>

<!-- â”€â”€ SIDEBAR â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ -->
<nav id="sidebar">
  <div class="sidebar-logo">
    <div class="model">HydroPress X500</div>
    <div class="sub">Interactive Manual Â· Rev 3.2</div>
  </div>
  {nav_html()}
</nav>

<!-- â”€â”€ MAIN â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ -->
<main id="main">

  <!-- COVER -->
  <section id="cover">
    <div class="cover-eyebrow">Technical Documentation</div>
    <h1 class="cover-title">HydroPress <span>X500</span></h1>
    <p class="cover-subtitle">Industrial Hydraulic Press â€” User &amp; Service Manual</p>
    <div class="cover-badges">
      <span class="badge badge-gold">HPX-500</span>
      <span class="badge badge-blue">Revision 3.2</span>
      <span class="badge badge-dim">2024-01</span>
      <span class="badge badge-dim">500 kN</span>
      <span class="badge badge-dim">500 bar max</span>
    </div>
  </section>

  <!-- CH1: SAFETY -->
  <section class="chapter-block" id="ch1">
    <div class="chapter-header">
      <div class="chapter-icon">âš </div>
      <div>
        <div class="chapter-title">Safety Information</div>
        <div class="chapter-type-badge">Chapter 1 Â· Safety</div>
      </div>
    </div>
    <div class="section-block" id="ch1_sec1">
      <div class="section-title">Safety Symbols &amp; Callouts</div>
      <div class="safety-banner danger">
        <div class="safety-icon">ðŸ”´</div>
        <div>
          <div class="safety-label">Danger</div>
          <div class="safety-text">The hydraulic system operates at pressures up to 500 bar (7,250 PSI). Never loosen hydraulic fittings while the system is pressurized. Always depressurize fully before any maintenance work.</div>
        </div>
      </div>
      <div class="safety-banner warning">
        <div class="safety-icon">âš ï¸</div>
        <div>
          <div class="safety-label">Warning â€” Crush Hazard</div>
          <div class="safety-text">Keep hands and body clear of the press ram at all times during operation. Use appropriate tooling and fixtures. Never place hands under the ram.</div>
        </div>
      </div>
      <div class="safety-banner caution">
        <div class="safety-icon">ðŸŸ </div>
        <div>
          <div class="safety-label">Caution</div>
          <div class="safety-text">Minor injury or equipment damage possible if safety instructions are not followed. Read all warnings carefully before operating this equipment.</div>
        </div>
      </div>
      <div class="safety-banner note">
        <div class="safety-icon">â„¹ï¸</div>
        <div>
          <div class="safety-label">Note â€” Personal Protective Equipment</div>
          <div class="safety-text">Always wear safety glasses, steel-toed boots, and hydraulic-resistant gloves when operating or servicing this equipment.</div>
        </div>
      </div>
    </div>
  </section>

  <!-- CH2: SPECS -->
  <section class="chapter-block" id="ch2">
    <div class="chapter-header">
      <div class="chapter-icon">ðŸ“‹</div>
      <div>
        <div class="chapter-title">Technical Specifications</div>
        <div class="chapter-type-badge">Chapter 2 Â· Specifications</div>
      </div>
    </div>
    <div class="section-block" id="ch2_sec1">
      <div class="section-title">General Specifications</div>
      <div class="spec-summary">The HydroPress X500 delivers up to 500 kN of press force with a 300 mm stroke, operating at pressures up to 500 bar and powered by a 7.5 kW motor.</div>
      <div class="spec-table-wrap">
        <table class="spec">
          <thead><tr><th>Parameter</th><th>Value</th><th>Unit</th></tr></thead>
          <tbody>
            <tr><td>Maximum Press Force</td><td>500</td><td>kN</td></tr>
            <tr><td>Maximum Pressure</td><td>500</td><td>bar</td></tr>
            <tr><td>Ram Stroke</td><td>300</td><td>mm</td></tr>
            <tr><td>Daylight Opening</td><td>600</td><td>mm</td></tr>
            <tr><td>Bed Size (W Ã— D)</td><td>600 Ã— 400</td><td>mm</td></tr>
            <tr><td>Ram Speed (Rapid)</td><td>80</td><td>mm/s</td></tr>
            <tr><td>Ram Speed (Press)</td><td>10</td><td>mm/s</td></tr>
            <tr><td>Motor Power</td><td>7.5</td><td>kW</td></tr>
            <tr><td>Hydraulic Oil Capacity</td><td>60</td><td>L</td></tr>
            <tr><td>Operating Temperature</td><td>10 to 50</td><td>Â°C</td></tr>
            <tr><td>Weight (approx.)</td><td>2,400</td><td>kg</td></tr>
            <tr><td>Noise Level</td><td>&lt; 72</td><td>dB(A)</td></tr>
          </tbody>
        </table>
      </div>
    </div>
    <div class="section-block" id="ch2_sec3">
      <div class="section-title">Hydraulic System Specifications</div>
      <div class="spec-summary">The hydraulic system uses a fixed-displacement axial piston pump delivering 45 L/min, filtered to 10 microns, requiring ISO VG 46 oil changed every 2,000 hours.</div>
      <div class="spec-table-wrap">
        <table class="spec">
          <thead><tr><th>Component</th><th>Specification</th></tr></thead>
          <tbody>
            <tr><td>Pump Type</td><td>Fixed displacement axial piston</td></tr>
            <tr><td>Pump Flow Rate</td><td>45 L/min at 1,450 RPM</td></tr>
            <tr><td>Relief Valve</td><td>Factory set at 520 bar (do not adjust)</td></tr>
            <tr><td>Filtration</td><td>10 micron return line filter</td></tr>
            <tr><td>Recommended Oil</td><td>ISO VG 46 hydraulic oil</td></tr>
            <tr><td>Oil Change Interval</td><td>Every 2,000 operating hours</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  </section>

  <!-- CH3: INSTALLATION -->
  <section class="chapter-block" id="ch3">
    <div class="chapter-header">
      <div class="chapter-icon">ðŸ”§</div>
      <div>
        <div class="chapter-title">Installation</div>
        <div class="chapter-type-badge">Chapter 3 Â· Installation</div>
      </div>
    </div>
    <div class="section-block" id="ch3_sec1">
      <div class="section-title">3.1 Site Requirements</div>
      <div class="body-prose"><p>Ensure the installation site meets all requirements listed below before machine delivery. Inadequate site preparation is the most common cause of installation delays.</p></div>
      <div class="spec-table-wrap">
        <table class="spec">
          <thead><tr><th>Requirement</th><th>Minimum Value</th></tr></thead>
          <tbody>
            <tr><td>Floor Load Capacity</td><td>15,000 kg/mÂ²</td></tr>
            <tr><td>Ceiling Height</td><td>3,500 mm</td></tr>
            <tr><td>Power Supply</td><td>400V / 3-phase / 50Hz / 32A</td></tr>
            <tr><td>Ventilation</td><td>10 air changes per hour</td></tr>
            <tr><td>Ambient Temperature</td><td>10Â°C to 40Â°C</td></tr>
            <tr><td>Relative Humidity</td><td>20% to 80% non-condensing</td></tr>
          </tbody>
        </table>
      </div>
    </div>
    <div class="section-block" id="ch3_sec3">
      <div class="section-title">3.2 Installation Procedure</div>
      <div class="safety-banner warning">
        <div class="safety-icon">âš ï¸</div>
        <div>
          <div class="safety-label">Warning</div>
          <div class="safety-text">Use only certified lifting equipment rated for minimum 3,000 kg capacity.</div>
        </div>
      </div>
      <div id="wizard-install" class="wizard"></div>
    </div>
  </section>

  <!-- CH4: OPERATION -->
  <section class="chapter-block" id="ch4">
    <div class="chapter-header">
      <div class="chapter-icon">â–¶</div>
      <div>
        <div class="chapter-title">Operation</div>
        <div class="chapter-type-badge">Chapter 4 Â· Operation</div>
      </div>
    </div>
    <div class="section-block" id="ch4_sec1">
      <div class="section-title">4.1 Pre-Operation Checklist</div>
      <div class="body-prose"><p>Perform all checks before every shift. Do not operate the machine if any item fails.</p></div>
      <div id="checklist-preop" class="checklist"></div>
    </div>
    <div class="section-block" id="ch4_sec3">
      <div class="section-title">4.2 Standard Pressing Operation</div>
      <div id="wizard-press" class="wizard"></div>
    </div>
  </section>

  <!-- CH5: MAINTENANCE -->
  <section class="chapter-block" id="ch5">
    <div class="chapter-header">
      <div class="chapter-icon">ðŸ“…</div>
      <div>
        <div class="chapter-title">Maintenance &amp; Service</div>
        <div class="chapter-type-badge">Chapter 5 Â· Maintenance</div>
      </div>
    </div>
    <div class="section-block" id="ch5_sec1">
      <div class="section-title">5.1 Preventive Maintenance Schedule</div>
      <div id="maint-schedule" class="maint-wrap"></div>
    </div>
    <div class="section-block" id="ch5_sec2">
      <div class="section-title">5.2 Hydraulic Oil Change Procedure</div>
      <div class="safety-banner caution">
        <div class="safety-icon">ðŸŸ </div>
        <div>
          <div class="safety-label">Caution</div>
          <div class="safety-text">Dispose of used hydraulic oil according to local environmental regulations.</div>
        </div>
      </div>
      <div id="wizard-oil" class="wizard"></div>
    </div>
  </section>

  <!-- CH6: TROUBLESHOOTING -->
  <section class="chapter-block" id="ch6">
    <div class="chapter-header">
      <div class="chapter-icon">ðŸ”</div>
      <div>
        <div class="chapter-title">Troubleshooting</div>
        <div class="chapter-type-badge">Chapter 6 Â· Fault Finder</div>
      </div>
    </div>
    <div class="section-block" id="ch6_sec1">
      <div class="section-title">Fault Finder</div>
      <div class="body-prose"><p>Search for your symptom below. If the problem persists after following corrective actions, contact HydroPress Technical Support.</p></div>
      <div id="fault-finder" class="fault-finder"></div>
    </div>
  </section>

</main>

<script>
// â”€â”€ DATA FROM PIPELINE â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
const CHECKLIST = {checklist_json};
const FAULT_TREE = {fault_json};
const MAINT_ROWS = {maint_json};
const PROCEDURES = {proc_json};

// â”€â”€ NAV TOGGLE â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
function toggleNav(btn) {{
  btn.classList.toggle('open');
  const secs = btn.nextElementSibling;
  secs.classList.toggle('open');
}}
// Open first chapter by default
document.addEventListener('DOMContentLoaded', () => {{
  const firstBtn = document.querySelector('.nav-ch-btn');
  if (firstBtn) toggleNav(firstBtn);
}});

// â”€â”€ WIZARD COMPONENT â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
function buildWizard(el, steps, title) {{
  if (!el || !steps || !steps.length) return;
  let current = 0;

  function render() {{
    const pct = Math.round(((current) / steps.length) * 100);
    const done = current >= steps.length;
    el.innerHTML = `
      <div class="wizard-header">
        <span class="wizard-title">${{title}}</span>
        <span class="wizard-progress">${{done ? 'âœ“ Complete' : `Step ${{current+1}} of ${{steps.length}}`}}</span>
      </div>
      <div class="wizard-bar-wrap"><div class="wizard-bar" style="width:${{pct}}%"></div></div>
      <div class="wizard-body">
        ${{done
          ? `<div class="wizard-done">âœ“ Procedure Complete</div>`
          : `<div class="wizard-step-num">Step ${{current + 1}} of ${{steps.length}}</div>
             <div class="wizard-step-text">${{steps[current].replace(/^Step\s+\d+:\s*/i,'')}}</div>`
        }}
      </div>
      <div class="wizard-controls">
        <button class="btn btn-ghost" onclick="wizBack('${{el.id}}')" ${{current===0||done?'disabled style="opacity:.3"':''}}>â† Back</button>
        <div class="wizard-dots">
          ${{steps.map((_,i) => `<div class="wizard-dot ${{i<current?'done':i===current?'active':''}}"></div>`).join('')}}
        </div>
        <button class="btn ${{done?'btn-success':'btn-primary'}}" onclick="wizNext('${{el.id}}')" ${{done?'disabled':''}}>
          ${{done ? 'âœ“ Done' : current===steps.length-1 ? 'Finish âœ“' : 'Next â†’'}}
        </button>
      </div>`;
  }}

  el._wizState = {{ steps, title, current: 0, render }};
  render();
}}

const _wizards = {{}};
function initWizard(id, steps, title) {{
  const el = document.getElementById(id);
  if (!el) return;
  let current = 0;
  _wizards[id] = {{ steps, current }};
  renderWizard(id, title);
}}
function renderWizard(id, titleOverride) {{
  const el = document.getElementById(id);
  const w = _wizards[id];
  if (!el||!w) return;
  const {{ steps, current }} = w;
  const pct = Math.round((current / steps.length) * 100);
  const done = current >= steps.length;
  const title = titleOverride || el.dataset.title || 'Procedure';
  el.innerHTML = `
    <div class="wizard-header">
      <span class="wizard-title">${{title}}</span>
      <span class="wizard-progress">${{done ? 'âœ“ Complete' : `Step ${{current+1}} / ${{steps.length}}`}}</span>
    </div>
    <div class="wizard-bar-wrap"><div class="wizard-bar" style="width:${{pct}}%"></div></div>
    <div class="wizard-body">
      ${{done
        ? '<div class="wizard-done">âœ“ Procedure Complete</div>'
        : `<div class="wizard-step-num">Step ${{current + 1}}</div>
           <div class="wizard-step-text">${{steps[current].replace(/^Step\s+\d+[:.]\s*/i,'')}}</div>`
      }}
    </div>
    <div class="wizard-controls">
      <button class="btn btn-ghost" onclick="wizBack('${{id}}','${{title}}')" ${{current===0||done?'disabled style="opacity:.3"':''}}>â† Back</button>
      <div class="wizard-dots">${{steps.map((_,i)=>`<div class="wizard-dot ${{i<current?'done':i===current?'active':''}}"></div>`).join('')}}</div>
      <button class="btn ${{done?'btn-success':'btn-primary'}}" onclick="wizNext('${{id}}','${{title}}')" ${{done?'disabled':''}}>
        ${{done?'âœ“ Done':current===steps.length-1?'Finish âœ“':'Next â†’'}}
      </button>
    </div>`;
}}
function wizNext(id, title) {{ const w=_wizards[id]; if(w&&w.current<w.steps.length){{ w.current++; renderWizard(id,title); }} }}
function wizBack(id, title) {{ const w=_wizards[id]; if(w&&w.current>0){{ w.current--; renderWizard(id,title); }} }}

// â”€â”€ CHECKLIST COMPONENT â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
function buildChecklist(el, items) {{
  if (!el) return;
  let checked = new Set();

  function render() {{
    const pct = Math.round((checked.size / items.length) * 100);
    el.innerHTML = `
      <div class="checklist-header">
        <span class="checklist-title">Pre-Operation Checklist</span>
        <span class="checklist-progress">${{checked.size}} / ${{items.length}} complete</span>
      </div>
      <div class="checklist-bar-wrap"><div class="checklist-bar" style="width:${{pct}}%"></div></div>
      ${{items.map((item,i) => `
        <div class="checklist-item ${{checked.has(i)?'checked':''}}" onclick="toggleCheck(${{i}})">
          <div class="checklist-cb">${{checked.has(i)?'âœ“':''}}</div>
          <div class="checklist-item-body">
            <div class="checklist-item-name">
              ${{item.item}}
              ${{item.critical?'<span class="crit-badge">CRITICAL</span>':''}}
            </div>
            <div class="checklist-item-expected">Expected: ${{item.expected}}</div>
          </div>
        </div>`).join('')}}
      <div class="checklist-footer">
        <button class="btn btn-ghost" onclick="resetChecklist()">Reset</button>
        ${{pct===100?'<button class="btn btn-success" disabled>âœ“ All Checks Passed</button>':''}}
      </div>`;
  }}

  window.toggleCheck = (i) => {{ checked.has(i)?checked.delete(i):checked.add(i); render(); }};
  window.resetChecklist = () => {{ checked.clear(); render(); }};
  render();
}}

// â”€â”€ MAINTENANCE SCHEDULE â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
function buildMaintSchedule(el, rows) {{
  if (!el) return;
  const intervals = ['All', ...new Set(rows.map(r => r.interval))];
  let activeFilter = 'All';

  function render() {{
    const filtered = activeFilter==='All' ? rows : rows.filter(r=>r.interval===activeFilter);
    el.innerHTML = `
      <div class="maint-filters">
        <span class="filter-label">Filter:</span>
        ${{intervals.map(iv=>`<button class="filter-btn ${{activeFilter===iv?'active':''}}" onclick="setMaintFilter('${{iv}}')">${{iv}}</button>`).join('')}}
      </div>
      <table class="maint-table">
        <thead><tr><th>Interval</th><th>Task</th><th>Priority</th><th>Est. Time</th><th>Reference</th></tr></thead>
        <tbody>
          ${{filtered.map(r=>`
            <tr>
              <td><span class="badge badge-dim">${{r.interval}}</span></td>
              <td>${{r.task}}</td>
              <td><span class="prio-badge prio-${{r.priority}}">${{r.priority}}</span></td>
              <td><span class="time-chip">~${{r.est_minutes}} min</span></td>
              <td style="color:var(--text-muted);font-size:12px">${{r.reference}}</td>
            </tr>`).join('')}}
        </tbody>
      </table>`;
  }}

  window.setMaintFilter = (iv) => {{ activeFilter=iv; render(); }};
  render();
}}

// â”€â”€ FAULT FINDER â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
function buildFaultFinder(el, tree) {{
  if (!el) return;
  let query = '';
  let openSymptom = null;

  function render() {{
    const filtered = query
      ? tree.filter(s => s.symptom.toLowerCase().includes(query.toLowerCase()))
      : tree;
    el.innerHTML = `
      <div class="fault-search-wrap">
        <input class="fault-search" placeholder="Describe the problem (e.g. 'ram not moving')..."
               value="${{query}}" oninput="faultSearch(this.value)">
      </div>
      <div class="fault-results">
        ${{filtered.length===0
          ? '<div class="fault-empty">No matching symptoms found. Try different keywords.</div>'
          : filtered.map((s,i) => `
            <div class="fault-symptom">
              <button class="fault-symptom-btn ${{openSymptom===i?'open':''}}" onclick="toggleFault(${{i}})">
                <span>ðŸ”´</span>
                <span>${{s.symptom}}</span>
                <span class="arrow">â€º</span>
              </button>
              <div class="fault-causes ${{openSymptom===i?'open':''}}">
                ${{s.causes.map(c=>`
                  <div class="fault-cause">
                    <div>
                      <div class="cause-label">Possible Cause</div>
                      <div class="cause-text">${{c.cause}}</div>
                    </div>
                    <div>
                      <div class="fix-label">Corrective Action</div>
                      <div class="fix-text">${{c.fix}}</div>
                    </div>
                  </div>`).join('')}}
              </div>
            </div>`).join('')
        }}
      </div>`;
  }}

  window.faultSearch = (v) => {{ query=v; openSymptom=null; render(); }};
  window.toggleFault = (i) => {{ openSymptom = openSymptom===i ? null : i; render(); }};
  render();
}}

// â”€â”€ INIT ALL COMPONENTS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
document.addEventListener('DOMContentLoaded', () => {{

  // Installation wizard
  const procKeys = Object.keys(PROCEDURES);
  const installKey = procKeys.find(k=>k.includes('ch3'));
  const pressKey   = procKeys.find(k=>k.includes('ch4_sec3'));
  const oilKey     = procKeys.find(k=>k.includes('ch5'));

  if(installKey) initWizard('wizard-install', PROCEDURES[installKey].steps, 'Installation Procedure');
  if(pressKey)   initWizard('wizard-press',   PROCEDURES[pressKey].steps,   'Standard Pressing Operation');
  if(oilKey)     initWizard('wizard-oil',     PROCEDURES[oilKey].steps,     'Hydraulic Oil Change');

  buildChecklist(document.getElementById('checklist-preop'), CHECKLIST);
  buildMaintSchedule(document.getElementById('maint-schedule'), MAINT_ROWS);
  buildFaultFinder(document.getElementById('fault-finder'), FAULT_TREE);
}});
</script>
</body>
</html>'''

with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
    f.write(HTML)

print(f"Web manual written â†’ {OUTPUT_HTML}")
print(f"File size: {len(HTML):,} bytes ({len(HTML)//1024} KB)")

