"""Custom CSS — "Paper Console": the console layout in the ledger palette.

The operations-terminal structure (dark evergreen rail, flat bordered
panels, IBM Plex Mono display voice) wearing the original colors: warm
cream ground, evergreen ink, one gold accent. Instrument Sans does the body
work; the fonts are embedded from ``preview/fonts`` so the app runs with
the network unplugged.

Every class contract from the pages (.card, .stat, .badge, .chatlog, .kv,
.page-head, .chart-head, .flash, …) is kept — only the world changed.
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
  --sans: "Instrument Sans", ui-sans-serif, system-ui, -apple-system, sans-serif;
  --mono: "IBM Plex Mono", ui-monospace, SFMono-Regular, Menlo, monospace;
  --ease: cubic-bezier(.23,1,.32,1);
  --r: 16px;
  --glass: rgba(255,253,246,.42);
  --glass-edge: rgba(255,255,255,.6);
  --glass-blur: blur(26px) saturate(1.5);
  --glass-shadow: inset 0 1px 0 rgba(255,255,255,.7),
                  0 14px 34px -22px rgba(27,53,40,.4);
  /* the visible light-catch that makes a panel read as glass on flat paper */
  --glass-sheen: linear-gradient(165deg,
                  rgba(255,255,255,.6) 0%, rgba(255,255,255,.16) 34%,
                  rgba(255,253,246,0) 60%);
}

html, body, [class*="css"], .stApp { font-family: var(--sans); }
.stApp {
  background:
    radial-gradient(52rem 36rem at 12%% -8%%, rgba(168,130,15,.15), transparent 62%%),
    radial-gradient(64rem 44rem at 108%% 22%%, rgba(18,138,94,.13), transparent 65%%),
    radial-gradient(48rem 42rem at 60%% 118%%, rgba(168,130,15,.11), transparent 60%%),
    var(--ground);
  background-attachment: fixed;
  color: var(--ink);
}
.block-container { max-width: 1320px; padding-top: 1.1rem; padding-bottom: 4rem; }
section.stMain { overflow-x: clip; }
[data-testid="stHeader"] { background: transparent; }
[data-testid="stDecoration"] { display: none; }

/* Display voice: the terminal speaks mono. */
h1, h2, h3, h4,
[data-testid="stMarkdownContainer"] h1, [data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3, [data-testid="stHeading"] h1,
[data-testid="stHeading"] h2, [data-testid="stHeading"] h3 {
  font-family: var(--mono) !important; color: var(--ink);
  font-weight: 600; letter-spacing: -0.01em;
}
h1 { font-size: 1.7rem; line-height: 1.15; }
h2 { font-size: 1.05rem; margin-top: 1.5rem; text-transform: uppercase;
     letter-spacing: .06em; color: var(--muted); }
h3 { font-size: .95rem; }
h4 { font-size: .85rem; text-transform: uppercase; letter-spacing: .07em;
     color: var(--muted); }
p, li, label, .stMarkdown { color: var(--ink); }
.mono { font-family: var(--mono); font-variant-numeric: tabular-nums; }
.subtle { color: var(--muted); font-size: 0.85rem; }

::selection { background: #F7EFD5; color: var(--ink); }
input, textarea { caret-color: var(--accent); }
* { scrollbar-width: thin; scrollbar-color: var(--line) transparent; }
:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
hr { border-color: var(--line-soft); }

/* Streamlit keeps columns on one row at every width; below the bento's
   comfortable minimum, let rows wrap so tiles keep their measure. */
@media (max-width: 1180px) {
  [data-testid="stHorizontalBlock"] { flex-wrap: wrap !important; }
  [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
    flex: 1 1 240px !important; min-width: 240px !important; }
}

/* the theme toggle: a round glass button pinned to the corner */
.st-key-theme_toggle { position: fixed; top: 10px; right: 18px;
  z-index: 1000001; width: auto !important; }
.st-key-theme_toggle .stButton button {
  width: 38px; height: 38px; min-height: 38px; border-radius: 50%%;
  padding: 0; justify-content: center; }
.st-key-theme_toggle .stButton button [data-testid="stIconMaterial"] {
  background: transparent !important; border: none !important;
  box-shadow: none !important; padding: 0; margin: 0 !important;
  font-size: 1.05rem; }

/* live status dot (agent running / stopped) */
.livedot { display: inline-block; width: 9px; height: 9px; border-radius: 50%%;
  background: var(--muted); vertical-align: 1px; margin-left: 2px; }
.livedot.on { background: var(--ok); box-shadow: 0 0 0 3px rgba(18,138,94,.16); }

/* ---------- the rail ---------- */
[data-testid="stSidebar"] {
  background: var(--rail); border-right: 1px solid var(--line-soft);
}
[data-testid="stSidebar"] * { color: #EFEADA; }
[data-testid="stSidebar"] .stButton button {
  background: transparent !important; border: none !important; box-shadow: none;
  backdrop-filter: none; -webkit-backdrop-filter: none;
  width: 100%%; justify-content: flex-start; text-align: left;
  font-family: var(--mono); font-size: .78rem; text-transform: uppercase;
  letter-spacing: .09em; color: #B7C2B0; border-radius: 7px;
  padding: .45rem .7rem; min-height: 0;
}
[data-testid="stSidebar"] .stButton button:hover {
  color: #F5F1E4; background: rgba(233,223,201,.10) !important; transform: none;
}
[data-testid="stSidebar"] .stButton button[kind="primary"],
[data-testid="stSidebar"] .stButton button[kind="primary"] * {
  color: #E9C25C !important; -webkit-text-fill-color: #E9C25C !important;
}
[data-testid="stSidebar"] .stButton button[kind="primary"] {
  background: rgba(168,130,15,.16) !important;
  box-shadow: inset 2px 0 0 var(--accent);
}
[data-testid="stSidebar"] [data-testid="stSelectbox"] > div {
  background: rgba(239,234,218,.08); border-radius: 11px;
  border: 1px solid rgba(239,234,218,.28);
  backdrop-filter: blur(8px) saturate(1.3);
  -webkit-backdrop-filter: blur(8px) saturate(1.3);
  box-shadow: inset 0 1px 0 rgba(255,255,255,.14);
}
/* The light base theme paints the value box; blank the internals so the
   dark shell shows through and the cream text stays legible. */
[data-testid="stSidebar"] [data-testid="stSelectbox"] div,
[data-testid="stSidebar"] [data-testid="stSelectbox"] input {
  background-color: transparent !important;
  color: #EFEADA !important; -webkit-text-fill-color: #EFEADA !important;
}
[data-testid="stSidebar"] svg { fill: #C9D2C4; }
[data-testid="stSidebar"] hr { border-color: rgba(233,223,201,.18); }
[data-testid="stSidebar"] .stCaption, [data-testid="stSidebar"] small { color: #A8B3A2; }

.atlas-brand { padding: .3rem .2rem 1rem; font-family: var(--mono); }
.atlas-brand .name { font-size: 1.05rem; font-weight: 600; letter-spacing: .18em;
  color: #F5F1E4; }
.atlas-brand .name::after { content: "_"; color: var(--accent); font-weight: 600; }
@media (prefers-reduced-motion: no-preference) {
  .atlas-brand .name::after { animation: caret 1.1s steps(1) infinite; }
}
@keyframes caret { 50%% { opacity: 0; } }
.atlas-brand .build { display: block; margin-top: 3px; font-size: .58rem;
  color: #A8B3A2; letter-spacing: .08em; text-transform: uppercase; }

/* ---------- page head ---------- */
.page-head { padding: 0 0 .9rem; margin-bottom: 1.1rem;
  border-bottom: 1px solid var(--line-soft); }
.page-head .eyebrow { font-family: var(--mono); font-size: .66rem;
  text-transform: uppercase; letter-spacing: .16em; color: var(--amber);
  margin-bottom: .3rem; }
.page-head .eyebrow::before { content: "// "; color: var(--muted); }
.page-head h1 { margin: 0 0 .25rem; }
.page-head .sub { color: var(--muted); font-size: .9rem; margin: 0; }

/* ---------- panels ---------- */
.card {
  background: var(--glass-sheen), var(--glass);
  border: 1px solid var(--glass-edge); border-radius: var(--r);
  backdrop-filter: var(--glass-blur); -webkit-backdrop-filter: var(--glass-blur);
  box-shadow: var(--glass-shadow);
  padding: .95rem 1.1rem; margin-bottom: .65rem;
  transition: border-color .18s var(--ease), transform .18s var(--ease);
}
.card:hover { border-color: #CDC3A8; transform: translateY(-1px); }
.card.accent { border-left: 2px solid var(--accent); }
.card-title { font-weight: 600; font-size: .95rem; color: var(--ink); }
.card-meta { font-size: .8rem; color: var(--muted); margin-top: 2px; }
.card-body { font-size: .88rem; margin-top: .5rem; color: var(--ink);
  white-space: pre-line; }

[class*="st-key-demo_"], [class*="st-key-card_"], .st-key-ask_draft {
  background: var(--glass-sheen), var(--glass);
  border: 1px solid var(--glass-edge) !important;
  backdrop-filter: var(--glass-blur); -webkit-backdrop-filter: var(--glass-blur);
  box-shadow: var(--glass-shadow);
  border-radius: 18px !important; padding: 1.0rem 1.05rem !important;
  transition: border-color .18s var(--ease);
}
[class*="st-key-card_"]:hover { border-color: #CDC3A8; }

/* ---------- stat tiles ---------- */
.stat {
  background: var(--glass-sheen), var(--glass);
  border: 1px solid var(--glass-edge);
  backdrop-filter: var(--glass-blur); -webkit-backdrop-filter: var(--glass-blur);
  box-shadow: var(--glass-shadow);
  border-left: 3px solid var(--accent); border-radius: var(--r);
  padding: .75rem .95rem; min-height: 96px;
  display: flex; flex-direction: column; justify-content: center;
}
.stat .label { font-family: var(--mono); font-size: .62rem; text-transform: uppercase;
  letter-spacing: .12em; color: var(--muted); }
.stat .value { font-family: var(--mono); font-size: 1.75rem; font-weight: 600;
  color: var(--ink); line-height: 1.15; font-variant-numeric: tabular-nums;
  white-space: nowrap; }
.stat .delta { font-size: .74rem; color: var(--muted); }
.stat.bare { background: none; border: none; box-shadow: none;
  backdrop-filter: none; -webkit-backdrop-filter: none;
  min-height: 0; padding: .3rem 0 .55rem; }
.stat.bare .value { font-size: 2.1rem; }
.stat.ok .label { color: var(--ok); }
.stat.warn .label { color: var(--warn); }
.donut-cap { text-align: center; font-size: .78rem; color: var(--muted);
  margin-top: -0.35rem; }
.stat.warn  { border-left-color: var(--warn); }  .stat.warn .value { color: var(--warn); }
.stat.danger{ border-left-color: var(--danger);} .stat.danger .value { color: var(--danger); }
.stat.ok    { border-left-color: var(--ok); }    .stat.ok .value { color: var(--ok); }

/* ---------- badges ---------- */
.badge {
  display: inline-block; font-family: var(--mono); font-size: .62rem;
  text-transform: uppercase; letter-spacing: .08em; padding: 1px 7px;
  border-radius: 4px; border: 1px solid; background: rgba(255,253,246,.45);
  backdrop-filter: blur(6px); -webkit-backdrop-filter: blur(6px);
  box-shadow: inset 0 1px 0 rgba(255,255,255,.5);
  vertical-align: middle;
}
.badge.pending      { color: %(status_pending)s; border-color: %(status_pending)s55; }
.badge.acknowledged { color: %(status_acknowledged)s; border-color: %(status_acknowledged)s55; }
.badge.in_progress  { color: %(status_in_progress)s; border-color: %(status_in_progress)s55; }
.badge.completed    { color: %(status_completed)s; border-color: %(status_completed)s55; }
.badge.escalated    { color: %(status_escalated)s; border-color: %(status_escalated)s55; }
.badge.role  { color: %(ok)s; border-color: #128A5E44; }
.badge.gold  { color: var(--amber); border-color: #A8820F44; }
.badge.muted { color: var(--muted); border-color: var(--line); }
.badge.ooo   { color: var(--danger); border-color: #BE3E2F44; }

/* ---------- buttons ---------- */
.stButton button {
  border-radius: 11px; border: 1px solid var(--glass-edge); font-weight: 500;
  background: rgba(255,253,246,.5); color: var(--ink);
  backdrop-filter: blur(16px) saturate(1.35); -webkit-backdrop-filter: blur(16px) saturate(1.35);
  box-shadow: inset 0 1px 0 rgba(255,255,255,.65);
  transition: transform .4s cubic-bezier(.34,1.35,.64,1),
              border-color .15s var(--ease), background .15s var(--ease);
  will-change: transform;
}
.stButton button:hover { border-color: var(--accent); background: rgba(255,253,246,.78); }
.stButton button:active { transform: scale(.96); transition: transform .1s ease-out; }
.stButton button[kind="primary"],
[data-testid="stBaseButton-primary"] {
  background: rgba(20,56,42,.85); border-color: rgba(255,255,255,.28);
  backdrop-filter: blur(16px) saturate(1.35);
  -webkit-backdrop-filter: blur(16px) saturate(1.35);
  box-shadow: inset 0 1px 0 rgba(255,255,255,.22),
              0 8px 18px -12px rgba(27,53,40,.6);
}
.stButton button[kind="primary"], .stButton button[kind="primary"] *,
[data-testid="stBaseButton-primary"], [data-testid="stBaseButton-primary"] * {
  color: #F3EEE0 !important; -webkit-text-fill-color: #F3EEE0 !important;
}
.stButton button[kind="primary"]:hover { filter: brightness(1.12); }
@media (prefers-reduced-motion: reduce) {
  .stButton button, .stButton button:active { transition: none; transform: none; }
}

/* ---------- inputs, tabs, tables ---------- */
.stTextInput input, .stTextArea textarea, .stNumberInput input {
  background: var(--glass) !important; border-color: var(--glass-edge) !important;
  border-radius: 11px !important; color: var(--ink) !important;
  backdrop-filter: blur(14px) saturate(1.45);
  -webkit-backdrop-filter: blur(14px) saturate(1.45);
  box-shadow: inset 0 1px 0 rgba(255,255,255,.8),
              0 2px 6px -4px rgba(27,53,40,.35);
}
.stTextArea textarea::placeholder, .stTextInput input::placeholder {
  font-family: var(--mono); color: var(--muted); }
[data-testid="stSelectbox"] > div {
  background: var(--glass); border: 1px solid var(--glass-edge);
  border-radius: 11px;
  backdrop-filter: blur(14px) saturate(1.45);
  -webkit-backdrop-filter: blur(14px) saturate(1.45);
  box-shadow: inset 0 1px 0 rgba(255,255,255,.8),
              0 2px 6px -4px rgba(27,53,40,.35);
}
[role="listbox"], [data-baseweb="popover"] {
  color: var(--ink); background: rgba(255,253,246,.7);
  backdrop-filter: var(--glass-blur); -webkit-backdrop-filter: var(--glass-blur);
  border: 1px solid var(--glass-edge); border-radius: 12px;
  box-shadow: var(--glass-shadow), 0 18px 40px -24px rgba(27,53,40,.5);
}

.stTabs [data-baseweb="tab-list"] { gap: .2rem; border-bottom: 1px solid var(--line-soft); }
.stTabs [data-baseweb="tab"] {
  font-family: var(--mono); font-size: .74rem; text-transform: uppercase;
  letter-spacing: .08em; color: var(--muted); padding: .4rem .8rem;
}
.stTabs [aria-selected="true"] { color: var(--ink) !important;
  box-shadow: inset 0 -2px 0 var(--accent); background: transparent; }

.stExpander { border: 1px solid var(--glass-edge) !important; border-radius: var(--r) !important;
  background: var(--glass); backdrop-filter: var(--glass-blur);
  -webkit-backdrop-filter: var(--glass-blur); }
[data-testid="stMetricValue"] { color: var(--ink); font-family: var(--mono); }
[data-testid="stDataFrame"] {
  border: 1px solid var(--glass-edge); border-radius: var(--r);
  background: var(--glass); backdrop-filter: var(--glass-blur);
  -webkit-backdrop-filter: var(--glass-blur); box-shadow: var(--glass-shadow);
}
[data-testid="stAlert"] {
  background: var(--glass) !important; border: 1px solid var(--glass-edge);
  border-radius: 12px; backdrop-filter: var(--glass-blur);
  -webkit-backdrop-filter: var(--glass-blur); box-shadow: var(--glass-shadow);
}
[data-testid="stToast"] {
  background: rgba(255,253,246,.8) !important;
  border: 1px solid var(--glass-edge) !important; border-radius: 14px !important;
  backdrop-filter: var(--glass-blur); -webkit-backdrop-filter: var(--glass-blur);
  box-shadow: var(--glass-shadow), 0 16px 36px -20px rgba(27,53,40,.5) !important;
  color: var(--ink) !important;
}

.empty { border: 1px dashed var(--glass-edge); border-radius: var(--r);
  padding: 1.7rem 1.3rem; text-align: center; color: var(--muted);
  background: var(--glass); backdrop-filter: var(--glass-blur);
  -webkit-backdrop-filter: var(--glass-blur);
  box-shadow: var(--glass-shadow); }
.empty .big { font-family: var(--mono); font-size: .95rem; color: var(--ink);
  margin-bottom: .2rem; }

.kv { font-size: .86rem; padding: .16rem 0; }
.kv .k { color: var(--muted); display: inline-block; min-width: 120px;
  font-family: var(--mono); font-size: .72rem; text-transform: uppercase;
  letter-spacing: .07em; }

.chart-head { font-family: var(--mono); font-size: .72rem; text-transform: uppercase;
  letter-spacing: .1em; color: var(--muted); margin: .05rem 0 .55rem;
  display: flex; align-items: baseline; gap: .6rem; }
.chart-head::before { content: "▮ "; color: var(--accent); }
.chart-note { font-size: .66rem; color: var(--muted); letter-spacing: .05em;
  margin-left: .55em; }
.chart-note::before { content: "· "; color: var(--line); }

/* Bento rows line up: a column stretches to the row's height, but the
   card's own layout wrapper keeps its natural height and leaves ragged
   bottoms. Let wrappers holding a dashboard card grow, and the card fill. */
[data-testid="stColumn"] > [data-testid="stVerticalBlock"]
  > [data-testid="stLayoutWrapper"]:has(> [class*="st-key-card_"]) {
  flex: 1 1 auto; }
[class*="st-key-card_"] { height: 100%%; }
/* Cards that end up taller than their content spread it instead of
   pooling the slack at the bottom. */
.st-key-card_kpi, .st-key-card_donut { justify-content: space-between; }

/* ---------- the conversation ---------- */
/* One fluid, centred column: log, draft, chips, undo and composer all share
   min(920px, full width). */
.chatlog { width: 100%%; max-width: 920px; margin-inline: auto;
  padding: .15rem 0 .3rem; }
.msg { display: flex; gap: 11px; margin-bottom: 15px; }
.msg.user { justify-content: flex-end; }
.msg.user .bub { background: rgba(20,56,42,.85);
  border: 1px solid rgba(255,255,255,.28);
  color: #F3EEE0; border-radius: 18px 18px 6px 18px; padding: 9px 15px;
  backdrop-filter: blur(16px) saturate(1.35);
  -webkit-backdrop-filter: blur(16px) saturate(1.35);
  box-shadow: inset 0 1px 0 rgba(255,255,255,.22),
              0 8px 18px -12px rgba(27,53,40,.6);
  max-width: 78%%; }
.msg.bot .ava { width: 27px; height: 27px; border-radius: 7px;
  background: var(--accent-strong); color: #F2F6FF; display: grid;
  place-items: center; font-family: var(--mono); font-weight: 600;
  font-size: .8rem; flex: none; margin-top: 2px; }
.msg.bot .bub { background: var(--glass); border: 1px solid var(--glass-edge);
  backdrop-filter: var(--glass-blur); -webkit-backdrop-filter: var(--glass-blur);
  box-shadow: var(--glass-shadow);
  border-radius: 6px 18px 18px 18px; padding: 11px 15px; flex: 1; min-width: 0; }
.msg .bub p { margin: 0; }
.msg .bub p + p { margin-top: 8px; }
.msg .bub .small { font-size: .82rem; color: var(--muted); }
.chatcard { border: 1px solid var(--line); background: rgba(246,241,225,.9);
  border-radius: 12px; padding: .55rem .8rem; margin-top: .55rem; }
.cc-title { font-weight: 600; font-size: .9rem; display: block; color: var(--ink); }
.cc-meta { font-size: .78rem; color: var(--muted); display: block; margin-top: 2px; }
.chatrow { border-top: 1px solid var(--line-soft); padding: .5rem 0 .35rem;
  display: block; }
.chatrow:first-child { border-top: none; }

.bub.typing { display: inline-flex; gap: 5px; align-items: center;
  padding: 14px 15px 12px; flex: none; }
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
  font-size: .68rem; text-transform: uppercase; letter-spacing: .07em;
  padding: .28rem .7rem; min-height: 0; color: var(--muted);
}
[class*="st-key-chip_"] .stButton button:hover {
  color: var(--accent); border-color: var(--accent) !important;
  transform: translateY(-1px);
}
[class*="st-key-chip_"] .stButton button p { font-size: .68rem; color: inherit !important; }

/* composer */
[data-testid="stBottom"] { background: rgba(250,246,235,.72);
  backdrop-filter: blur(14px) saturate(1.3); -webkit-backdrop-filter: blur(14px) saturate(1.3);
  border-top: 1px solid var(--glass-edge); }
[data-testid="stBottomBlockContainer"] { max-width: 1320px;
  padding-top: .55rem; padding-bottom: 1rem; background: transparent; }
.stChatInput { max-width: 920px; margin-inline: auto; }
.stChatInput > div { border-radius: 18px !important;
  border: 1px solid var(--glass-edge) !important; background: var(--glass) !important;
  backdrop-filter: var(--glass-blur); -webkit-backdrop-filter: var(--glass-blur);
  box-shadow: var(--glass-shadow) !important; }
.stChatInput textarea { background: transparent !important; color: var(--ink) !important; }
.stChatInput textarea::placeholder { font-family: var(--mono); color: var(--muted); }

/* draft card */
.st-key-ask_draft { max-width: 920px; margin-inline: auto; }
.st-key-ask_undo { max-width: 920px; margin-inline: auto; }
.st-key-ask_undo button { border-radius: 6px !important; font-family: var(--mono);
  font-size: .68rem; text-transform: uppercase; letter-spacing: .07em;
  padding: .28rem .8rem; min-height: 0; color: var(--muted); }
.draft-head { font-family: var(--mono); font-size: .8rem; text-transform: uppercase;
  letter-spacing: .1em; color: var(--ink); display: flex; align-items: center;
  gap: .6rem; margin-bottom: .4rem; }
.draft-head::before { content: "▮ "; color: var(--accent); }
.draft-src { font-size: .6rem; color: var(--amber); border: 1px solid #A8820F55;
  padding: 1px 7px; border-radius: 4px; letter-spacing: .08em; }
.draft-route { margin: .25rem 0 .5rem; font-size: .9rem; }

/* ---------- toast & flash ---------- */
[data-testid="stToast"] {
  background: var(--glass) !important; color: var(--ink) !important;
  backdrop-filter: var(--glass-blur); -webkit-backdrop-filter: var(--glass-blur);
  border: 1px solid var(--glass-edge); border-left: 3px solid var(--accent);
  border-radius: 14px; padding: .8rem .95rem;
  box-shadow: var(--glass-shadow);
}
[data-testid="stToast"] [data-testid="stMarkdownContainer"] p { color: var(--ink); }
[data-testid="stToast"] [data-testid="stMarkdownContainer"] p strong {
  font-family: var(--mono); font-size: .78rem; text-transform: uppercase;
  letter-spacing: .09em; color: var(--amber); }

.flash {
  position: fixed; right: 22px; bottom: 84px; z-index: 98;
  background: var(--glass); color: var(--ink); border: 1px solid var(--glass-edge);
  backdrop-filter: var(--glass-blur); -webkit-backdrop-filter: var(--glass-blur);
  box-shadow: var(--glass-shadow);
  border-left: 3px solid var(--ok);
  padding: .55rem 1rem; border-radius: 12px; font-size: .84rem;
  font-family: var(--mono);
  animation: flashin .3s var(--ease) both;
}
@keyframes flashin { from { opacity: 0; transform: translateY(8px); } }

/* ---------- the org tree ---------- */
/* The reference board's anatomy — top accent bar, avatar chip riding the
   corner, a reports-count pill under the card, elbow connectors — in the
   ledger's evergreen and gold. Pure CSS; the canvas scrolls sideways. */
.orgwrap { overflow-x: auto; padding: 1.4rem .5rem .9rem;
  background: var(--glass); border: 1px solid var(--glass-edge);
  border-radius: 18px; backdrop-filter: var(--glass-blur);
  -webkit-backdrop-filter: var(--glass-blur); box-shadow: var(--glass-shadow); }
.orgtree { min-width: max-content; margin-inline: auto; }
/* !important: Streamlit's markdown CSS hits nested lists with
   `li > ul { display: block }` at higher specificity. */
.orgtree ul { display: flex !important; justify-content: center;
  padding: 26px 0 0 !important; margin: 0 !important; position: relative; }
.orgtree li { list-style: none !important; position: relative;
  padding: 26px 12px 14px !important; margin: 0 !important;
  display: flex; flex-direction: column; align-items: center; }
/* elbows */
.orgtree li::before, .orgtree li::after { content: "";
  position: absolute; top: 0; right: 50%%; width: 50%%; height: 26px;
  border-top: 1.5px solid var(--line); }
.orgtree li::after { right: auto; left: 50%%;
  border-left: 1.5px solid var(--line); }
.orgtree li:only-child::before, .orgtree li:only-child::after { display: none; }
.orgtree li:only-child { padding-top: 0 !important; }
.orgtree li:first-child::before, .orgtree li:last-child::after { border: 0 none; }
.orgtree li:last-child::before { border-right: 1.5px solid var(--line);
  border-radius: 0 8px 0 0; }
.orgtree li:first-child::after { border-radius: 8px 0 0 0; }
.orgtree ul ul::before { content: ""; position: absolute; top: 0; left: 50%%;
  height: 26px; border-left: 1.5px solid var(--line); }
.orgtree > ul { padding-top: 0 !important; }
.orgtree > ul > li { padding-top: 0 !important; }
.orgtree > ul > li::before, .orgtree > ul > li::after { display: none; }
/* the card */
.onode { position: relative; width: 178px;
  background: rgba(255,253,246,.55); border: 1px solid var(--glass-edge);
  border-radius: 12px; padding: 14px 12px 12px; text-align: center;
  backdrop-filter: blur(14px) saturate(1.45);
  -webkit-backdrop-filter: blur(14px) saturate(1.45);
  box-shadow: inset 0 3px 0 var(--accent-strong),
              inset 0 4px 0 rgba(255,255,255,.5),
              0 10px 24px -18px rgba(27,53,40,.4);
  transition: transform .18s var(--ease), border-color .18s var(--ease);
}
.onode:hover { transform: translateY(-2px); border-color: #CDC3A8; }
.onode.hit { box-shadow: inset 0 3px 0 var(--accent),
  0 0 0 2px #A8820F55, 0 10px 24px -18px rgba(27,53,40,.4); }
.oava { position: absolute; top: -14px; right: 10px; width: 30px; height: 30px;
  border-radius: 50%%; background: var(--accent); color: #122019;
  font-family: var(--mono); font-weight: 600; font-size: .66rem;
  display: grid; place-items: center;
  box-shadow: 0 0 0 3px rgba(255,253,246,.94), inset 0 1px 0 rgba(255,255,255,.35); }
.onode.away .oava { box-shadow: 0 0 0 3px var(--danger),
  inset 0 1px 0 rgba(255,255,255,.35); }
.oname { font-weight: 600; font-size: .84rem; color: var(--ink); line-height: 1.2; }
.orole { font-size: .72rem; color: var(--muted); margin-top: 2px; line-height: 1.25; }
.odept { font-family: var(--mono); font-size: .58rem; text-transform: uppercase;
  letter-spacing: .1em; color: var(--amber); margin-top: 4px; }
.okids { position: absolute; left: 50%%; bottom: -9px; transform: translateX(-50%%);
  min-width: 18px; height: 18px; padding: 0 4px; border-radius: 5px;
  background: var(--accent-strong); color: #F3EEE0; font-family: var(--mono);
  font-size: .6rem; font-weight: 600; display: grid; place-items: center;
  box-shadow: 0 0 0 2px rgba(255,253,246,.94); }
@media (prefers-reduced-transparency: reduce) {
  .orgwrap { background: var(--surface); backdrop-filter: none;
    -webkit-backdrop-filter: none; }
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
  .stTextInput input, .stTextArea textarea, .stNumberInput input,
  [data-testid="stSelectbox"] > div, [role="listbox"], [data-baseweb="popover"],
  [data-testid="stDataFrame"], [data-testid="stAlert"], .empty, .onode,
  .orgwrap, .badge {
    background: var(--surface) !important;
    backdrop-filter: none !important; -webkit-backdrop-filter: none !important;
  }
  .msg.user .bub, .stButton button[kind="primary"],
  [data-testid="stBaseButton-primary"] {
    background: var(--accent-strong) !important;
    backdrop-filter: none !important; -webkit-backdrop-filter: none !important;
  }
  [data-testid="stSidebar"] [data-testid="stSelectbox"] > div {
    background: %(green_800)s !important;
    backdrop-filter: none !important; -webkit-backdrop-filter: none !important;
  }
  .stApp { background: var(--ground); }
  body::after { display: none; }
}
@media (prefers-contrast: more) {
  .card, [class*="st-key-demo_"], [class*="st-key-card_"], .st-key-ask_draft,
  .stat, .msg.bot .bub, .empty, .onode, [data-testid="stAlert"],
  .stTextInput input, .stTextArea textarea, .stNumberInput input,
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
  .card:hover { transform: none; }
  .atlas-brand .name::after { animation: none; }
}

footer { visibility: hidden; }
</style>
"""


# --- glass icon tiles & the confidence meter ---------------------------------
# Appended after the token pass so literal % values stay untouched.
_ART = """
/* Material glyphs sit on small liquid-glass tiles. */
[data-testid="stIconMaterial"] { font-size: 1rem; }
.stButton button [data-testid="stIconMaterial"],
[data-testid="stChatInput"] [data-testid="stIconMaterial"] {
  box-sizing: content-box; padding: 4px; border-radius: 8px;
  background: rgba(255,253,246,.55);
  border: 1px solid rgba(255,255,255,.65);
  backdrop-filter: blur(14px) saturate(1.45);
  -webkit-backdrop-filter: blur(14px) saturate(1.45);
  box-shadow: inset 0 1px 0 rgba(255,255,255,.8),
              0 2px 6px -4px rgba(27,53,40,.35);
}
[data-testid="stSidebar"] .stButton button [data-testid="stIconMaterial"] {
  font-size: .9rem; padding: 4px; margin-right: .3rem; border-radius: 8px;
  background: rgba(239,234,218,.09);
  border: 1px solid rgba(255,255,255,.14);
  box-shadow: inset 0 1px 0 rgba(255,255,255,.16);
}
[data-testid="stSidebar"] .stButton button[kind="primary"] [data-testid="stIconMaterial"] {
  background: rgba(233,194,92,.14);
  border-color: rgba(233,194,92,.35);
}
[class*="st-key-chip_"] [data-testid="stIconMaterial"] { font-size: .8rem; padding: 3px; }

/* The route-confidence meter on the approval card. */
.confmeter { margin: .25rem 0 .5rem; }
.confmeter .confhead { display: flex; justify-content: space-between;
  font-family: var(--mono); font-size: .62rem; text-transform: uppercase;
  letter-spacing: .11em; color: var(--muted); margin-bottom: .3rem; }
.confmeter .confhead b { color: var(--ink); font-weight: 600; }
.confmeter .track { height: 8px; border-radius: 999px;
  background: rgba(27,53,40,.08);
  border: 1px solid rgba(255,255,255,.6);
  box-shadow: inset 0 1px 2px rgba(27,53,40,.12); overflow: hidden; }
.confmeter .fill { display: block; height: 100%; border-radius: inherit;
  background: linear-gradient(90deg, #A8820F, #C29B22);
  box-shadow: inset 0 1px 0 rgba(255,255,255,.45);
  transition: width .5s var(--ease); }
.confmeter.high .fill { background: linear-gradient(90deg, #128A5E, #1BA371); }
.confmeter.low .fill { background: linear-gradient(90deg, #BE3E2F, #D05A48); }

@media (prefers-reduced-transparency: reduce), (prefers-contrast: more) {
  .stButton button [data-testid="stIconMaterial"],
  [data-testid="stSidebar"] .stButton button [data-testid="stIconMaterial"] {
    background: transparent; border-color: transparent;
    backdrop-filter: none; -webkit-backdrop-filter: none; box-shadow: none;
  }
}
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
  --glass: rgba(18,34,26,.45);
  --glass-edge: rgba(255,255,255,.14);
  --glass-shadow: inset 0 1px 0 rgba(255,255,255,.12),
                  0 14px 34px -22px rgba(0,0,0,.65);
  --glass-sheen: linear-gradient(165deg,
                  rgba(255,255,255,.1) 0%, rgba(255,255,255,.03) 34%,
                  rgba(255,255,255,0) 60%);
}
.stApp {
  background:
    radial-gradient(52rem 36rem at 12% -8%, rgba(233,194,92,.13), transparent 62%),
    radial-gradient(64rem 44rem at 108% 22%, rgba(63,191,140,.11), transparent 65%),
    radial-gradient(48rem 42rem at 60% 118%, rgba(233,194,92,.08), transparent 60%),
    var(--ground);
  background-attachment: fixed;
}
::selection { background: #3A4A3F; color: var(--ink); }
.stButton button {
  background: rgba(236,239,232,.07); color: var(--ink);
  border-color: rgba(255,255,255,.16);
  box-shadow: inset 0 1px 0 rgba(255,255,255,.12);
}
.stButton button:hover { background: rgba(236,239,232,.13); }
.stButton button [data-testid="stIconMaterial"],
[data-testid="stChatInput"] [data-testid="stIconMaterial"] {
  background: rgba(236,239,232,.08); border-color: rgba(255,255,255,.16);
  box-shadow: inset 0 1px 0 rgba(255,255,255,.14);
}
.stButton button[kind="primary"],
[data-testid="stBaseButton-primary"] {
  background: rgba(30,68,51,.8); border-color: rgba(255,255,255,.22);
}
.stTextInput input, .stTextArea textarea, .stNumberInput input,
[data-testid="stSelectbox"] > div {
  box-shadow: inset 0 1px 0 rgba(255,255,255,.12),
              0 2px 6px -4px rgba(0,0,0,.5);
}
[role="listbox"], [data-baseweb="popover"] {
  background: rgba(18,34,26,.88);
}
[role="listbox"] li, [data-baseweb="popover"] li { color: var(--ink); }
[data-testid="stToast"] {
  background: rgba(18,34,26,.88) !important; color: var(--ink) !important;
}
.badge { background: rgba(236,239,232,.06);
  box-shadow: inset 0 1px 0 rgba(255,255,255,.1); }
.msg.user .bub { background: rgba(30,68,51,.75);
  border-color: rgba(255,255,255,.2); }
.msg.bot .ava { background: #1E4433; }
.onode { background: rgba(22,40,30,.6); }
.oava { color: #122019; box-shadow: 0 0 0 3px rgba(14,27,21,.9),
  inset 0 1px 0 rgba(255,255,255,.35); }
.okids { color: #ECEFE8; box-shadow: 0 0 0 2px rgba(14,27,21,.9); }
.confmeter .track { background: rgba(236,239,232,.12);
  border-color: rgba(255,255,255,.14);
  box-shadow: inset 0 1px 2px rgba(0,0,0,.4); }
.livedot.on { box-shadow: 0 0 0 3px rgba(63,191,140,.2); }
[data-testid="stSidebar"] { border-right-color: rgba(255,255,255,.08); }
[data-testid="stBottom"] { background: rgba(14,27,21,.78); }
[data-testid="stBottom"] > div { background: transparent; }
/* The light base theme paints widget internals; blank them so the dark
   glass shells show through (same trick the rail select already uses). */
[data-testid="stSelectbox"] div, [data-testid="stSelectbox"] input,
.stTextInput div, .stTextArea div, .stNumberInput div,
.stNumberInput button, .stTextArea textarea {
  background-color: transparent !important;
  color: var(--ink) !important; -webkit-text-fill-color: var(--ink) !important;
}
.stTextInput input, .stTextArea textarea {
  background-color: var(--glass) !important; }
body::after { opacity: .06; }
</style>
"""


def is_dark() -> bool:
    return bool(st.session_state.get("atlas_dark"))


def inject() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
    if is_dark():
        st.markdown(_DARK, unsafe_allow_html=True)


def _flip() -> None:
    st.session_state["atlas_dark"] = not st.session_state.get("atlas_dark")


def mode_toggle() -> None:
    """A fixed round glass button in the top-right corner: sun <-> moon."""
    with st.container(key="theme_toggle"):
        st.button(
            "",
            icon=":material/light_mode:" if is_dark() else ":material/dark_mode:",
            key="theme_toggle_btn",
            help="Switch to light mode" if is_dark() else "Switch to dark mode",
            on_click=_flip,
        )
