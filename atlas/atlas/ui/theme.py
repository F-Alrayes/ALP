"""Custom CSS — "Paper Console": the console layout in the ledger palette.

Build 31 tightens the whole system around a small token contract:

* type — a compact scale on a 13-14px body, mono display voice kept, an
  11px floor with per-size tracking (small caps track out, display tracks in);
* space — an 8px vertical rhythm (Streamlit's 16px block gap halved), compact
  cards/stats/chat, a slim page head;
* shape — three radii (--r-sm 6 / --r-md 10 / --r-lg 16);
* material — three glass tiers (surface / control / overlay) plus the
  evergreen fill, all tokenised so dark mode is a token swap, not a re-paint;
* motion — one ease (--ease), 120-260ms, transform/opacity only, hover gated
  behind (hover:hover), reduced-motion variants throughout.

Every class contract from the pages (.card, .stat, .badge, .chatlog, .kv,
.page-head, .chart-head, .flash, .trace, .timeline, …) is kept.
"""

from __future__ import annotations

import base64
from pathlib import Path

import streamlit as st

from ..config import PALETTE, STATUS_COLORS

# (family, style, weight, file) — latin subsets shared with the preview.
_FONT_DIR = Path(__file__).resolve().parents[2] / "preview" / "fonts"
_FACES = [
    ("Instrument Sans", "normal", "400 700", "instrument-sans-latin-wght-normal.woff2"),
    ("Instrument Sans", "italic", "400 700", "instrument-sans-latin-wght-italic.woff2"),
    ("IBM Plex Mono", "normal", "400", "ibm-plex-mono-latin-400-normal.woff2"),
    ("IBM Plex Mono", "normal", "600", "ibm-plex-mono-latin-600-normal.woff2"),
]


def _font_css() -> str:
    rules = []
    for family, style, weight, fname in _FACES:
        path = _FONT_DIR / fname
        if not path.is_file():
            continue
        blob = base64.b64encode(path.read_bytes()).decode()
        rules.append(
            f"@font-face{{font-family:'{family}';font-style:{style};"
            f"font-weight:{weight};font-display:swap;"
            f"src:url(data:font/woff2;base64,{blob}) format('woff2');}}"
        )
    return "\n".join(rules)


_CSS_TEMPLATE = """
<style>
%(fonts)s
:root {
  --ground: %(cream_100)s;
  --surface: %(cream_200)s;
  --panel-deep: %(green_800)s;
  --rail: %(green_900)s;
  --line: %(cream_300)s;
  --line-soft: #EFE8D5;
  --ink: %(ink)s;
  --muted: %(muted)s;
  --accent: #A8820F;                 /* interactive chrome (gold) */
  --accent-strong: %(green_700)s;    /* filled actions */
  --accent-tint: %(green_100)s;
  --amber: %(gold_600)s;
  --danger: %(danger)s;
  --warn: %(warn)s;
  --ok: %(ok)s;
  --warn-text: #7F5410;              /* text-weight tones (AA on cream) */
  --ok-text: #0E6E4B;
  --status-pending: #8A5A0E;
  --status-acknowledged: #0F7A52;
  --status-in_progress: #83660A;
  --status-completed: #0F7A52;
  --status-escalated: #BE3E2F;
  --sans: "Instrument Sans", ui-sans-serif, system-ui, -apple-system, sans-serif;
  --mono: "IBM Plex Mono", ui-monospace, SFMono-Regular, Menlo, monospace;
  --ease: cubic-bezier(.23,1,.32,1);
  /* shape */
  --r-sm: 6px; --r-md: 10px; --r-lg: 16px; --r: var(--r-lg);
  /* type floor */
  --fs-2xs: .6875rem;                /* 11px — nothing sits below this */
  /* materials: surface (panels) / control (widgets) / overlay (menus) */
  --glass: rgba(255,253,246,.42);
  --glass-control: rgba(255,253,246,.55);
  --glass-control-hover: rgba(255,253,246,.75);
  --glass-overlay: rgba(255,253,246,.84);
  --glass-blur: blur(24px) saturate(1.5);
  --blur-control: blur(12px) saturate(1.4);
  --blur-overlay: blur(20px) saturate(1.4);
  --fill-strong: rgba(20,56,42,.88);
  --edge: rgba(255,255,255,.6);
  --glass-edge: var(--edge);
  --edge-hover: rgba(168,130,15,.45);
  --edge-inverse: rgba(255,255,255,.26);
  --hover-tint: rgba(168,130,15,.08);
  --ring: 0 0 0 3px rgba(168,130,15,.35);
  --sheen-line: inset 0 1px 0 rgba(255,255,255,.7);
  --shadow-control: var(--sheen-line), 0 2px 6px -4px rgba(27,53,40,.35);
  --glass-shadow: var(--sheen-line), 0 14px 34px -22px rgba(27,53,40,.4);
  --shadow-overlay: var(--sheen-line), 0 18px 40px -24px rgba(27,53,40,.5);
  --shadow-fill: inset 0 1px 0 rgba(255,255,255,.22),
                 0 8px 18px -12px rgba(27,53,40,.6);
  --shadow-hover: var(--sheen-line), 0 8px 20px -12px rgba(27,53,40,.5);
  --fill-strong-hover: rgba(20,56,42,.97);
  /* the visible light-catch that makes a panel read as glass on flat paper */
  --glass-sheen: linear-gradient(165deg,
                  rgba(255,255,255,.6) 0%%, rgba(255,255,255,.16) 34%%,
                  rgba(255,253,246,0) 60%%);
}

html, body, [class*="css"], .stApp { font-family: var(--sans); }
body { background: var(--ground); transition: background-color 220ms ease; }
.stApp {
  background:
    radial-gradient(52rem 36rem at 12%% -8%%, rgba(168,130,15,.15), transparent 62%%),
    radial-gradient(64rem 44rem at 108%% 22%%, rgba(18,138,94,.13), transparent 65%%),
    radial-gradient(48rem 42rem at 60%% 118%%, rgba(168,130,15,.11), transparent 60%%);
  background-attachment: fixed;
  color: var(--ink);
}
.block-container { max-width: 1320px; padding: .75rem 3rem 2rem; }
section.stMain { overflow-x: clip; }
[data-testid="stHeader"] { background: transparent; }
[data-testid="stDecoration"] { display: none; }
/* zero-height style/toggle containers must not spend a flex gap */
.stMain [data-testid="stElementContainer"]:has(.stMarkdown style:only-child) {
  display: none; }
.stMain [data-testid="stLayoutWrapper"]:has(> .st-key-theme_toggle) {
  display: contents; }
.stMain [data-testid="stElementContainer"]:has(> iframe[height="0"]) {
  display: none; }

/* Display voice: the terminal speaks mono, quietly. */
h1, h2, h3, h4,
[data-testid="stMarkdownContainer"] h1, [data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3, [data-testid="stHeading"] h1,
[data-testid="stHeading"] h2, [data-testid="stHeading"] h3 {
  font-family: var(--mono) !important; color: var(--ink);
  font-weight: 600;
}
[data-testid="stMarkdownContainer"] .page-head h1 {
  font-size: 1.05rem; line-height: 1.25; letter-spacing: -0.01em;
  padding: 0; margin: 0; }
[data-testid="stMarkdownContainer"] h2, [data-testid="stHeading"] h2 {
  font-size: .8rem; text-transform: uppercase; letter-spacing: .06em;
  color: var(--muted); padding: 12px 0 0; margin: 0; }
[data-testid="stMarkdownContainer"] h3, [data-testid="stHeading"] h3 {
  font-size: .875rem; padding: 4px 0 0; margin: 0; }
[data-testid="stMarkdownContainer"] h4, [data-testid="stHeading"] h4 {
  font-family: var(--mono) !important; font-weight: 600;
  font-size: .7rem; text-transform: uppercase; letter-spacing: .07em;
  color: var(--muted); padding: 8px 0 0; margin: 0; }
[data-testid="stMarkdownContainer"] h4::before {
  content: "▮ "; color: var(--accent); }
/* Streamlit tucks a -1rem margin under every markdown container and lets
   the final paragraph's own 1rem margin cancel it. Custom divs carry no
   margin, so on the tightened 8px rhythm the next row paints over them.
   Neutralise both sides so each block owns exactly its height. */
.stMain [data-testid="stMarkdownContainer"] { margin-bottom: 0 !important; }
.stMain [data-testid="stMarkdownContainer"] > p:last-child,
.stMain [data-testid="stMarkdownContainer"] > div:last-child,
.stMain [data-testid="stMarkdownContainer"] > ul:last-child,
.stMain [data-testid="stMarkdownContainer"] > table:last-child {
  margin-bottom: 0 !important; }
[data-testid="stHeaderActionElements"] { display: none; }
p, li, .stMarkdown { color: var(--ink); }
.stMain [data-testid="stMarkdownContainer"] p { font-size: .875rem; }
.stMain [data-testid="stMarkdownContainer"],
.stMain [data-testid="stMarkdownContainer"] :is(p, li, span),
[data-testid="stWidgetLabel"] p, [data-testid="stCaptionContainer"] p,
[data-testid="stAlert"] p { font-family: var(--sans); }
.mono { font-family: var(--mono); font-variant-numeric: tabular-nums; }
.subtle { color: var(--muted); font-size: .8rem; }
.stMain a { color: var(--amber);
  text-decoration-color: color-mix(in srgb, var(--amber) 40%%, transparent); }
.stMain a:hover { color: var(--accent); }

::selection { background: #F7EFD5; color: var(--ink); }
input, textarea { caret-color: var(--accent); }
* { scrollbar-width: thin; scrollbar-color: var(--line) transparent; }
hr { border-color: var(--line-soft); }

/* ---------- one focus ring for everything ---------- */
:focus-visible { outline: none; }
.stButton button:focus-visible, [class*="st-key-chip_"] button:focus-visible,
.st-key-theme_toggle button:focus-visible, [data-testid="stTab"]:focus-visible,
[data-testid="stChatInputSubmitButton"]:focus-visible {
  box-shadow: var(--ring), var(--sheen-line) !important;
  border-color: var(--accent) !important;
}
.stTextInput input:focus-visible, .stTextArea textarea:focus-visible,
.stNumberInput input:focus-visible, .stChatInput textarea:focus-visible {
  outline: none; }
[data-testid="stTextInputRootElement"]:focus-within,
[data-testid="stNumberInputContainer"]:focus-within,
.stTextArea [data-baseweb="textarea"]:focus-within,
[data-testid="stSelectbox"] > div:focus-within,
.stChatInput > div:focus-within {
  box-shadow: var(--ring), var(--sheen-line) !important;
  border-color: var(--accent) !important;
  transition: border-color 150ms ease, box-shadow 150ms ease;
}

/* Streamlit keeps columns on one row at every width; below the bento's
   comfortable minimum, let rows wrap so tiles keep their measure.
   (The top bar opts back out further down — it must stay one line.) */
@media (max-width: 1180px) {
  [data-testid="stHorizontalBlock"]:not(.st-key-topbar [data-testid="stHorizontalBlock"]) {
    flex-wrap: wrap !important; }
  [data-testid="stHorizontalBlock"]:not(.st-key-topbar [data-testid="stHorizontalBlock"])
    > [data-testid="stColumn"] {
    flex: 1 1 240px !important; min-width: 240px !important; }
}

/* the theme toggle: a round glass button pinned to the corner */
.st-key-theme_toggle { position: fixed; top: 10px; right: 18px;
  z-index: 1000001; width: auto !important; }
.st-key-theme_toggle .stButton button {
  width: 38px; height: 38px; min-height: 38px; border-radius: 50%%;
  padding: 0; justify-content: center; }
.st-key-theme_toggle .stButton button > div { justify-content: center; }
.st-key-theme_toggle .stButton button [data-testid="stMarkdownContainer"] {
  position: absolute; width: 1px; height: 1px; overflow: hidden;
  clip: rect(0 0 0 0); white-space: nowrap; }
.st-key-theme_toggle .stButton button [data-testid="stIconMaterial"] {
  padding: 0; margin: 0 !important; font-size: 1.05rem;
  transition: transform 200ms var(--ease); }
@media (hover: hover) and (pointer: fine) {
  .st-key-theme_toggle .stButton button:hover [data-testid="stIconMaterial"] {
    transform: rotate(-25deg); }
}
.st-key-theme_toggle .stButton button:active { transform: scale(.92); }

/* ---------- icon optical alignment ---------- */
/* Material glyph spans inherit the label's tall line box and ride high or
   low against caps text; pin every glyph to a 1-line box on the flex
   centreline, then nudge the two contexts the eye still catches. */
[data-testid="stIconMaterial"] { line-height: 1; align-self: center; }
.stButton button > div { display: flex; align-items: center; }
[class*="st-key-chip_"] [data-testid="stIconMaterial"] {
  position: relative; top: .5px; }
.st-key-topbar .stButton button [data-testid="stIconMaterial"] {
  position: relative; top: .5px; }
.st-key-topbar .stMarkdownBadge { vertical-align: middle;
  margin-left: .3rem; transform: translateY(-1px); }

/* live status dot (agent running / stopped) */
.livedot { display: inline-block; width: 9px; height: 9px; border-radius: 50%%;
  background: var(--muted); vertical-align: 1px; margin-left: 2px; }
.livedot.on { background: var(--ok); box-shadow: 0 0 0 3px rgba(18,138,94,.16); }

/* ---------- vertical rhythm: halve Streamlit's stack gap ---------- */
.stMain [data-testid="stVerticalBlock"] { gap: 8px; }
.stMain [data-testid="stHorizontalBlock"] { gap: 12px; }
[class*="st-key-demo_"], [class*="st-key-card_"], .st-key-ask_draft { gap: 8px; }

/* ---------- the top bar: a floating glass island ---------- */
.st-key-topbar { position: sticky; top: 8px; z-index: 999990;
  background: var(--glass-overlay); border: 1px solid var(--edge);
  border-radius: 999px; padding: 5px 12px 5px 18px; margin: 0 46px 6px 0;
  backdrop-filter: var(--blur-overlay); -webkit-backdrop-filter: var(--blur-overlay);
  box-shadow: var(--shadow-overlay);
}
.st-key-topbar [data-testid="stHorizontalBlock"] {
  flex-wrap: nowrap !important; gap: 2px; align-items: center; }
.st-key-topbar [data-testid="stColumn"] {
  flex: 0 0 auto !important; width: auto !important; min-width: 0 !important; }
.st-key-topbar [data-testid="stColumn"]:last-child {
  flex: 0 1 250px !important; margin-left: auto; min-width: 150px !important; }
.st-key-topbar .stButton button {
  background: transparent !important; border: none !important;
  box-shadow: none !important;
  backdrop-filter: none; -webkit-backdrop-filter: none;
  min-height: 34px; padding: .3rem .7rem; border-radius: 999px;
  position: relative; white-space: nowrap;
  font-family: var(--mono); font-size: .68rem; text-transform: uppercase;
  letter-spacing: .08em; color: var(--muted);
  transition: background-color 120ms ease, color 120ms ease,
              transform 160ms var(--ease);
}
.st-key-topbar .stButton button p {
  font-family: var(--mono) !important; font-size: .68rem;
  letter-spacing: .08em; text-transform: uppercase; color: inherit; }
.st-key-topbar .stButton button [data-testid="stIconMaterial"] {
  font-size: .9rem; transition: transform 160ms var(--ease); }
@media (hover: hover) and (pointer: fine) {
  .st-key-topbar .stButton button:hover {
    color: var(--ink);
    background: var(--glass-sheen), var(--hover-tint) !important;
    transform: none; }
  .st-key-topbar .stButton button:hover [data-testid="stIconMaterial"] {
    transform: translateY(-1px); }
}
.st-key-topbar .stButton button:active { transform: scale(.95); }
.st-key-topbar .stButton button[kind="primary"],
.st-key-topbar .stButton button[kind="primary"] p {
  color: var(--accent) !important;
  -webkit-text-fill-color: var(--accent) !important;
}
.st-key-topbar .stButton button[kind="primary"] {
  background: var(--hover-tint) !important; box-shadow: none !important;
  backdrop-filter: none; -webkit-backdrop-filter: none;
}
.st-key-topbar .stButton button[kind="primary"]::after {
  content: ""; position: absolute; left: .85rem; right: .85rem; bottom: 2px;
  height: 2px; border-radius: 2px; background: var(--accent);
  animation: growx 200ms var(--ease) both; transform-origin: left center; }
/* the unread count rides the nav item as a real badge */
.st-key-topbar .stMarkdownBadge {
  background: var(--accent) !important; color: #122019 !important;
  -webkit-text-fill-color: #122019 !important;
  font: 600 11px/18px var(--mono) !important;
  min-width: 18px; height: 18px; padding: 0 5px; border-radius: 999px;
  display: inline-block; text-align: center;
}
@media (prefers-reduced-motion: no-preference) {
  .st-key-topbar .stMarkdownBadge { animation: badgein .22s var(--ease) both; }
}
@keyframes badgein { from { transform: scale(.6); opacity: 0; } }
.st-key-topbar [data-testid="stSelectbox"] > div {
  border-radius: 999px !important; }
@media (max-width: 1220px) {
  .atlas-brand .build { display: none; }
  .st-key-topbar .stButton button { padding: .3rem .5rem; }
  .st-key-topbar { margin-right: 0; padding-right: 56px; }
}
.st-key-topbar [data-testid="stSelectbox"] > div > div { min-height: 32px; }
.st-key-topbar [data-testid="stWidgetLabel"] { display: none; }

.atlas-brand { font-family: var(--mono); display: flex; align-items: baseline;
  gap: .5rem; white-space: nowrap; padding-right: .3rem; }
.atlas-brand .name { font-size: .92rem; font-weight: 600; letter-spacing: .16em;
  color: var(--ink); }
.atlas-brand .name::after { content: "_"; color: var(--accent); font-weight: 600; }
@media (prefers-reduced-motion: no-preference) {
  .atlas-brand .name::after { animation: caret 1.1s steps(1) infinite; }
}
@keyframes caret { 50%% { opacity: 0; } }
.atlas-brand .build { font-size: .68rem; color: var(--muted);
  letter-spacing: .08em; text-transform: uppercase; }

/* ---------- page head: one quiet line ---------- */
.page-head { display: flex; align-items: baseline; gap: .7rem;
  padding: 2px 0 8px; margin-bottom: 2px;
  border-bottom: 1px solid var(--line-soft); }
.page-head h1 { margin: 0; }
.page-head .sub { color: var(--muted); font-size: .78rem; margin: 0; }

/* ---------- panels ---------- */
.card {
  background: var(--glass-sheen), var(--glass);
  border: 1px solid var(--edge); border-radius: 12px;
  backdrop-filter: var(--glass-blur); -webkit-backdrop-filter: var(--glass-blur);
  box-shadow: var(--glass-shadow);
  padding: 10px 14px; margin-bottom: 0;
  transition: border-color 150ms ease;
}
.card.accent { border-left: 2px solid var(--accent); }
.card-title { font-weight: 600; font-size: .9rem; line-height: 1.3; color: var(--ink); }
.card-meta { font-size: .76rem; line-height: 1.45; color: var(--muted); margin-top: 1px; }
.card-body { font-size: .84rem; margin-top: 4px; color: var(--ink);
  white-space: pre-line; }
.card-chips { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 4px; }

/* a list row is one hover unit: card and its action light together */
@media (hover: hover) and (pointer: fine) {
  [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"] .card):has(.stButton):hover .card {
    border-color: var(--edge-hover); }
  [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"] .card):hover .stButton button {
    border-color: var(--accent); background: var(--glass-control-hover); }
  .card:hover { border-color: var(--edge-hover); }
}

[class*="st-key-demo_"], [class*="st-key-card_"], .st-key-ask_draft {
  background: var(--glass-sheen), var(--glass);
  border: 1px solid var(--edge) !important;
  backdrop-filter: var(--glass-blur); -webkit-backdrop-filter: var(--glass-blur);
  box-shadow: var(--glass-shadow);
  border-radius: var(--r-lg) !important; padding: 12px 16px !important;
  transition: border-color 150ms ease;
}
@media (hover: hover) and (pointer: fine) {
  [class*="st-key-card_"]:hover { border-color: var(--edge-hover); }
}

/* ---------- stat tiles ---------- */
.stat {
  background: var(--glass-sheen), var(--glass);
  border: 1px solid var(--edge);
  backdrop-filter: var(--glass-blur); -webkit-backdrop-filter: var(--glass-blur);
  box-shadow: var(--glass-shadow);
  border-left: 3px solid var(--accent); border-radius: var(--r-lg);
  padding: 8px 12px; min-height: 64px;
  display: flex; flex-direction: column; justify-content: center;
}
.stat .label { font-family: var(--mono); font-size: var(--fs-2xs);
  text-transform: uppercase; letter-spacing: .1em; color: var(--muted); }
.stat .value { font-family: var(--mono); font-size: 1.5rem; font-weight: 600;
  color: var(--ink); line-height: 1.1; letter-spacing: -0.01em;
  font-variant-numeric: tabular-nums; white-space: nowrap; }
.stat .delta { font-size: .74rem; color: var(--muted); }
.stat.bare { background: none; border: none; box-shadow: none;
  backdrop-filter: none; -webkit-backdrop-filter: none;
  min-height: 0; padding: .25rem 0 .35rem .6rem; border-radius: 0;
  border-left: 2px solid var(--line); }
.stat.bare .value { font-size: 1.5rem; }
.stat.bare.ok { border-left-color: var(--ok); }
.stat.bare.warn { border-left-color: var(--warn); }
.stat.bare.danger { border-left-color: var(--danger); }
.stat.ok .label { color: var(--ok-text); }
.stat.warn .label { color: var(--warn-text); }
.donut-cap { text-align: center; font-size: .74rem; color: var(--muted);
  margin-top: -0.35rem; }
.stat.warn  { border-left-color: var(--warn); }  .stat.warn .value { color: var(--warn-text); }
.stat.danger{ border-left-color: var(--danger);} .stat.danger .value { color: var(--danger); }
.stat.ok    { border-left-color: var(--ok); }    .stat.ok .value { color: var(--ok-text); }

/* ---------- badges ---------- */
.badge {
  display: inline-block; font-family: var(--mono); font-size: var(--fs-2xs);
  text-transform: uppercase; letter-spacing: .08em; padding: 1px 6px;
  border-radius: var(--r-sm); border: 1px solid;
  border-color: color-mix(in srgb, currentColor 32%%, transparent);
  background: var(--glass-control);
  backdrop-filter: blur(6px); -webkit-backdrop-filter: blur(6px);
  box-shadow: inset 0 1px 0 rgba(255,255,255,.5);
  vertical-align: middle;
}
.badge.pending      { color: var(--status-pending); }
.badge.acknowledged { color: var(--status-acknowledged); }
.badge.in_progress  { color: var(--status-in_progress); }
.badge.completed    { color: var(--status-completed); }
.badge.escalated    { color: var(--status-escalated); }
.badge.role  { color: var(--ok-text); }
.badge.gold  { color: var(--amber); }
.badge.muted { color: var(--muted); border-color: var(--line); }
.badge.ooo   { color: var(--danger); }

/* ---------- buttons ---------- */
.stButton button {
  border-radius: var(--r-md); border: 1px solid var(--edge); font-weight: 500;
  background: var(--glass-control); color: var(--ink);
  min-height: 32px; padding: 3px 12px;
  backdrop-filter: var(--blur-control); -webkit-backdrop-filter: var(--blur-control);
  box-shadow: var(--shadow-control);
  transition: transform 160ms var(--ease), border-color 150ms ease,
              background-color 150ms ease, box-shadow 150ms ease;
}
.stButton button p { font: inherit; letter-spacing: inherit; color: inherit;
  font-size: 13px; line-height: 20px; font-weight: 500; }
.stButton button [data-testid="stIconMaterial"] { font-size: 1rem; }
@media (hover: hover) and (pointer: fine) {
  .stButton button:hover { border-color: var(--edge-hover);
    background: var(--glass-sheen), var(--glass-control-hover);
    box-shadow: var(--shadow-hover); }
}
.stButton button:active { transform: scale(.97); }
.stButton button[kind="primary"],
[data-testid="stBaseButton-primary"] {
  background: var(--fill-strong); border-color: var(--edge-inverse);
  backdrop-filter: blur(16px) saturate(1.35);
  -webkit-backdrop-filter: blur(16px) saturate(1.35);
  box-shadow: var(--shadow-fill);
}
.stButton button[kind="primary"], .stButton button[kind="primary"] *,
[data-testid="stBaseButton-primary"], [data-testid="stBaseButton-primary"] * {
  color: #F3EEE0 !important; -webkit-text-fill-color: #F3EEE0 !important;
}
@media (hover: hover) and (pointer: fine) {
  .stButton button[kind="primary"]:hover,
  [data-testid="stBaseButton-primary"]:hover {
    background: var(--glass-sheen), var(--fill-strong-hover);
    box-shadow: inset 0 1px 0 rgba(255,255,255,.3),
                0 10px 20px -12px rgba(27,53,40,.75);
  }
}
.stButton button:disabled {
  opacity: .55; background: transparent !important;
  border-color: var(--line) !important; box-shadow: none;
  backdrop-filter: none; -webkit-backdrop-filter: none;
  cursor: not-allowed; transform: none;
}
.stButton button:disabled, .stButton button:disabled p,
.stButton button:disabled [data-testid="stIconMaterial"] {
  color: var(--muted) !important; -webkit-text-fill-color: var(--muted) !important;
}
.stButton button:disabled [data-testid="stIconMaterial"] { background: none !important; }
@media (prefers-reduced-motion: reduce) {
  .stButton button { transition: border-color 150ms ease,
    background-color 150ms ease, box-shadow 150ms ease; }
  .stButton button:active { transform: none; }
}

/* quiet tertiary controls: back links and undo */
.st-key-back_request button, .st-key-back_person button,
.st-key-back_process button, .st-key-ask_undo button {
  background: transparent !important; border: none !important;
  box-shadow: none !important; backdrop-filter: none;
  -webkit-backdrop-filter: none; padding: 0 2px; min-height: 24px;
  color: var(--muted); font-family: var(--mono); font-size: .68rem;
  text-transform: uppercase; letter-spacing: .09em;
}
.st-key-back_request button p, .st-key-back_person button p,
.st-key-back_process button p, .st-key-ask_undo button p {
  font-family: var(--mono) !important; font-size: .68rem;
  letter-spacing: .09em; text-transform: uppercase; }
.st-key-back_request button [data-testid="stIconMaterial"],
.st-key-back_person button [data-testid="stIconMaterial"],
.st-key-back_process button [data-testid="stIconMaterial"] {
  transition: transform 180ms var(--ease); }
@media (hover: hover) and (pointer: fine) {
  .st-key-back_request button:hover, .st-key-back_person button:hover,
  .st-key-back_process button:hover, .st-key-ask_undo button:hover {
    color: var(--accent); }
  .st-key-back_request button:hover [data-testid="stIconMaterial"],
  .st-key-back_person button:hover [data-testid="stIconMaterial"],
  .st-key-back_process button:hover [data-testid="stIconMaterial"] {
    transform: translateX(-3px); }
}

/* the quick-advance chips on the demo clock */
.st-key-adv1 button, .st-key-adv24 button, .st-key-adv48 button {
  border-radius: 999px; min-height: 26px; padding: 1px 10px;
  font-family: var(--mono); }
.st-key-adv1 button p, .st-key-adv24 button p, .st-key-adv48 button p {
  font-family: var(--mono) !important; font-size: .72rem; }
/* the destructive confirm wears the danger fill */
.st-key-reset_yes button { background: rgba(190,62,47,.9) !important;
  border-color: rgba(255,255,255,.28) !important; }
.st-key-demo_reset [data-testid="stAlert"] {
  animation: risein .2s var(--ease) both; }

/* ---------- inputs, tabs, tables ---------- */
/* one glass box per field: the root carries the material, internals are clear */
.stMain [data-testid="stWidgetLabel"] { min-height: 0; margin-bottom: 2px; }
.stMain [data-testid="stWidgetLabel"] p, .stTextInput label, .stTextArea label,
.stSelectbox label, .stNumberInput label {
  font-family: var(--mono) !important; font-size: var(--fs-2xs);
  line-height: 16px; text-transform: uppercase; letter-spacing: .08em;
  color: var(--muted) !important;
}
.stTextInput div, .stTextArea div, .stNumberInput div,
.stNumberInput button, .stTextInput input, .stTextArea textarea,
.stNumberInput input, [data-testid="stSelectbox"] > div div,
[data-testid="stSelectbox"] input {
  background-color: transparent !important; border-color: transparent;
  color: var(--ink); -webkit-text-fill-color: var(--ink);
}
[data-testid="stTextInputRootElement"], [data-testid="stNumberInputContainer"],
.stTextArea [data-baseweb="textarea"], [data-testid="stSelectbox"] > div {
  background: var(--glass-control) !important;
  border: 1px solid var(--edge) !important;
  border-radius: var(--r-md) !important;
  backdrop-filter: var(--blur-control);
  -webkit-backdrop-filter: var(--blur-control);
  box-shadow: var(--shadow-control) !important;
}
.stMain .stTextInput input, .stMain .stNumberInput input {
  padding: 6px 10px; font-size: .8125rem; }
.stTextArea textarea { font-size: .8125rem; }
[data-testid="stSelectbox"] input, [data-baseweb="select"] div { font-size: .8125rem; }
.stMain [data-testid="stSelectbox"] > div > div { min-height: 32px; }
.stTextArea textarea::placeholder, .stTextInput input::placeholder {
  font-family: var(--mono); color: var(--muted); }
[data-testid="stNumberInputStepDown"], [data-testid="stNumberInputStepUp"] {
  border-left: 1px solid var(--line-soft); width: 30px; border-radius: 8px; }
.stNumberInput button { color: var(--muted);
  transition: background-color 150ms ease, color 150ms ease; }
@media (hover: hover) and (pointer: fine) {
  .stNumberInput button:hover { background-color: var(--hover-tint) !important;
    color: var(--ink) !important; }
  .stNumberInput button:hover svg { fill: var(--ink); }
}
[data-testid="stSelectbox"] svg { fill: var(--muted); color: var(--muted);
  transition: fill 150ms var(--ease); }
@media (hover: hover) and (pointer: fine) {
  [data-testid="stSelectbox"] > div:hover svg { fill: var(--ink); }
}
[role="listbox"], [data-baseweb="popover"] {
  color: var(--ink); background: var(--glass-overlay);
  backdrop-filter: var(--blur-overlay); -webkit-backdrop-filter: var(--blur-overlay);
  border: 1px solid var(--edge); border-radius: var(--r-md);
  box-shadow: var(--shadow-overlay), 0 18px 40px -24px rgba(27,53,40,.5);
}
[role="option"] { transition: background-color 100ms ease; }
@media (prefers-reduced-motion: no-preference) {
  [data-testid="stSelectboxVirtualDropdown"], [data-baseweb="popover"] {
    transform-origin: top center; animation: popin 160ms var(--ease) both; }
}
@media (prefers-reduced-motion: reduce) {
  [data-testid="stSelectboxVirtualDropdown"], [data-baseweb="popover"] {
    animation: fadein 120ms ease both; }
}
@keyframes popin { from { opacity: 0; transform: translateY(-4px) scale(.97); } }
@keyframes fadein { from { opacity: 0; } }

/* tabs: quiet mono labels, one animated gold indicator */
.stTabs [role="tablist"] { gap: .2rem; }
.stTabs [role="tablist"]::after { background: var(--line-soft) !important;
  height: 1px; }
.stTabs [data-testid="stTab"] {
  position: relative; height: auto; min-height: 32px; padding: .35rem .7rem;
  font-family: var(--mono); font-size: .72rem; text-transform: uppercase;
  letter-spacing: .08em; color: var(--muted);
  border-radius: var(--r-sm) var(--r-sm) 0 0;
  transition: color 140ms ease, background-color 150ms var(--ease);
}
.stTabs [data-testid="stTab"] p { font: inherit; letter-spacing: inherit;
  color: inherit !important; }
@media (hover: hover) and (pointer: fine) {
  .stTabs [data-testid="stTab"]:hover { color: var(--ink) !important;
    background: var(--hover-tint); }
}
.stTabs [data-testid="stTab"][aria-selected="true"] { color: var(--ink) !important; }
.stTabs [data-testid="stTab"]::after { content: ""; position: absolute;
  left: .7rem; right: .7rem; bottom: -1px; height: 2px; border-radius: 2px;
  background: var(--accent); transform: scaleX(0);
  transition: transform 180ms var(--ease); }
.stTabs [data-testid="stTab"][aria-selected="true"]::after { transform: scaleX(1); }
.stTabs [role="tablist"] > div:not([role="tab"]):not([data-testid="stTab"]) {
  background: transparent !important; }
.stTabs [role="tabpanel"] { padding-top: 8px; }
@media (prefers-reduced-motion: no-preference) {
  [data-testid="stTabPanel"] { animation: fadein 140ms var(--ease) both; }
}

.stExpander { border: 1px solid var(--edge) !important;
  border-radius: var(--r-lg) !important;
  background: var(--glass); backdrop-filter: var(--glass-blur);
  -webkit-backdrop-filter: var(--glass-blur); }
[data-testid="stExpander"] details { border: 0 !important; }
.stExpander summary { min-height: 32px; padding: 2px 10px;
  border-radius: var(--r-md);
  transition: color 120ms ease, background-color 120ms ease; }
.stExpander summary, .stExpander summary p, .stExpander summary span {
  font-size: .875rem; }
@media (hover: hover) and (pointer: fine) {
  .stExpander summary:hover { color: var(--accent);
    background: var(--hover-tint) !important; }
}
[data-testid="stExpanderDetails"] { padding: 8px 12px 12px; }
@media (prefers-reduced-motion: no-preference) {
  [data-testid="stExpanderDetails"] { animation: expin 180ms var(--ease) both; }
}
@keyframes expin { from { opacity: 0; transform: translateY(-4px); } }
[data-testid="stMetricValue"] { color: var(--ink); font-family: var(--mono); }
[data-testid="stDataFrame"] {
  border: 1px solid var(--edge); border-radius: var(--r-lg);
  background: var(--glass); backdrop-filter: var(--glass-blur);
  -webkit-backdrop-filter: var(--glass-blur); box-shadow: var(--glass-shadow);
}

/* the tokenised table (bottlenecks) — both modes derive from one rule */
.dtable { width: 100%%; border-collapse: collapse; font-size: .84rem; }
.dtable, .dtable tr, .dtable th, .dtable td {
  border-left: 0 !important; border-right: 0 !important; border-top: 0 !important;
  background: transparent !important; }
.dtable thead th { font-family: var(--mono); font-size: var(--fs-2xs);
  letter-spacing: .1em; text-transform: uppercase; color: var(--muted);
  text-align: left; font-weight: 500; padding: .3rem .6rem;
  border-bottom: 1px solid var(--line-soft); white-space: nowrap; }
.dtable tbody td { color: var(--ink); padding: .35rem .6rem;
  border-bottom: 1px solid var(--line-soft);
  font-variant-numeric: tabular-nums; }
.dtable tbody tr:last-child td { border-bottom: 0; }
.dtable tbody tr { transition: background-color 120ms ease; }
@media (hover: hover) and (pointer: fine) {
  .dtable tbody tr:hover { background: var(--hover-tint); }
}
.dtable .num { text-align: right; font-family: var(--mono); font-size: .78rem; }
.dtable .loadbar { display: inline-block; width: 72px; height: 6px;
  border-radius: 999px; background: rgba(27,53,40,.08);
  vertical-align: middle; margin-right: 7px; overflow: hidden; }
.dtable .loadbar i { display: block; height: 100%%; border-radius: inherit;
  background: linear-gradient(90deg, #A8820F, #C29B22); }

[data-testid="stAlert"] {
  background: var(--glass) !important; border: 1px solid var(--edge);
  border-left: 2px solid var(--amber);
  border-radius: var(--r-md); backdrop-filter: var(--glass-blur);
  -webkit-backdrop-filter: var(--glass-blur); box-shadow: var(--glass-shadow);
}
[data-testid="stAlertContainer"], [data-testid="stAlertContainer"] > div {
  background: transparent !important; border-radius: inherit;
  color: var(--ink) !important; }
[data-testid="stAlertContainer"] { padding: 8px 12px; }
[data-testid="stAlert"] p { font-size: .8125rem; color: var(--ink) !important; }
[data-testid="stAlert"]:has([data-testid="stAlertContentWarning"]) {
  border-left-color: var(--warn); }
[data-testid="stAlert"]:has([data-testid="stAlertContentError"]) {
  border-left-color: var(--danger); }
[data-testid="stAlert"]:has([data-testid="stAlertContentSuccess"]) {
  border-left-color: var(--ok); }
[data-testid="stAlert"] [data-testid="stIconMaterial"],
[data-testid="stAlert"] svg { color: inherit; fill: currentColor; font-size: 16px; }

.stMain [data-testid="stCaptionContainer"] { margin-bottom: -8px; }
.stMain [data-testid="stCaptionContainer"] p { margin-bottom: 8px;
  font-size: 12px; line-height: 18px; color: var(--muted) !important; }

.empty { border: 1px dashed var(--edge); border-radius: var(--r-lg);
  padding: 16px 14px; text-align: center; color: var(--muted);
  font-size: .8125rem;
  background: var(--glass); backdrop-filter: var(--glass-blur);
  -webkit-backdrop-filter: var(--glass-blur);
  box-shadow: var(--glass-shadow); }
.empty .big { font-family: var(--mono); font-size: .875rem; color: var(--ink);
  margin-bottom: .2rem; }

.kv { font-size: .84rem; padding: .12rem 0; }
.kv .k { color: var(--muted); display: inline-block; min-width: 118px;
  font-family: var(--mono); font-size: var(--fs-2xs); text-transform: uppercase;
  letter-spacing: .08em; }

.chart-head { font-family: var(--mono); font-size: .72rem; text-transform: uppercase;
  letter-spacing: .08em; color: var(--muted); margin: 0 0 2px;
  display: flex; align-items: baseline; gap: .6rem; }
.chart-head::before { content: "▮ "; color: var(--accent); }
.chart-note { font-size: var(--fs-2xs); color: var(--muted); letter-spacing: .05em;
  margin-left: .55em; }
.chart-note::before { content: "· "; color: var(--line); }

/* ---------- the routing trace & request timeline ---------- */
.trace .step { display: grid; grid-template-columns: 118px 1fr; gap: .5rem;
  padding: .3rem 0; border-top: 1px solid var(--line-soft); font-size: .84rem; }
.trace .step:first-child { border-top: 0; }
.trace .step .label { font-family: var(--mono); font-size: var(--fs-2xs);
  text-transform: uppercase; letter-spacing: .08em; color: var(--muted); }
.trace .step.ok .label { color: var(--ok-text); }
.trace .step.fail .label { color: var(--danger); }
.trace .step.warn .label { color: var(--warn-text); }
.trace .step .detail { color: var(--ink); }

.timeline .entry { position: relative; padding: .35rem 0 .35rem .9rem;
  border-left: 2px solid var(--line-soft); font-size: .84rem; line-height: 1.45; }
.timeline .entry::before { content: ""; position: absolute; left: -5px;
  top: .75rem; width: 8px; height: 8px; border-radius: 50%%;
  background: var(--muted); box-shadow: 0 0 0 2px var(--surface); }
.timeline .entry.agent::before { background: var(--amber); }
.timeline .entry.alert::before { background: var(--danger); }
.timeline .when { font-family: var(--mono); font-size: var(--fs-2xs);
  letter-spacing: .04em; color: var(--muted);
  font-variant-numeric: tabular-nums; }
.timeline .who { color: var(--amber); }

/* Bento rows line up: a column stretches to the row's height, but the
   card's own layout wrapper keeps its natural height and leaves ragged
   bottoms. Let wrappers holding a dashboard card grow, and the card fill. */
[data-testid="stColumn"] > [data-testid="stVerticalBlock"]
  > [data-testid="stLayoutWrapper"]:has(> [class*="st-key-card_"]) {
  flex: 1 1 auto; }
[class*="st-key-card_"] { height: 100%%; }
/* Cards that end up taller than their content centre the body in the
   leftover space instead of pooling the slack at the bottom. */
.st-key-card_donut { justify-content: space-between; }
.st-key-card_kpi > [data-testid="stElementContainer"]:last-child {
  margin-block: auto; }

/* ---------- the conversation ---------- */
/* One fluid, centred column: log, draft, chips, undo and composer all share
   min(920px, full width). */
.chatlog { width: 100%%; max-width: 920px; margin-inline: auto; padding: 0; }
.chatlog, .msg .bub { font-size: .8125rem; line-height: 1.5; }
.msg { display: flex; gap: 8px; margin-bottom: 10px; }
.msg.user { justify-content: flex-end; }
.msg.user .bub { background: var(--fill-strong);
  border: 1px solid var(--edge-inverse);
  color: #F3EEE0; border-radius: 16px 16px 6px 16px; padding: 7px 12px;
  backdrop-filter: blur(16px) saturate(1.35);
  -webkit-backdrop-filter: blur(16px) saturate(1.35);
  box-shadow: var(--shadow-fill);
  max-width: 78%%; }
.msg.bot .ava { width: 24px; height: 24px; border-radius: var(--r-sm);
  background: var(--accent-strong); color: #F2F6FF; display: grid;
  place-items: center; font-family: var(--mono); font-weight: 600;
  font-size: .72rem; flex: none; margin-top: 2px; }
.msg.bot .bub { background: var(--glass); border: 1px solid var(--edge);
  backdrop-filter: var(--glass-blur); -webkit-backdrop-filter: var(--glass-blur);
  box-shadow: var(--glass-shadow);
  border-radius: 6px 16px 16px 16px; padding: 8px 12px; flex: 1; min-width: 0; }
.msg .bub p { margin: 0; }
.msg .bub p + p { margin-top: 6px; }
.msg .bub .small { font-size: .75rem; color: var(--muted); }
.chatcard { border: 1px solid var(--line); background: rgba(246,241,225,.9);
  border-radius: var(--r-md); padding: 6px 10px; margin-top: 6px; }
.cc-title { font-weight: 600; font-size: .84rem; display: block; color: var(--ink); }
.cc-meta { font-size: .75rem; color: var(--muted); display: block; margin-top: 2px; }
.chatrow { border-top: 1px solid var(--line-soft); padding: 6px 0 4px;
  display: block; }
.chatrow:first-child { border-top: none; }

.bub.typing { display: inline-flex; gap: 5px; align-items: center;
  padding: 10px 12px 8px; flex: none; }
.bub.typing span { width: 6px; height: 6px; border-radius: 50%%;
  background: var(--accent); opacity: .35; }
@media (prefers-reduced-motion: no-preference) {
  .bub.typing span { animation: atlasdots 1s var(--ease) infinite; }
  .bub.typing span:nth-child(2) { animation-delay: .15s; }
  .bub.typing span:nth-child(3) { animation-delay: .3s; }
  .chatlog .msg:nth-last-child(-n+2) { animation: msgin .24s var(--ease) both; }
}
@keyframes atlasdots { 0%%, 100%% { opacity: .35; transform: translateY(0); }
  40%% { opacity: 1; transform: translateY(-3px); } }
@keyframes msgin { from { opacity: 0; transform: translateY(6px); } }

/* chips */
[data-testid="stHorizontalBlock"]:has([class*="st-key-chip_"]) {
  max-width: 920px; margin-inline: auto; }
[class*="st-key-chip_"] .stButton button {
  border-radius: 999px !important; background: transparent !important;
  border: 1px solid var(--line) !important; font-family: var(--mono);
  font-size: var(--fs-2xs); text-transform: uppercase; letter-spacing: .07em;
  padding: .26rem .7rem; min-height: 0; color: var(--muted);
}
@media (hover: hover) and (pointer: fine) {
  [class*="st-key-chip_"] .stButton button:hover {
    color: var(--accent); border-color: var(--accent) !important;
    background: var(--glass-sheen), var(--glass-control) !important;
    backdrop-filter: var(--blur-control);
    -webkit-backdrop-filter: var(--blur-control);
    box-shadow: var(--shadow-control);
    transform: translateY(-1px);
  }
}
[class*="st-key-chip_"] .stButton button:active {
  transform: translateY(0) scale(.97); }
[class*="st-key-chip_"] .stButton button p { font-size: var(--fs-2xs);
  color: inherit !important; }

/* composer */
[data-testid="stBottom"] { background: rgba(250,246,235,.72);
  backdrop-filter: blur(14px) saturate(1.3); -webkit-backdrop-filter: blur(14px) saturate(1.3);
  border-top: 1px solid var(--edge); }
[data-testid="stBottom"] > div { background: transparent; }
[data-testid="stBottomBlockContainer"] { max-width: 1320px;
  padding-top: 6px; padding-bottom: 10px; background: transparent; }
.stChatInput { max-width: 920px; margin-inline: auto; }
.stChatInput > div { border-radius: var(--r-lg) !important;
  border: 1px solid var(--edge) !important; background: var(--glass) !important;
  backdrop-filter: var(--glass-blur); -webkit-backdrop-filter: var(--glass-blur);
  box-shadow: var(--glass-shadow) !important; }
.stChatInput textarea { background: transparent !important; color: var(--ink) !important;
  min-height: 40px; }
.stChatInput textarea::placeholder { font-family: var(--mono); color: var(--muted); }
[data-testid="stChatInputSubmitButton"] { border-radius: 999px;
  width: 30px; height: 30px; background: transparent;
  color: var(--muted) !important;
  transition: background-color 150ms var(--ease), transform 150ms var(--ease); }
[data-testid="stChatInputSubmitButton"] svg { fill: currentColor;
  width: 16px; height: 16px; }
[data-testid="stChatInputSubmitButton"]:not([disabled]) {
  background: var(--accent-strong); color: #F3EEE0 !important;
  border: 1px solid var(--edge); }
@media (hover: hover) and (pointer: fine) {
  [data-testid="stChatInputSubmitButton"]:not([disabled]):hover {
    transform: scale(1.06); }
}

/* draft card */
.st-key-ask_draft { max-width: 920px; margin-inline: auto; }
.st-key-ask_undo { max-width: 920px; margin-inline: auto; }
.draft-head { font-family: var(--mono); font-size: .8rem; text-transform: uppercase;
  letter-spacing: .06em; color: var(--ink); display: flex; align-items: center;
  gap: .6rem; margin-bottom: 2px; }
.draft-head::before { content: "▮ "; color: var(--accent); }
.draft-src { font-size: var(--fs-2xs); color: var(--amber);
  border: 1px solid color-mix(in srgb, var(--amber) 33%%, transparent);
  padding: 0 6px; border-radius: var(--r-sm); letter-spacing: .08em; }
.draft-route { margin: 0 0 4px; font-size: .84rem; }
@media (prefers-reduced-motion: no-preference) {
  .st-key-ask_draft { animation: risein 300ms var(--ease) both; }
}
@media (prefers-reduced-motion: reduce) {
  .st-key-ask_draft { animation: fadein 200ms ease both; }
}

/* ---------- toast & flash ---------- */
[data-testid="stToast"] {
  background: var(--glass-overlay) !important; color: var(--ink) !important;
  backdrop-filter: var(--blur-overlay); -webkit-backdrop-filter: var(--blur-overlay);
  border: 1px solid var(--edge) !important; border-left: 3px solid var(--accent);
  border-radius: var(--r-md) !important; padding: .7rem .85rem;
  box-shadow: var(--shadow-overlay) !important;
}
[data-testid="stToast"] [data-testid="stMarkdownContainer"] p { color: var(--ink);
  font-size: .84rem; }
[data-testid="stToast"] [data-testid="stMarkdownContainer"] p strong {
  font-family: var(--mono); font-size: .72rem; text-transform: uppercase;
  letter-spacing: .08em; color: var(--amber); }

.flash {
  position: fixed; right: 22px; bottom: 84px; z-index: 98;
  background: var(--glass-overlay); color: var(--ink);
  border: 1px solid var(--edge);
  backdrop-filter: var(--blur-overlay); -webkit-backdrop-filter: var(--blur-overlay);
  box-shadow: var(--shadow-overlay);
  border-left: 3px solid var(--ok); pointer-events: none;
  padding: .5rem .9rem; border-radius: var(--r-md); font-size: .8rem;
  font-family: var(--mono);
  animation: flashin 260ms var(--ease) both,
             flashout 220ms var(--ease) 4s forwards;
}
@keyframes flashin { from { opacity: 0; transform: translateY(8px); } }
@keyframes flashout { to { opacity: 0; transform: translateY(8px); } }
@media (prefers-reduced-motion: reduce) {
  .flash { animation: fadein 200ms ease both, flashfade 200ms ease 4s forwards; }
  @keyframes flashfade { to { opacity: 0; } }
}

/* ---------- charts grow in ---------- */
/* Bars grow from their baseline (transform-box makes the origin the bars'
   own box). Delays follow the card stagger so each chart grows as its
   card lands. */
@media (prefers-reduced-motion: no-preference) {
  .js-plotly-plot .barlayer { transform-box: fill-box; }
  .st-key-card_status .js-plotly-plot .barlayer {
    transform-origin: left center; animation: growx .55s .12s var(--ease) both; }
  .st-key-card_dept .js-plotly-plot .barlayer {
    transform-origin: center bottom; animation: growy .55s .18s var(--ease) both; }
  .st-key-card_turnaround .js-plotly-plot .barlayer {
    transform-origin: center bottom; animation: growy .55s .22s var(--ease) both; }
  .st-key-card_ages .js-plotly-plot .barlayer {
    transform-origin: center bottom; animation: growy .55s .26s var(--ease) both; }
}
@keyframes growx { from { transform: scaleX(0); opacity: .4; } }
@keyframes growy { from { transform: scaleY(0); opacity: .4; } }

/* ---------- glass fallbacks ---------- */
@media (prefers-reduced-transparency: reduce) {
  .card, [class*="st-key-demo_"], [class*="st-key-card_"], .st-key-ask_draft,
  .stat, .msg.bot .bub, .stExpander, [data-testid="stToast"], .flash,
  .stChatInput > div, .stButton button, [data-testid="stBottom"],
  [data-testid="stTextInputRootElement"], [data-testid="stNumberInputContainer"],
  .stTextArea [data-baseweb="textarea"],
  [data-testid="stSelectbox"] > div, [role="listbox"], [data-baseweb="popover"],
  [data-testid="stDataFrame"], [data-testid="stAlert"], .empty, .badge {
    background: var(--surface) !important;
    backdrop-filter: none !important; -webkit-backdrop-filter: none !important;
  }
  .msg.user .bub, .stButton button[kind="primary"],
  [data-testid="stBaseButton-primary"] {
    background: var(--accent-strong) !important;
    backdrop-filter: none !important; -webkit-backdrop-filter: none !important;
  }
  .st-key-topbar {
    background: var(--surface) !important;
    backdrop-filter: none !important; -webkit-backdrop-filter: none !important;
  }
  .stApp { background: var(--ground); }
  body::after { display: none; }
}
@media (prefers-contrast: more) {
  .card, [class*="st-key-demo_"], [class*="st-key-card_"], .st-key-ask_draft,
  .stat, .msg.bot .bub, .empty, [data-testid="stAlert"],
  [data-testid="stTextInputRootElement"], [data-testid="stNumberInputContainer"],
  .stTextArea [data-baseweb="textarea"],
  [data-testid="stSelectbox"] > div { border-color: var(--muted) !important; }
}

/* ---------- motion ---------- */
@media (prefers-reduced-motion: no-preference) {
  .page-head { animation: risein .26s var(--ease) both; }
  .stat { animation: risein .3s var(--ease) both; }
  [data-testid="stColumn"]:nth-child(2) .stat { animation-delay: .04s; }
  [data-testid="stColumn"]:nth-child(3) .stat { animation-delay: .08s; }
  [data-testid="stColumn"]:nth-child(4) .stat { animation-delay: .12s; }
  [data-testid="stColumn"]:nth-child(5) .stat { animation-delay: .16s; }
  .card, [class*="st-key-card_"], [class*="st-key-demo_"] {
    animation: risein .3s var(--ease) both; }
  .st-key-card_flow, .st-key-card_dept, .st-key-demo_ooo { animation-delay: .06s; }
  .st-key-card_donut, .st-key-card_turnaround, .st-key-demo_agent { animation-delay: .1s; }
  .st-key-card_ages, .st-key-card_bottlenecks, .st-key-demo_reset { animation-delay: .14s; }
}
@keyframes risein { from { opacity: 0; transform: translateY(7px); } }
@media (prefers-reduced-motion: reduce) {
  .card, [class*="st-key-card_"] { transition: none; }
  .atlas-brand .name::after { animation: none; }
}

footer { visibility: hidden; }
</style>
"""


# --- glass icon glyphs & the confidence meter --------------------------------
# Appended after the token pass so literal % values stay untouched.
_ART = """
/* The glyphs themselves are cut from glass — a translucent gradient ink
   with a light-catch, clipped to the letterform. No tiles behind them. */
[data-testid="stIconMaterial"] {
  font-size: 1.05rem;
  background: linear-gradient(165deg,
    rgba(20,56,42,.95) 8%, rgba(20,56,42,.45) 52%, rgba(20,56,42,.8) 92%);
  -webkit-background-clip: text; background-clip: text;
  color: transparent !important; -webkit-text-fill-color: transparent !important;
  filter: drop-shadow(0 1px 0 rgba(255,255,255,.55));
}
.st-key-topbar .stButton button[kind="primary"] [data-testid="stIconMaterial"] {
  background: linear-gradient(165deg,
    #83660A 8%, rgba(168,130,15,.5) 52%, #A8820F 92%);
  -webkit-background-clip: text; background-clip: text;
  -webkit-text-fill-color: transparent !important;
}
.stButton button[kind="primary"] [data-testid="stIconMaterial"],
[data-testid="stBaseButton-primary"] [data-testid="stIconMaterial"] {
  background: linear-gradient(165deg,
    rgba(243,238,224,.98) 8%, rgba(243,238,224,.48) 52%, rgba(243,238,224,.85) 92%);
  -webkit-background-clip: text; background-clip: text;
  -webkit-text-fill-color: transparent !important;
  filter: drop-shadow(0 1px 1px rgba(0,0,0,.35));
}
[class*="st-key-chip_"] [data-testid="stIconMaterial"] { font-size: .82rem; }
@media (prefers-contrast: more) {
  [data-testid="stIconMaterial"] {
    background: none !important; color: currentColor !important;
    -webkit-text-fill-color: currentColor !important; filter: none !important;
  }
}

/* The route-confidence meter on the approval card. */
.confmeter { margin: 0 0 4px; }
.confmeter .confhead { display: flex; justify-content: space-between;
  font-family: var(--mono); font-size: var(--fs-2xs); text-transform: uppercase;
  letter-spacing: .1em; color: var(--muted); margin-bottom: .3rem; }
.confmeter .confhead b { color: var(--ink); font-weight: 600; }
.confmeter .track { height: 8px; border-radius: 999px;
  background: rgba(27,53,40,.08);
  border: 1px solid rgba(255,255,255,.6);
  box-shadow: inset 0 1px 2px rgba(27,53,40,.12); overflow: hidden; }
.confmeter .fill { display: block; height: 100%; border-radius: inherit;
  background: linear-gradient(90deg, #A8820F, #C29B22);
  box-shadow: inset 0 1px 0 rgba(255,255,255,.45);
  transform-origin: left center;
}
@media (prefers-reduced-motion: no-preference) {
  .confmeter .fill { animation: confgrow 600ms var(--ease) 180ms both; }
}
@keyframes confgrow { from { transform: scaleX(0); } }
.confmeter.high .fill { background: linear-gradient(90deg, #128A5E, #1BA371); }
.confmeter.low .fill { background: linear-gradient(90deg, #BE3E2F, #D05A48); }

"""



# Appended after token processing — the data URI is full of literal %.
_GRAIN = (
    'body::after{content:"";position:fixed;inset:0;z-index:90;pointer-events:none;'
    'opacity:.045;background-image:url("data:image/svg+xml,%3Csvg xmlns=\'http://'
    "www.w3.org/2000/svg' width='160' height='160'%3E%3Cfilter id='n'%3E%3CfeTurbulence "
    "type='fractalNoise' baseFrequency='.9' numOctaves='2' stitchTiles='stitch'/%3E"
    "%3C/filter%3E%3Crect width='160' height='160' filter='url(%23n)'/%3E%3C/svg%3E\");}"
)


def _render_css() -> str:
    css = _CSS_TEMPLATE.replace("%(fonts)s", _font_css())
    for key, value in PALETTE.items():
        css = css.replace(f"%({key})s", value)
    for key, value in STATUS_COLORS.items():
        css = css.replace(f"%(status_{key})s", value)
    # Literal percent signs survive the token pass as %%.
    css = css.replace("%%", "%")
    return css.replace("</style>", _ART + "\n" + _GRAIN + "\n</style>")


CSS = _render_css()

# --- night variant -----------------------------------------------------------
# The same Paper Console, printed on dark evergreen stock: tokens flip, the
# glass turns smoky, and the handful of literal light values are re-inked.
_DARK = """
<style>
:root {
  color-scheme: dark;
  --ground: #0E1B15;
  --surface: #16281F;
  --rail: #0A1410;
  --line: rgba(236,239,232,.16);
  --line-soft: rgba(236,239,232,.1);
  --ink: #ECEFE8;
  --muted: #9DAA9E;
  --accent: #E9C25C;
  --accent-strong: #1E4433;
  --amber: #D9B254;
  --danger: #E06B5B;
  --warn: #D9A441;
  --ok: #3FBF8C;
  --warn-text: #D9A441;
  --ok-text: #3FBF8C;
  --status-pending: #D9A441;
  --status-acknowledged: #3FBF8C;
  --status-in_progress: #D9B254;
  --status-completed: #3FBF8C;
  --status-escalated: #E06B5B;
  --glass: rgba(18,34,26,.45);
  --glass-control: rgba(236,239,232,.07);
  --glass-control-hover: rgba(236,239,232,.14);
  --glass-overlay: rgba(18,34,26,.92);
  --fill-strong: rgba(30,68,51,.85);
  --edge: rgba(255,255,255,.14);
  --glass-edge: var(--edge);
  --edge-hover: rgba(233,194,92,.4);
  --edge-inverse: rgba(255,255,255,.2);
  --hover-tint: rgba(233,194,92,.12);
  --ring: 0 0 0 3px rgba(233,194,92,.35);
  --sheen-line: inset 0 1px 0 rgba(255,255,255,.12);
  --shadow-control: var(--sheen-line), 0 2px 6px -4px rgba(0,0,0,.5);
  --glass-shadow: var(--sheen-line), 0 14px 34px -22px rgba(0,0,0,.65);
  --shadow-overlay: var(--sheen-line), 0 18px 40px -24px rgba(0,0,0,.7);
  --shadow-fill: inset 0 1px 0 rgba(255,255,255,.18),
                 0 8px 18px -12px rgba(0,0,0,.7);
  --shadow-hover: var(--sheen-line), 0 8px 20px -12px rgba(0,0,0,.6);
  --fill-strong-hover: rgba(36,80,60,.95);
  --glass-sheen: linear-gradient(165deg,
                  rgba(255,255,255,.1) 0%, rgba(255,255,255,.03) 34%,
                  rgba(255,255,255,0) 60%);
}
body, [data-testid="stAppViewContainer"] { background-color: var(--ground); }
.stApp {
  background:
    radial-gradient(52rem 36rem at 12% -8%, rgba(233,194,92,.13), transparent 62%),
    radial-gradient(64rem 44rem at 108% 22%, rgba(63,191,140,.11), transparent 65%),
    radial-gradient(48rem 42rem at 60% 118%, rgba(233,194,92,.08), transparent 60%);
  background-attachment: fixed;
}
::selection { background: #3A4A3F; color: var(--ink); }
[data-testid="stIconMaterial"] {
  background: linear-gradient(165deg,
    rgba(236,239,232,.95) 8%, rgba(236,239,232,.42) 52%, rgba(236,239,232,.8) 92%);
  -webkit-background-clip: text; background-clip: text;
  filter: drop-shadow(0 1px 1px rgba(0,0,0,.45));
}
.stButton button:disabled { border-color: rgba(236,239,232,.18) !important; }
.st-key-reset_yes button { background: rgba(224,107,91,.82) !important; }
[role="listbox"] li, [role="listbox"] li *,
[data-baseweb="menu"] li, [data-baseweb="menu"] li *,
[role="option"], [role="option"] * {
  background-color: transparent !important;
  color: var(--ink) !important; -webkit-text-fill-color: var(--ink) !important;
}
[role="option"]:hover, [role="option"][aria-selected="true"],
[data-baseweb="menu"] li:hover {
  background-color: rgba(236,239,232,.14) !important;
}
/* help tooltips: dark pill, light text */
[data-baseweb="tooltip"], [data-testid="stTooltipContent"] {
  background: #101E17 !important; color: var(--ink) !important;
  border: 1px solid rgba(255,255,255,.18) !important;
}
[data-baseweb="tooltip"] *, [data-testid="stTooltipContent"] * {
  background: transparent !important;
  color: var(--ink) !important; -webkit-text-fill-color: var(--ink) !important;
}
[data-testid="stToast"] {
  background: rgba(18,34,26,.88) !important; color: var(--ink) !important;
}
.badge { box-shadow: inset 0 1px 0 rgba(255,255,255,.1); }
.dtable .loadbar { background: rgba(236,239,232,.12); }
.dtable .loadbar i { background: linear-gradient(90deg, #D9B254, #E9C25C); }
.msg.bot .ava { background: #1E4433; }
.chatcard { background: rgba(18,34,26,.55);
  border-color: rgba(236,239,232,.16);
  box-shadow: inset 0 1px 0 rgba(255,255,255,.08); }
[data-testid="stChatInputSubmitButton"]:not([disabled]) {
  background: var(--accent); color: #122019 !important; }
[data-testid="stChatInputSubmitButton"]:not([disabled]) svg { fill: #122019; }
.confmeter .track { background: rgba(236,239,232,.12);
  border-color: rgba(255,255,255,.14);
  box-shadow: inset 0 1px 2px rgba(0,0,0,.4); }
.livedot.on { box-shadow: 0 0 0 3px rgba(63,191,140,.2); }
.st-key-topbar .stButton button[kind="primary"] [data-testid="stIconMaterial"] {
  background: linear-gradient(165deg,
    #F2D584 8%, rgba(233,194,92,.5) 52%, #D9B254 92%);
  -webkit-background-clip: text; background-clip: text;
  -webkit-text-fill-color: transparent !important;
}
[data-testid="stBottom"] { background: rgba(14,27,21,.78); }
[data-testid="stBottom"] > div { background: transparent; }
body::after { opacity: .06; }
</style>
"""


def is_dark() -> bool:
    return bool(st.session_state.get("atlas_dark"))


def inject() -> None:
    # One markdown element for both sheets, so light and dark pages share
    # identical layout (an extra zero-height container would shift the page).
    st.markdown(CSS + (_DARK if is_dark() else ""), unsafe_allow_html=True)


def _flip() -> None:
    st.session_state["atlas_dark"] = not st.session_state.get("atlas_dark")


def mode_toggle() -> None:
    """A fixed round glass button in the top-right corner: sun <-> moon."""
    with st.container(key="theme_toggle"):
        st.button(
            "Switch to light mode" if is_dark() else "Switch to dark mode",
            icon=":material/light_mode:" if is_dark() else ":material/dark_mode:",
            key="theme_toggle_btn",
            on_click=_flip,
        )
