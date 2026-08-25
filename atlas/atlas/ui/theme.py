"""Custom CSS. Dark green, gold and cream — an internal tool, not a default app."""

from __future__ import annotations

import streamlit as st

from ..config import PALETTE

# No webfonts: Atlas must run with the network unplugged, so the type stack is
# whatever the machine already has.
_CSS_TEMPLATE = """
<style>
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
  --ink: %(ink)s;
  --muted: %(muted)s;
  --danger: %(danger)s;
  --warn: %(warn)s;
  --ok: %(ok)s;
}

html, body, [class*="css"], .stApp {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
}

.stApp { background: var(--cream-100); color: var(--ink); }

.block-container { padding-top: 2.2rem; padding-bottom: 4rem; max-width: 1240px; }

h1, h2, h3, h4 { color: var(--green-900); letter-spacing: -0.015em; font-weight: 650; }
h1 { font-size: 1.95rem; }
h2 { font-size: 1.35rem; margin-top: 1.6rem; }
h3 { font-size: 1.08rem; }
p, li, label, .stMarkdown { color: var(--ink); }

/* ---------- sidebar ---------- */
[data-testid="stSidebar"] { background: var(--green-900); border-right: 1px solid var(--green-800); }
[data-testid="stSidebar"] * { color: var(--cream-200) !important; }
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
  color: var(--cream-100) !important; letter-spacing: 0.01em;
}
[data-testid="stSidebar"] hr { border-color: rgba(233,223,201,0.18); }
[data-testid="stSidebar"] .stButton > button {
  background: rgba(233,223,201,0.08); border: 1px solid rgba(233,223,201,0.28);
  color: var(--cream-100) !important; font-weight: 550;
}
[data-testid="stSidebar"] .stButton > button:hover {
  background: var(--gold-500); border-color: var(--gold-500); color: var(--green-900) !important;
}
/* Form controls on the dark sidebar: the widget internals carry the light
   theme's own background, so blank them out and put one tinted shell around
   each control. Selectors stick to stable data-testids. */
[data-testid="stSidebar"] [data-testid="stSelectbox"] div,
[data-testid="stSidebar"] [data-testid="stSelectbox"] input,
[data-testid="stSidebar"] [data-testid="stNumberInput"] div,
[data-testid="stSidebar"] [data-testid="stNumberInput"] input,
[data-testid="stSidebar"] [data-testid="stTextInput"] div,
[data-testid="stSidebar"] [data-testid="stTextInput"] input,
[data-testid="stSidebar"] [data-baseweb="select"] div {
  background-color: transparent !important;
  color: var(--cream-100) !important;
  -webkit-text-fill-color: var(--cream-100) !important;
}
[data-testid="stSidebar"] [data-testid="stSelectbox"] > div,
[data-testid="stSidebar"] [data-testid="stNumberInput"] > div,
[data-testid="stSidebar"] [data-testid="stTextInput"] > div {
  background-color: rgba(233,223,201,0.12) !important;
  border: 1px solid rgba(233,223,201,0.30) !important;
  border-radius: 8px !important;
}
[data-testid="stSidebar"] svg { fill: var(--cream-200); }
/* The dropdown itself renders on the light body, so keep it readable there. */
[role="listbox"], [data-baseweb="popover"] { color: var(--ink); }
[data-testid="stSidebarNav"] { padding-top: 0.4rem; }

/* ---------- brand block ---------- */
.atlas-brand { padding: 0.2rem 0 1.0rem 0; }
.atlas-brand .mark {
  display: inline-flex; align-items: center; justify-content: center;
  width: 34px; height: 34px; border-radius: 9px; background: var(--gold-500);
  color: var(--green-900) !important; font-weight: 800; font-size: 1.05rem; margin-right: 0.6rem;
}
.atlas-brand .name { font-size: 1.25rem; font-weight: 700; letter-spacing: 0.04em; }
.atlas-brand .tag { font-size: 0.74rem; opacity: 0.72; letter-spacing: 0.12em; text-transform: uppercase; }

/* ---------- page header ---------- */
.page-head { border-bottom: 1px solid var(--cream-300); padding-bottom: 0.9rem; margin-bottom: 1.4rem; }
.page-head .eyebrow {
  font-size: 0.72rem; letter-spacing: 0.16em; text-transform: uppercase;
  color: var(--gold-600); font-weight: 650;
}
.page-head h1 { margin: 0.25rem 0 0.35rem 0; }
.page-head .sub { color: var(--muted); font-size: 0.94rem; margin: 0; }

/* ---------- cards ---------- */
.card {
  background: #fff; border: 1px solid var(--cream-300); border-radius: 12px;
  padding: 1.05rem 1.2rem; margin-bottom: 0.85rem;
  box-shadow: 0 1px 2px rgba(18,53,40,0.04);
}
.card.accent { border-left: 4px solid var(--gold-500); }
.card .card-title { font-weight: 650; color: var(--green-900); font-size: 1.0rem; margin-bottom: 0.15rem; }
.card .card-meta { color: var(--muted); font-size: 0.82rem; }
.card .card-body { margin-top: 0.55rem; font-size: 0.92rem; white-space: pre-wrap; }

.stat {
  background: #fff; border: 1px solid var(--cream-300); border-radius: 12px;
  padding: 0.95rem 1.1rem; height: 100%;
}
.stat .label {
  font-size: 0.7rem; letter-spacing: 0.13em; text-transform: uppercase;
  color: var(--muted); font-weight: 650;
}
.stat .value { font-size: 1.75rem; font-weight: 700; color: var(--green-900); line-height: 1.25; }
.stat .delta { font-size: 0.8rem; color: var(--muted); }
.stat.warn { border-left: 4px solid var(--warn); }
.stat.danger { border-left: 4px solid var(--danger); }
.stat.ok { border-left: 4px solid var(--ok); }

/* ---------- badges ---------- */
.badge {
  display: inline-block; padding: 0.14rem 0.55rem; border-radius: 999px;
  font-size: 0.72rem; font-weight: 650; letter-spacing: 0.03em;
  border: 1px solid transparent; white-space: nowrap;
}
.badge.pending { background: #FBF0DC; color: #8A5A12; border-color: #EBD6A9; }
.badge.acknowledged { background: #E1EEE7; color: #1C5540; border-color: #BFDACD; }
.badge.in_progress { background: #FAF0D3; color: #8A6A0F; border-color: #E8D493; }
.badge.completed { background: #E2F0E7; color: #24614A; border-color: #BCDCC8; }
.badge.escalated { background: #F8E2E0; color: #8C2A22; border-color: #E9BEB9; }
.badge.ooo { background: #F3E7CE; color: #7A5A12; border-color: #E1CB96; }
.badge.role { background: var(--green-100); color: var(--green-800); border-color: #C6D9CE; }
.badge.gold { background: #F7ECC9; color: #7A5C10; border-color: #E6D296; }
.badge.muted { background: var(--cream-200); color: var(--muted); border-color: var(--cream-300); }

/* ---------- resolution trace ---------- */
.trace { border-left: 2px solid var(--cream-300); margin: 0.4rem 0 0.4rem 0.6rem; padding-left: 1.05rem; }
.trace .step { position: relative; padding: 0.5rem 0; }
.trace .step:before {
  content: ''; position: absolute; left: -1.42rem; top: 0.85rem;
  width: 11px; height: 11px; border-radius: 50%; border: 2px solid #fff;
}
.trace .step.ok:before { background: var(--ok); }
.trace .step.warn:before { background: var(--warn); }
.trace .step.fail:before { background: var(--danger); }
.trace .step .label { font-weight: 650; font-size: 0.88rem; color: var(--green-900); }
.trace .step .detail { font-size: 0.88rem; color: #40514A; }

/* ---------- timeline ---------- */
.timeline { border-left: 2px solid var(--cream-300); margin-left: 0.55rem; padding-left: 1.05rem; }
.timeline .entry { position: relative; padding: 0.45rem 0; }
.timeline .entry:before {
  content: ''; position: absolute; left: -1.36rem; top: 0.8rem;
  width: 9px; height: 9px; border-radius: 50%; background: var(--green-600); border: 2px solid #fff;
}
.timeline .entry.agent:before { background: var(--gold-500); }
.timeline .entry.alert:before { background: var(--danger); }
.timeline .when { font-size: 0.74rem; color: var(--muted); letter-spacing: 0.02em; }
.timeline .what { font-size: 0.88rem; color: var(--ink); }
.timeline .who { font-size: 0.74rem; color: var(--gold-600); font-weight: 600; }

/* ---------- buttons ---------- */
.stButton > button {
  border-radius: 8px; border: 1px solid var(--cream-300); font-weight: 550;
  background: #fff; color: var(--green-800); transition: all 0.12s ease;
}
.stButton > button:hover { border-color: var(--green-600); color: var(--green-900); background: #fff; }
.stButton > button[kind="primary"],
[data-testid="stBaseButton-primary"] {
  background: var(--green-700); border-color: var(--green-700);
}
/* The label lives in a nested node, so colour the descendants too. */
.stButton > button[kind="primary"], .stButton > button[kind="primary"] *,
[data-testid="stBaseButton-primary"], [data-testid="stBaseButton-primary"] * {
  color: var(--cream-100) !important;
  -webkit-text-fill-color: var(--cream-100) !important;
}
.stButton > button[kind="primary"]:hover,
[data-testid="stBaseButton-primary"]:hover {
  background: var(--green-800); border-color: var(--green-800);
}
[data-testid="stSidebar"] .stButton > button:hover,
[data-testid="stSidebar"] .stButton > button:hover * {
  color: var(--green-900) !important; -webkit-text-fill-color: var(--green-900) !important;
}

/* ---------- inputs & tabs ---------- */
.stTextInput input, .stTextArea textarea, .stNumberInput input {
  border-radius: 8px !important; border-color: var(--cream-300) !important; background: #fff !important;
}
.stTabs [data-baseweb="tab-list"] { gap: 0.35rem; border-bottom: 1px solid var(--cream-300); }
.stTabs [data-baseweb="tab"] {
  border-radius: 8px 8px 0 0; padding: 0.4rem 0.95rem; font-weight: 550; color: var(--muted);
}
.stTabs [aria-selected="true"] { background: #fff; color: var(--green-900) !important; border: 1px solid var(--cream-300); border-bottom: none; }

.stExpander { border: 1px solid var(--cream-300) !important; border-radius: 10px !important; background: #fff; }

[data-testid="stMetricValue"] { color: var(--green-900); font-weight: 700; }
[data-testid="stDataFrame"] { border: 1px solid var(--cream-300); border-radius: 10px; }

.empty {
  border: 1px dashed var(--cream-300); border-radius: 12px; padding: 1.8rem 1.4rem;
  text-align: center; color: var(--muted); background: #FFFDF8;
}
.empty .big { font-size: 1.0rem; color: var(--green-800); font-weight: 600; margin-bottom: 0.2rem; }

.subtle { color: var(--muted); font-size: 0.85rem; }
.kv { font-size: 0.88rem; padding: 0.16rem 0; }
.kv .k { color: var(--muted); display: inline-block; min-width: 120px; }
hr { border-color: var(--cream-300); }
footer, #MainMenu { visibility: hidden; }
</style>
"""


def _render_css() -> str:
    css = _CSS_TEMPLATE
    for key, value in PALETTE.items():
        css = css.replace(f"%({key})s", value)
    return css


CSS = _render_css()


def inject() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
