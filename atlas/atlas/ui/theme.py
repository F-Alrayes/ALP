"""Custom CSS — "The Private Ledger", matched to the browser preview.

Warm paper, evergreen ink, one gold accent. Fraunces carries the display
voice, Instrument Sans does the work, IBM Plex Mono holds the numbers. The
fonts are embedded from the same woff2 subsets the preview uses (see
``preview/fonts``), so the app still runs with the network unplugged; if the
files are missing the fallback stacks carry the page.
"""

from __future__ import annotations

import base64
from pathlib import Path

import streamlit as st

from ..config import PALETTE

# The preview's latin subsets, reused verbatim. (family, style, weight, file)
_FONT_DIR = Path(__file__).resolve().parents[2] / "preview" / "fonts"
_FACES = [
    ("Fraunces", "normal", "100 900", "fraunces-latin-wght-normal.woff2"),
    ("Fraunces", "italic", "100 900", "fraunces-latin-wght-italic.woff2"),
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
  --green-900: %(green_900)s;
  --green-800: %(green_800)s;
  --green-700: %(green_700)s;
  --green-600: %(green_600)s;
  --green-100: %(green_100)s;
  --gold-600: %(gold_600)s;
  --gold-500: %(gold_500)s;
  --gold-300: %(gold_300)s;
  --cream-100: %(cream_100)s;
  --cream-200: %(cream_200)s;
  --cream-300: %(cream_300)s;
  --surface: #FFFDF6;
  --line-soft: #EFE8D5;
  --ink: %(ink)s;
  --muted: %(muted)s;
  --danger: %(danger)s;
  --warn: %(warn)s;
  --ok: %(ok)s;
  --sans: "Instrument Sans", ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif;
  --serif: "Fraunces", Georgia, "Times New Roman", serif;
  --mono: "IBM Plex Mono", ui-monospace, SFMono-Regular, Menlo, monospace;
  --ease: cubic-bezier(.23,1,.32,1);
  --edge: inset 0 1px 0 rgba(255,255,255,.55);
  --shadow: 0 1px 2px rgba(27,53,40,.05), 0 10px 28px -20px rgba(27,53,40,.38);
}

html, body, [class*="css"], .stApp { font-family: var(--sans); }
.stApp { background: var(--cream-100); color: var(--ink); }

/* Film grain: the same fixed, inert layer as the preview — paper, not a hex. */
.stApp::after {
  content: ''; position: fixed; inset: 0; z-index: 999; pointer-events: none;
  opacity: 0.05;
  background-image: url("data:image/svg+xml,%%3Csvg xmlns='http://www.w3.org/2000/svg' width='160' height='160'%%3E%%3Cfilter id='n'%%3E%%3CfeTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2' stitchTiles='stitch'/%%3E%%3C/filter%%3E%%3Crect width='160' height='160' filter='url(%%23n)'/%%3E%%3C/svg%%3E");
}

.block-container { padding-top: 0; padding-bottom: 4rem; max-width: 1240px; }
[data-testid="stMainBlockContainer"] { padding-top: 0; }

/* Streamlit's own theme sets heading fonts with higher specificity, so the
   display face has to insist. */
h1, h2, h3, h4,
[data-testid="stMarkdownContainer"] h1, [data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3, [data-testid="stHeading"] h1,
[data-testid="stHeading"] h2, [data-testid="stHeading"] h3 {
  font-family: var(--serif) !important; color: var(--ink);
  letter-spacing: -0.015em; font-weight: 560;
}
h1 { font-size: 2.3rem; line-height: 1.08; letter-spacing: -0.02em; }
h2 { font-size: 1.36rem; margin-top: 1.6rem; }
h3 { font-size: 1.05rem; }
p, li, label, .stMarkdown { color: var(--ink); }

::selection { background: #F7EFD5; color: var(--ink); }
input, textarea { caret-color: var(--gold-500); }
* { scrollbar-width: thin; scrollbar-color: var(--cream-300) transparent; }
:focus-visible { outline: 2px solid var(--gold-500); outline-offset: 2px; }

/* ---------- topbar: the preview's glass bar ---------- */
/* No sidebar. Navigation lives in a sticky translucent bar, exactly like
   the preview's .topbar: brand left, tabs beside it, identity right. */
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"],
[data-testid="stSidebarCollapseButton"] { display: none !important; }
[data-testid="stHeader"] { display: none; }

/* Sticky must live on the wrapper Streamlit puts around the keyed container:
   the wrapper is exactly as tall as the bar, so sticky on the bar itself has
   no room to stick. Browsers without :has simply get a non-sticky bar. */
div[data-testid="stLayoutWrapper"]:has(> .st-key-atlas_topbar) {
  position: sticky; top: 0; z-index: 99;
  /* The zero-height element carrying this stylesheet sits above the bar and
     still claims the block's 1rem flex gap; pull the bar up over it. */
  margin-top: -1rem;
}
section[data-testid="stMain"] { overflow-x: clip; }
.st-key-atlas_topbar {
  background: rgba(255, 253, 246, 0.92);  /* fallback where color-mix is unsupported */
  background: color-mix(in srgb, var(--surface) 84%, transparent);
  backdrop-filter: blur(14px) saturate(1.15);
  -webkit-backdrop-filter: blur(14px) saturate(1.15);
  border-bottom: 1px solid var(--cream-300);
  /* Full-bleed inside the centred block container: Streamlit pins the block's
     width, so take the viewport width explicitly and offset back to x=0. */
  width: 100vw !important; max-width: 100vw !important;
  margin: 0 0 1.3rem calc(50% - 50vw);
  padding: 0.5rem max(1.5rem, calc(50vw - 596px));
}
@supports not ((backdrop-filter: blur(1px)) or (-webkit-backdrop-filter: blur(1px))) {
  .st-key-atlas_topbar { background: var(--surface); }
}
/* The brand, tabs and More keep their natural width; the spacer and the
   identity select absorb any squeeze on narrower windows. */
.st-key-atlas_topbar [data-testid="stColumn"]:nth-child(-n+5) { min-width: max-content; }
@media (max-width: 1180px) {
  .st-key-atlas_topbar .stButton > button { padding: 0.3rem 0.55rem; }
  .atlas-brand .build { display: none; }
}
/* Below Streamlit's 640px column breakpoint the columns would stack into a
   full-screen sticky wall; force the bar to stay one row instead. */
@media (max-width: 640px) {
  .st-key-atlas_topbar [data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important; }
  .st-key-atlas_topbar [data-testid="stColumn"] { min-width: 0 !important; }
  .st-key-atlas_topbar [data-testid="stColumn"]:nth-child(-n+5) { min-width: max-content !important; }
  .atlas-brand .name, .atlas-brand .build { display: none; }
}
.st-key-atlas_topbar .stButton > button {
  background: transparent !important; border: none !important; color: var(--muted);
  box-shadow: none; font-weight: 550; border-radius: 999px;
  padding: 0.3rem 0.85rem; min-height: 0;
  transition: background .15s var(--ease), color .15s var(--ease);
}
/* Streamlit paints button labels on a nested node; keep them with the button. */
.st-key-atlas_topbar .stButton > button p,
.st-key-atlas_topbar [data-testid="stPopover"] button p,
[data-testid="stPopoverBody"] .stButton > button p {
  color: inherit !important; font-size: 0.9rem; white-space: nowrap;
}
.st-key-atlas_topbar .stButton > button:hover,
.st-key-atlas_topbar [data-testid="stPopover"] > button:hover {
  color: var(--ink); background: %(cream_200)s; border: none;
}
.st-key-atlas_topbar .stButton > button:active { transform: scale(.97); }
/* The active tab is pressed into the paper, not painted green — and its
   label keeps the ink (the global primary rule paints labels cream). */
.st-key-atlas_topbar .stButton > button[kind="primary"] {
  background: %(cream_200)s !important; border: none !important;
  box-shadow: inset 0 1px 3px rgba(27,53,40,.12), inset 0 0 0 1px var(--cream-300);
}
.st-key-atlas_topbar .stButton > button[kind="primary"],
.st-key-atlas_topbar .stButton > button[kind="primary"] *,
[data-testid="stPopoverBody"] .stButton > button[kind="primary"],
[data-testid="stPopoverBody"] .stButton > button[kind="primary"] * {
  color: var(--ink) !important; -webkit-text-fill-color: var(--ink) !important;
}
.st-key-atlas_topbar .stButton > button:hover { transform: none; box-shadow: none; }
.st-key-atlas_topbar [data-testid="stPopover"] button {
  background: transparent !important; border: none !important; color: var(--muted);
  font-weight: 550; border-radius: 999px; padding: 0.3rem 0.85rem; min-height: 0;
  white-space: nowrap;
}
.st-key-atlas_topbar [data-testid="stPopover"] button:hover { color: var(--ink); background: %(cream_200)s !important; }
.st-key-atlas_topbar [data-testid="stSelectbox"] > div {
  background: var(--surface); border-radius: 9px;
}
[data-testid="stPopoverBody"] {
  background: var(--surface); border: 1px solid var(--cream-300);
  border-radius: 12px; box-shadow: var(--edge), var(--shadow); min-width: 230px;
}
[data-testid="stPopoverBody"] .stButton > button {
  background: transparent !important; border: none !important; justify-content: flex-start;
  text-align: left; color: var(--ink); border-radius: 8px; min-height: 0;
  padding: 0.42rem 0.7rem; box-shadow: none;
}
[data-testid="stPopoverBody"] .stButton > button:hover {
  background: %(cream_200)s !important; transform: none;
}
[data-testid="stPopoverBody"] .stButton > button[kind="primary"] {
  background: %(cream_200)s !important; box-shadow: none;
}
[role="listbox"], [data-baseweb="popover"] { color: var(--ink); background: var(--surface); }

/* ---------- brand block ---------- */
.atlas-brand { display: flex; align-items: center; gap: 0.5rem; white-space: nowrap;
  padding: 0; overflow: hidden; min-width: 0; }
.atlas-brand .mark {
  display: inline-flex; align-items: center; justify-content: center;
  width: 27px; height: 27px; border-radius: 8px; background: var(--gold-500);
  color: var(--green-900); font-weight: 640; font-size: 0.95rem;
  font-family: var(--serif); flex: none;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.28), 0 1px 2px rgba(27,53,40,.18);
}
.atlas-brand .name { font-family: var(--serif); font-size: 1.0rem; font-weight: 600; letter-spacing: 0.12em; }
.atlas-brand .build { font-size: 0.58rem; color: var(--muted); letter-spacing: 0.06em;
  text-transform: uppercase; overflow: hidden; text-overflow: ellipsis; }

/* ---------- page header ---------- */
.page-head { border-bottom: 1px solid var(--cream-300); padding-bottom: 0.9rem; margin-bottom: 1.4rem; }
/* The heading carries its own weight; no kicker above it. */
.page-head .eyebrow { display: none; }
.page-head h1 { margin: 0.25rem 0 0.35rem 0; }
.page-head .sub { color: var(--muted); font-size: 0.94rem; margin: 0; }

/* ---------- cards ---------- */
.card {
  background: var(--surface); border: 1px solid var(--line-soft); border-radius: 10px;
  padding: 1.05rem 1.2rem; margin-bottom: 0.85rem;
  box-shadow: var(--edge), var(--shadow);
}
/* Status lives in the badge and the copy, never in a painted edge. */
.card.accent { border-color: var(--cream-300); background: #FBF4E1; }
.card .card-title { font-weight: 600; color: var(--ink); font-size: 1.0rem; margin-bottom: 0.15rem; }
.card .card-meta { color: var(--muted); font-size: 0.82rem; }
.card .card-body { margin-top: 0.55rem; font-size: 0.92rem; white-space: pre-wrap; }

.stat {
  background: var(--surface); border: 1px solid var(--line-soft); border-radius: 10px;
  padding: 0.95rem 1.1rem; height: 100%%;
  box-shadow: var(--edge), var(--shadow);
}
.stat .label { font-size: 0.72rem; color: var(--muted); font-weight: 500; letter-spacing: 0.02em; }
.stat .value {
  font-family: var(--serif); font-size: 2rem; font-weight: 560;
  color: var(--ink); line-height: 1.15; font-variant-numeric: tabular-nums;
}
.stat .delta { font-size: 0.8rem; color: var(--muted); }
/* Tone colours the number itself — the signal, not a stripe beside it. */
.stat.warn .value { color: var(--warn); }
.stat.danger .value { color: var(--danger); }
.stat.ok .value { color: var(--ok); }

/* ---------- badges ---------- */
.badge {
  display: inline-block; padding: 0.14rem 0.55rem; border-radius: 999px;
  font-size: 0.7rem; font-weight: 600; letter-spacing: 0.02em;
  border: 1px solid transparent; white-space: nowrap;
}
.badge.pending { background: #FBF1DC; color: %(warn)s; border-color: #E8D5AC; }
.badge.acknowledged { background: %(green_100)s; color: %(ok)s; border-color: #BCDCC8; }
.badge.in_progress { background: #F7EFD5; color: %(gold_600)s; border-color: #E6D296; }
.badge.completed { background: %(green_100)s; color: %(ok)s; border-color: #BCDCC8; }
.badge.escalated { background: #FAE7E3; color: %(danger)s; border-color: #E9BEB9; }
.badge.ooo { background: #FBF1DC; color: %(warn)s; border-color: #E1CB96; }
.badge.role { background: %(cream_200)s; color: %(muted)s; border-color: %(cream_300)s; }
.badge.gold { background: #F7EFD5; color: %(gold_600)s; border-color: #E6D296; }
.badge.muted { background: %(cream_200)s; color: %(muted)s; border-color: %(cream_300)s; }

/* ---------- resolution trace ---------- */
.trace { border-left: 1px solid var(--cream-300); margin: 0.4rem 0 0.4rem 0.6rem; padding-left: 1.05rem; }
.trace .step { position: relative; padding: 0.5rem 0; }
.trace .step:before {
  content: ''; position: absolute; left: -1.42rem; top: 0.85rem;
  width: 11px; height: 11px; border-radius: 50%%; border: 2px solid var(--surface);
}
.trace .step.ok:before { background: var(--ok); }
.trace .step.warn:before { background: var(--warn); }
.trace .step.fail:before { background: var(--danger); }
.trace .step .label { font-weight: 600; font-size: 0.88rem; color: var(--ink); }
.trace .step .detail { font-size: 0.88rem; color: var(--muted); }

/* ---------- timeline ---------- */
.timeline { border-left: 1px solid var(--cream-300); margin-left: 0.55rem; padding-left: 1.05rem; }
.timeline .entry { position: relative; padding: 0.45rem 0; }
.timeline .entry:before {
  content: ''; position: absolute; left: -1.36rem; top: 0.8rem;
  width: 9px; height: 9px; border-radius: 50%%; background: var(--green-600);
  border: 2px solid var(--surface);
}
.timeline .entry.agent:before { background: var(--gold-500); }
.timeline .entry.alert:before { background: var(--danger); }
.timeline .when { font-size: 0.74rem; color: var(--muted); letter-spacing: 0.02em; font-family: var(--mono); }
.timeline .what { font-size: 0.88rem; color: var(--ink); }
.timeline .who { font-size: 0.74rem; color: var(--gold-600); font-weight: 600; }

/* ---------- buttons ---------- */
.stButton > button {
  border-radius: 9px; border: 1px solid var(--cream-300); font-weight: 500;
  background: var(--surface); color: var(--ink);
  box-shadow: 0 1px 2px rgba(27,53,40,.05);
  transition: border-color .15s var(--ease), box-shadow .15s var(--ease),
              transform .14s var(--ease), background .15s var(--ease);
}
.stButton > button:hover {
  border-color: var(--green-600); color: var(--ink); background: var(--surface);
  transform: translateY(-1px); box-shadow: var(--edge), 0 3px 8px -2px rgba(27,53,40,.14);
}
.stButton > button:active { transform: scale(.97); box-shadow: none; }
.stButton > button[kind="primary"],
[data-testid="stBaseButton-primary"] {
  background: linear-gradient(#1D4635, var(--green-700));
  border-color: var(--green-700);
  box-shadow: inset 0 1px 0 rgba(255,255,255,.14), 0 1px 3px rgba(20,56,42,.3);
}
/* The label lives in a nested node, so colour the descendants too. */
.stButton > button[kind="primary"], .stButton > button[kind="primary"] *,
[data-testid="stBaseButton-primary"], [data-testid="stBaseButton-primary"] * {
  color: #F5F0E3 !important;
  -webkit-text-fill-color: #F5F0E3 !important;
}
.stButton > button[kind="primary"]:hover,
[data-testid="stBaseButton-primary"]:hover { filter: brightness(1.07); }
[data-testid="stSidebar"] .stButton > button:hover,
[data-testid="stSidebar"] .stButton > button:hover * {
  color: var(--green-900) !important; -webkit-text-fill-color: var(--green-900) !important;
  transform: none;
}

/* ---------- inputs & tabs ---------- */
.stTextInput input, .stTextArea textarea, .stNumberInput input {
  border-radius: 9px !important; border-color: var(--cream-300) !important;
  background: var(--surface) !important;
}
.stTextArea textarea::placeholder { font-family: var(--serif); font-style: italic; color: var(--muted); }
.stTabs [data-baseweb="tab-list"] { gap: 0.35rem; border-bottom: 1px solid var(--cream-300); }
.stTabs [data-baseweb="tab"] {
  border-radius: 8px; padding: 0.4rem 0.95rem; font-weight: 500; color: var(--muted);
}
.stTabs [aria-selected="true"] {
  background: %(cream_200)s; color: var(--ink) !important;
  box-shadow: inset 0 1px 3px rgba(27,53,40,.1), inset 0 0 0 1px var(--cream-300);
}

.stExpander { border: 1px solid var(--line-soft) !important; border-radius: 10px !important; background: var(--surface); }

[data-testid="stMetricValue"] { color: var(--ink); font-family: var(--serif); font-weight: 560; }
[data-testid="stDataFrame"] { border: 1px solid var(--line-soft); border-radius: 10px; }

.empty {
  border: 1px solid var(--line-soft); border-radius: 10px; padding: 1.9rem 1.4rem;
  text-align: center; color: var(--muted); background: %(cream_200)s;
}
.empty .big { font-family: var(--serif); font-size: 1.08rem; color: var(--ink); font-weight: 560; margin-bottom: 0.2rem; }

.subtle { color: var(--muted); font-size: 0.85rem; }
.kv { font-size: 0.88rem; padding: 0.16rem 0; }
.kv .k { color: var(--muted); display: inline-block; min-width: 120px; }
hr { border-color: var(--cream-300); }

/* ---------- flash: the preview's bottom-right pill ---------- */
.flash {
  position: fixed; right: 22px; bottom: 84px; z-index: 98;
  background: var(--green-700); color: #F3EEE0;
  padding: 0.6rem 1.15rem; border-radius: 999px; font-size: 0.88rem;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.12), 0 12px 30px -12px rgba(20,56,42,.55);
  animation: flashin .3s var(--ease) both;
}
@keyframes flashin { from { opacity: 0; transform: translateY(8px); } }

/* ---------- bordered containers read as ledger cards ---------- */
[class*="st-key-demo_"] {
  background: var(--surface); border: 1px solid var(--line-soft) !important;
  border-radius: 14px !important; box-shadow: var(--edge), var(--shadow);
  padding: 1.0rem 1.05rem !important;
}

/* ---------- assignment toast ---------- */
/* The preview's #notify banner, in Streamlit's clothing: same material,
   same gold signal, serif first line. */
[data-testid="stToast"] {
  background: var(--surface) !important; color: var(--ink) !important;
  border: 1px solid var(--cream-300); border-radius: 15px;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.8),
    0 2px 4px rgba(27,53,40,.06), 0 24px 56px -22px rgba(27,53,40,.45);
  padding: 0.85rem 1rem;
}
[data-testid="stToast"] [data-testid="stMarkdownContainer"] p { color: var(--ink); }
[data-testid="stToast"] [data-testid="stMarkdownContainer"] p strong {
  font-family: var(--serif); font-weight: 560; font-size: 1.02rem; color: var(--ink);
}
</style>
"""


def _render_css() -> str:
    css = _CSS_TEMPLATE.replace("%(fonts)s", _font_css())
    for key, value in PALETTE.items():
        css = css.replace(f"%({key})s", value)
    # Literal percent signs survive the token pass as %%.
    return css.replace("%%", "%")


CSS = _render_css()


def inject() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
