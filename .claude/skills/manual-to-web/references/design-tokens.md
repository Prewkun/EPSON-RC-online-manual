# Design Tokens — Manual Web Output

## CSS Variables (Phase 5 default dark theme)

```css
:root {
  --bg:        #0d0f14;   /* page background */
  --surface:   #151820;   /* sidebar, card backgrounds */
  --surface2:  #1c2030;   /* hover states, table headers */
  --border:    #252a38;   /* all borders */
  --accent:    #e8a020;   /* primary highlight (amber-gold) */
  --accent2:   #3b82f6;   /* secondary highlight (blue) */
  --danger:    #ef4444;   /* danger callouts */
  --warning:   #f59e0b;   /* warning callouts */
  --caution:   #f97316;   /* caution callouts */
  --note:      #3b82f6;   /* note callouts */
  --success:   #22c55e;   /* checklist pass, wizard complete */
  --text:      #e8eaf0;   /* primary text */
  --text-dim:  #7a8099;   /* secondary text */
  --text-muted:#4a5068;   /* tertiary text, labels */
  --nav-w:     280px;     /* sidebar width */
  --radius:    10px;      /* border radius */
}
```

## Light Theme Override

Replace `:root` with light palette values:

```css
:root {
  --bg:        #f8f9fa;
  --surface:   #ffffff;
  --surface2:  #f1f3f5;
  --border:    #dee2e6;
  --accent:    #c47a00;
  --accent2:   #1d4ed8;
  --danger:    #dc2626;
  --warning:   #d97706;
  --caution:   #ea580c;
  --note:      #1d4ed8;
  --success:   #16a34a;
  --text:      #111827;
  --text-dim:  #4b5563;
  --text-muted:#9ca3af;
}
```

## Typography

```css
--font-head: 'Syne', sans-serif;
--font-mono: 'JetBrains Mono', monospace;
--font-body: 'Inter', sans-serif;
```

Google Fonts CDN inclusion required in document head.

## Component Colour Map

| Component | Colour token |
|---|---|
| Danger banner | `--danger` |
| Warning banner | `--warning` |
| Caution banner | `--caution` |
| Note banner | `--note` |
| Procedure wizard | `--accent` |
| Checklist progress | `--success` |
| Maintenance — high priority | `--danger` |
| Maintenance — medium priority | `--warning` |
| Maintenance — low priority | `--success` |
| Fault finder symptom label | `--warning` |
| Fault finder fix label | `--success` |

## Sidebar Width

Default `280px`; increase to `320px` for dense manuals; collapse to `0` for mobile with hamburger toggle.

## Responsive Breakpoint

At `max-width: 768px`: sidebar stacks vertically, padding adjusts, fault finder grid becomes single column.
