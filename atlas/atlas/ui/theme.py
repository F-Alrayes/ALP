"""Custom CSS — "Night Console", a dark operations terminal.

A different world from the browser preview's paper ledger: near-black
blue-charcoal ground, flat bordered panels instead of soft shadows, IBM Plex
Mono as the display voice, one periwinkle accent plus amber. Navigation lives
in a dark left rail. Instrument Sans still does the body work; the fonts are
embedded from ``preview/fonts`` so the app runs with the network unplugged.

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
  --line-soft: #1E2530;
  --ink: %(ink)s;
  --muted: %(muted)s;
  --accent: #6E9BFF;                 /* interactive chrome */
  --accent-strong: %(green_700)s;    /* filled actions */
  --accent-tint: %(green_100)s;
  --amber: %(gold_600)s;
  --danger: %(danger)s;
  --warn: %(warn)s;
  --ok: %(ok)s;
  --sans: "Instrument Sans", ui-sans-serif, system-ui, -apple-system, sans-serif;
  --mono: "IBM Plex Mono", ui-monospace, SFMono-Regular, Menlo, monospace;
  --ease: cubic-bezier(.23,1,.32,1);
  --r: 10px;
}

html, body, [class*="css"], .stApp { font-family: var(--sans); }
.stApp { background: var(--ground); color: var(--ink); }
.block-container { max-width: 1320px; padding-top: 1.1rem; padding-bottom: 4rem; }
section[data-testid="stMain"] { overflow-x: clip; }
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

::selection { background: var(--accent-tint); color: var(--ink); }
input, textarea { caret-color: var(--accent); }
* { scrollbar-width: thin; scrollbar-color: var(--line) transparent; }
:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
hr { border-color: var(--line-soft); }

/* ---------- the rail ---------- */
[data-testid="stSidebar"] {
  background: var(--rail); border-right: 1px solid var(--line-soft);
}
[data-testid="stSidebar"] * { color: var(--ink); }
[data-testid="stSidebar"] .stButton button {
  background: transparent !important; border: none !important; box-shadow: none;
  width: 100%%; justify-content: flex-start; text-align: left;
  font-family: var(--mono); font-size: .78rem; text-transform: uppercase;
  letter-spacing: .09em; color: var(--muted); border-radius: 7px;
  padding: .45rem .7rem; min-height: 0;
}
[data-testid="stSidebar"] .stButton button:hover {
  color: var(--ink); background: rgba(110,155,255,.08) !important; transform: none;
}
[data-testid="stSidebar"] .stButton button[kind="primary"],
[data-testid="stSidebar"] .stButton button[kind="primary"] * {
  color: var(--accent) !important; -webkit-text-fill-color: var(--accent) !important;
}
[data-testid="stSidebar"] .stButton button[kind="primary"] {
  background: var(--accent-tint) !important;
  box-shadow: inset 2px 0 0 var(--accent);
}
[data-testid="stSidebar"] [data-testid="stSelectbox"] > div {
  background: %(green_800)s; border-radius: 8px; border: 1px solid var(--line-soft);
}
[data-testid="stSidebar"] hr { border-color: var(--line-soft); }
[data-testid="stSidebar"] .stCaption, [data-testid="stSidebar"] small { color: var(--muted); }

.atlas-brand { display: flex; align-items: baseline; gap: .5rem;
  padding: .3rem .2rem 1rem; font-family: var(--mono); }
.atlas-brand .name { font-size: 1.05rem; font-weight: 600; letter-spacing: .18em;
  color: var(--ink); }
.atlas-brand .name::after { content: "_"; color: var(--accent); font-weight: 600; }
@media (prefers-reduced-motion: no-preference) {
  .atlas-brand .name::after { animation: caret 1.1s steps(1) infinite; }
}
@keyframes caret { 50%% { opacity: 0; } }
.atlas-brand .build { font-size: .58rem; color: var(--muted);
  letter-spacing: .08em; text-transform: uppercase; }

/* ---------- page head ---------- */
.page-head { padding: 0 0 .9rem; margin-bottom: 1.1rem;
  border-bottom: 1px solid var(--line-soft); }
.page-head .eyebrow { font-family: var(--mono); font-size: .66rem;
  text-transform: uppercase; letter-spacing: .16em; color: var(--accent);
  margin-bottom: .3rem; }
.page-head .eyebrow::before { content: "// "; color: var(--muted); }
.page-head h1 { margin: 0 0 .25rem; }
.page-head .sub { color: var(--muted); font-size: .9rem; margin: 0; }

/* ---------- panels ---------- */
.card {
  background: var(--surface); border: 1px solid var(--line); border-radius: var(--r);
  padding: .95rem 1.1rem; margin-bottom: .65rem;
  transition: border-color .18s var(--ease), transform .18s var(--ease);
}
.card:hover { border-color: #3B4759; transform: translateY(-1px); }
.card.accent { border-left: 2px solid var(--accent); }
.card-title { font-weight: 600; font-size: .95rem; color: var(--ink); }
.card-meta { font-size: .8rem; color: var(--muted); margin-top: 2px; }
.card-body { font-size: .88rem; margin-top: .5rem; color: var(--ink);
  white-space: pre-line; }

[class*="st-key-demo_"], [class*="st-key-card_"], .st-key-ask_draft {
  background: var(--surface); border: 1px solid var(--line) !important;
  border-radius: var(--r) !important; padding: 1.0rem 1.05rem !important;
  transition: border-color .18s var(--ease);
}
[class*="st-key-card_"]:hover { border-color: #3B4759; }

/* ---------- stat tiles ---------- */
.stat {
  background: var(--surface); border: 1px solid var(--line);
  border-left: 2px solid var(--accent); border-radius: var(--r);
  padding: .75rem .95rem; min-height: 96px;
  display: flex; flex-direction: column; justify-content: center;
}
.stat .label { font-family: var(--mono); font-size: .62rem; text-transform: uppercase;
  letter-spacing: .12em; color: var(--muted); }
.stat .value { font-family: var(--mono); font-size: 1.75rem; font-weight: 600;
  color: var(--ink); line-height: 1.15; font-variant-numeric: tabular-nums; }
.stat .delta { font-size: .74rem; color: var(--muted); }
.stat.warn  { border-left-color: var(--warn); }  .stat.warn .value { color: var(--warn); }
.stat.danger{ border-left-color: var(--danger);} .stat.danger .value { color: var(--danger); }
.stat.ok    { border-left-color: var(--ok); }    .stat.ok .value { color: var(--ok); }

/* ---------- badges ---------- */
.badge {
  display: inline-block; font-family: var(--mono); font-size: .62rem;
  text-transform: uppercase; letter-spacing: .08em; padding: 1px 7px;
  border-radius: 4px; border: 1px solid; background: transparent;
  vertical-align: middle;
}
.badge.pending      { color: %(status_pending)s; border-color: %(status_pending)s55; }
.badge.acknowledged { color: %(status_acknowledged)s; border-color: %(status_acknowledged)s55; }
.badge.in_progress  { color: %(status_in_progress)s; border-color: %(status_in_progress)s55; }
.badge.completed    { color: %(status_completed)s; border-color: %(status_completed)s55; }
.badge.escalated    { color: %(status_escalated)s; border-color: %(status_escalated)s55; }
.badge.role  { color: var(--accent); border-color: #6E9BFF44; }
.badge.gold  { color: var(--amber); border-color: #D9A45B44; }
.badge.muted { color: var(--muted); border-color: var(--line); }
.badge.ooo   { color: var(--danger); border-color: #E0685C44; }

/* ---------- buttons ---------- */
.stButton button {
  border-radius: 8px; border: 1px solid var(--line); font-weight: 500;
  background: #1B2330; color: var(--ink);
  transition: transform .4s cubic-bezier(.34,1.35,.64,1),
              border-color .15s var(--ease), background .15s var(--ease);
  will-change: transform;
}
.stButton button:hover { border-color: var(--accent); background: #1F2937; }
.stButton button:active { transform: scale(.96); transition: transform .1s ease-out; }
.stButton button[kind="primary"],
[data-testid="stBaseButton-primary"] {
  background: var(--accent-strong); border-color: var(--accent-strong);
}
.stButton button[kind="primary"], .stButton button[kind="primary"] *,
[data-testid="stBaseButton-primary"], [data-testid="stBaseButton-primary"] * {
  color: #F2F6FF !important; -webkit-text-fill-color: #F2F6FF !important;
}
.stButton button[kind="primary"]:hover { filter: brightness(1.12); }
@media (prefers-reduced-motion: reduce) {
  .stButton button, .stButton button:active { transition: none; transform: none; }
}

/* ---------- inputs, tabs, tables ---------- */
.stTextInput input, .stTextArea textarea, .stNumberInput input {
  background: #131923 !important; border-color: var(--line) !important;
  border-radius: 8px !important; color: var(--ink) !important;
}
.stTextArea textarea::placeholder, .stTextInput input::placeholder {
  font-family: var(--mono); color: var(--muted); }
[data-testid="stSelectbox"] > div { background: #131923; border-radius: 8px; }
[role="listbox"], [data-baseweb="popover"] { color: var(--ink); background: var(--surface); }

.stTabs [data-baseweb="tab-list"] { gap: .2rem; border-bottom: 1px solid var(--line-soft); }
.stTabs [data-baseweb="tab"] {
  font-family: var(--mono); font-size: .74rem; text-transform: uppercase;
  letter-spacing: .08em; color: var(--muted); padding: .4rem .8rem;
}
.stTabs [aria-selected="true"] { color: var(--ink) !important;
  box-shadow: inset 0 -2px 0 var(--accent); background: transparent; }

.stExpander { border: 1px solid var(--line) !important; border-radius: var(--r) !important;
  background: var(--surface); }
[data-testid="stMetricValue"] { color: var(--ink); font-family: var(--mono); }
[data-testid="stDataFrame"] { border: 1px solid var(--line); border-radius: var(--r); }

.empty { border: 1px dashed var(--line); border-radius: var(--r);
  padding: 1.7rem 1.3rem; text-align: center; color: var(--muted);
  background: transparent; }
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
.chart-note { font-size: .66rem; color: #5C6878; letter-spacing: .05em; }

/* ---------- the conversation ---------- */
/* One fluid, centred column: log, draft, chips, undo and composer all share
   min(920px, full width). */
.chatlog { width: 100%%; max-width: 920px; margin-inline: auto;
  padding: .15rem 0 .3rem; }
.msg { display: flex; gap: 11px; margin-bottom: 15px; }
.msg.user { justify-content: flex-end; }
.msg.user .bub { background: #22365C; border: 1px solid #33507F;
  color: #E9EFFB; border-radius: 12px 12px 4px 12px; padding: 9px 14px;
  max-width: 78%%; }
.msg.bot .ava { width: 27px; height: 27px; border-radius: 7px;
  background: var(--accent-strong); color: #F2F6FF; display: grid;
  place-items: center; font-family: var(--mono); font-weight: 600;
  font-size: .8rem; flex: none; margin-top: 2px; }
.msg.bot .bub { background: var(--surface); border: 1px solid var(--line);
  border-radius: 4px 12px 12px 12px; padding: 11px 15px; flex: 1; min-width: 0; }
.msg .bub p { margin: 0; }
.msg .bub p + p { margin-top: 8px; }
.msg .bub .small { font-size: .82rem; color: var(--muted); }
.chatcard { border: 1px solid var(--line); background: #131923;
  border-radius: 8px; padding: .55rem .8rem; margin-top: .55rem; }
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
  border-radius: 6px !important; background: transparent !important;
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
[data-testid="stBottom"] { background: var(--ground);
  border-top: 1px solid var(--line-soft); }
[data-testid="stBottomBlockContainer"] { max-width: 1320px;
  padding-top: .55rem; padding-bottom: 1rem; background: var(--ground); }
.stChatInput { max-width: 920px; margin-inline: auto; }
.stChatInput > div { border-radius: 10px !important;
  border: 1px solid var(--line) !important; background: #131923 !important;
  box-shadow: none !important; }
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
.draft-src { font-size: .6rem; color: var(--accent); border: 1px solid #6E9BFF55;
  padding: 1px 7px; border-radius: 4px; letter-spacing: .08em; }
.draft-route { margin: .25rem 0 .5rem; font-size: .9rem; }

/* ---------- toast & flash ---------- */
[data-testid="stToast"] {
  background: var(--surface) !important; color: var(--ink) !important;
  border: 1px solid var(--line); border-left: 2px solid var(--accent);
  border-radius: 10px; padding: .8rem .95rem;
}
[data-testid="stToast"] [data-testid="stMarkdownContainer"] p { color: var(--ink); }
[data-testid="stToast"] [data-testid="stMarkdownContainer"] p strong {
  font-family: var(--mono); font-size: .78rem; text-transform: uppercase;
  letter-spacing: .09em; color: var(--accent); }

.flash {
  position: fixed; right: 22px; bottom: 84px; z-index: 98;
  background: var(--surface); color: var(--ink); border: 1px solid var(--line);
  border-left: 2px solid var(--ok);
  padding: .55rem 1rem; border-radius: 8px; font-size: .84rem;
  font-family: var(--mono);
  animation: flashin .3s var(--ease) both;
}
@keyframes flashin { from { opacity: 0; transform: translateY(8px); } }

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
  .st-key-card_dept, .st-key-demo_ooo { animation-delay: .06s; }
  .st-key-card_turnaround, .st-key-demo_agent { animation-delay: .1s; }
  .st-key-card_ages, .st-key-demo_reset { animation-delay: .14s; }
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


def _render_css() -> str:
    css = _CSS_TEMPLATE.replace("%(fonts)s", _font_css())
    for key, value in PALETTE.items():
        css = css.replace(f"%({key})s", value)
    for key, value in STATUS_COLORS.items():
        css = css.replace(f"%(status_{key})s", value)
    # Literal percent signs survive the token pass as %%.
    return css.replace("%%", "%")


CSS = _render_css()


def inject() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
