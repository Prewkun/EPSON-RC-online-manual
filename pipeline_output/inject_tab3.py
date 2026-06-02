import sys, re
sys.stdout.reconfigure(encoding='utf-8')

with open(r'E:\repos\reposEPSON-RC-online-manual\index.html', encoding='utf-8') as f:
    html = f.read()

with open(r'E:\repos\reposEPSON-RC-online-manual\pipeline_output\tab3_sidebar.html', encoding='utf-8') as f:
    sidebar_nav = f.read()

with open(r'E:\repos\reposEPSON-RC-online-manual\pipeline_output\tab3_content.html', encoding='utf-8') as f:
    content_sections = f.read()

print(f'Original HTML size: {len(html):,} bytes')

# 1. Add CSS variable
html = html.replace(
    "  --font:'Segoe UI',system-ui,sans-serif;",
    "  --font:'Segoe UI',system-ui,sans-serif;\n  --rc-accent:#f7a84f;",
    1
)

# 2. Add tab CSS
rc_css = """
#tab-rc.active{border-bottom-color:var(--rc-accent);color:var(--rc-accent)}
#tab-rc .tab-count{background:rgba(247,168,79,.15);color:var(--rc-accent)}
.rc-color{color:var(--rc-accent)!important}
.rc-subsec-list{display:flex;flex-direction:column;gap:4px;margin-top:10px;border-top:1px solid var(--border);padding-top:10px}
.rc-subsec{display:grid;grid-template-columns:140px 1fr auto;align-items:baseline;gap:8px;padding:4px 0;font-size:11.5px}
.rc-subsec-title{font-family:var(--mono);color:var(--rc-accent);font-size:11px;font-weight:600}
.rc-subsec-desc{color:var(--text2)}
.rc-subsec-pg{color:var(--text3);white-space:nowrap}
"""
html = html.replace('</style>', rc_css + '</style>', 1)

# 3. Add 3rd tab button - insert before the closing </div> of page-tabs
html = html.replace(
    '</div>\n\n<nav id="sidebar">',
    """  <div class="page-tab" id="tab-rc" onclick="switchPage('rc')">
    \U0001f4d8 RC+ Users Guide
    <span class="tab-count">23 chapters</span>
  </div>
</div>

<nav id="sidebar">""",
    1
)

# 4. Add RC+ sidebar before </nav>
rc_sidebar = f"""  <div id="sidebar-rc" style="display:none;flex-direction:column;height:100%">
    <div class="sidebar-header">
      <div class="sidebar-title rc-color">RC+ Users Guide</div>
      <div class="sidebar-subtitle">Epson RC+ 8.0 \xb7 Project Management &amp; Development</div>
    </div>
    <div class="sidebar-search">
      <input type="text" id="rc-sidebar-filter" placeholder="Filter chapters..." oninput="filterRcNav(this.value)">
    </div>
    <ul id="rc-nav-list" style="list-style:none;overflow-y:auto;flex:1;padding:4px 0">
{sidebar_nav}
    </ul>
  </div>
</nav>"""
html = html.replace('</nav>', rc_sidebar, 1)

# 5. Build RC page
rc_hero = """
  <!-- RC+ USERS GUIDE PAGE -->
  <div id="page-rc" style="display:none">
    <header style="position:sticky;top:44px;background:rgba(15,17,23,.95);backdrop-filter:blur(10px);border-bottom:1px solid var(--border);padding:8px 24px;display:flex;align-items:center;gap:12px;z-index:50;">
      <span style="font-size:13px;font-weight:600;color:var(--text2);white-space:nowrap">RC+ Users Guide</span>
      <div class="topbar-search">
        <input type="text" id="rc-search" placeholder="Search chapters..." oninput="searchRc(this.value)">
      </div>
      <span id="rc-search-info" style="font-size:12px;color:var(--rc-accent);display:none"></span>
      <span style="font-size:11px;color:var(--text3);margin-left:auto">23 chapters \xb7 742 pages</span>
    </header>
    <section style="padding:40px 44px 32px;border-bottom:1px solid var(--border);background:linear-gradient(135deg,#1f1510 0%,#1a1d27 60%,#1c1710 100%)">
      <div style="font-size:11px;font-weight:700;letter-spacing:2px;text-transform:uppercase;margin-bottom:8px;color:var(--rc-accent)">Epson RC+ 8.0 (Ver.8.0) \xb7 Rev.1</div>
      <div class="hero-title">RC+ Users Guide<br><span style="font-size:22px">Project Management &amp; Development</span></div>
      <div class="hero-sub" style="margin-bottom:24px">Complete guide to the Epson RC+ 8.0 IDE — from first connection to advanced conveyor tracking and robot calibration. Use this guide alongside the SPEL+ Language Reference and GUI Builder Reference tabs.</div>
      <div class="hero-stats">
        <div class="stat-chip"><span class="stat-num" style="color:var(--rc-accent)">23</span><span class="stat-label">Chapters</span></div>
        <div class="stat-chip"><span class="stat-num" style="color:var(--rc-accent)">742</span><span class="stat-label">Pages</span></div>
        <div class="stat-chip"><span class="stat-num" style="color:var(--rc-accent)">10</span><span class="stat-label">Topic Groups</span></div>
        <div class="stat-chip"><span class="stat-num" style="color:var(--rc-accent)">RC+ 8.0</span><span class="stat-label">Version</span></div>
      </div>
    </section>
    <div class="safety-banner">
      <strong>⚠️ Safety First:</strong> Read all safety information in Chapter 2 before operating any robot system. Ensure safety devices are installed and personnel are clear of the robot work envelope during operation.
    </div>
    <div class="filter-chips" id="rc-chips">
      <span class="chip active" onclick="filterRcGroup('all',this)">All</span>
      <span class="chip" onclick="filterRcGroup('rc-getting-started',this)">\U0001f680 Getting Started</span>
      <span class="chip" onclick="filterRcGroup('rc-ide',this)">\U0001f5a5 RC+ IDE</span>
      <span class="chip" onclick="filterRcGroup('rc-spel-dev',this)">⚡ SPEL+ Dev</span>
      <span class="chip" onclick="filterRcGroup('rc-simulator',this)">\U0001f916 Simulator</span>
      <span class="chip" onclick="filterRcGroup('rc-hardware',this)">⚙️ Hardware</span>
      <span class="chip" onclick="filterRcGroup('rc-connectivity',this)">\U0001f310 Connectivity</span>
      <span class="chip" onclick="filterRcGroup('rc-advanced',this)">\U0001f3ed Advanced</span>
    </div>
    <div id="rc-content" style="padding:0 24px 60px">
      <div id="rc-no-results" style="display:none;text-align:center;padding:60px 20px;color:var(--text3)">No chapters matched your search.</div>
"""
rc_page = rc_hero + content_sections + "\n    </div>\n  </div>\n"

html = html.replace('<button id="back-top"', rc_page + '\n<button id="back-top"', 1)

# 6. Patch switchPage
html = html.replace(
    "['spel','gui'].forEach(id=>{",
    "['spel','gui','rc'].forEach(id=>{",
    1
)
html = html.replace(
    "if(p==='gui')document.getElementById('gui-sidebar-filter').focus();",
    "if(p==='gui')document.getElementById('gui-sidebar-filter').focus();\n  if(p==='rc')document.getElementById('rc-sidebar-filter').focus();",
    1
)

# 7. Add RC JS
rc_js = """
function filterRcNav(q){
  q=q.toLowerCase();
  document.querySelectorAll('#rc-nav-list li').forEach(li=>{li.style.display=li.textContent.toLowerCase().includes(q)?'':'none';});
}
let rcSt;
function searchRc(q){
  clearTimeout(rcSt);
  rcSt=setTimeout(()=>{
    const cards=document.querySelectorAll('#rc-content .cmd-card');
    const secs=document.querySelectorAll('#rc-content .cat-section');
    const info=document.getElementById('rc-search-info');
    const noR=document.getElementById('rc-no-results');
    q=q.trim().toLowerCase();
    if(!q){cards.forEach(c=>c.classList.remove('hidden'));secs.forEach(s=>s.style.display='');info.style.display='none';noR.style.display='none';return;}
    let found=0;
    cards.forEach(c=>{const m=c.textContent.toLowerCase().includes(q);c.classList.toggle('hidden',!m);if(m)found++;});
    secs.forEach(s=>{s.style.display=s.querySelectorAll('.cmd-card:not(.hidden)').length>0?'':'none';});
    info.style.display='block';info.textContent=found+' chapter'+(found!==1?'s':'');
    noR.style.display=found===0?'block':'none';
  },120);
}
function filterRcGroup(id,chip){
  document.querySelectorAll('#rc-chips .chip').forEach(c=>c.classList.remove('active'));
  chip.classList.add('active');
  document.querySelectorAll('#rc-content .cat-section').forEach(s=>{s.style.display=id==='all'||s.id===id?'':'none';});
}
document.getElementById('sidebar-rc').style.display='none';
"""
html = html.replace('// Init: ensure correct sidebar shown', rc_js + '\n// Init: ensure correct sidebar shown', 1)

print(f'Modified HTML size: {len(html):,} bytes')

checks = [
    ('tab-rc', 'RC tab button'),
    ('sidebar-rc', 'RC sidebar'),
    ('page-rc', 'RC page'),
    ('filterRcNav', 'RC nav filter'),
    ("'rc']", 'switchPage updated'),
    ('rc-getting-started', 'Getting Started section'),
    ('rc-ide', 'IDE section'),
    ('rc-advanced', 'Advanced section'),
]
for token, label in checks:
    ok = token in html
    print(f'  {"OK" if ok else "MISSING"}: {label}')

with open(r'E:\repos\reposEPSON-RC-online-manual\index.html', 'w', encoding='utf-8') as f:
    f.write(html)
print('Saved index.html')
