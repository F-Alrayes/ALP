"""Central configuration for Atlas.

Everything is local and offline: a single SQLite file, a handful of tunable
agent thresholds, and the brand palette used by the custom CSS layer.
"""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "atlas.db"
DB_URL = f"sqlite:///{DB_PATH}"

APP_NAME = "Atlas"
APP_TAGLINE = "Responsibility, routed."
# Shown in the sidebar footer so a glance settles which build a deployment
# runs. Bump it with any visible UI change.
UI_BUILD = "Night Console · build 9"

# --- Agent thresholds (simulated hours) -------------------------------------
# Stored in settings() at seed time so they are inspectable/tunable from the DB,
# but these are the defaults the seed writes.
DEFAULT_SETTINGS = {
    "clock_offset_seconds": "0",
    "chase_after_hours": "48",
    "chase_interval_hours": "24",
    "max_chases": "2",
    "agent_tick_seconds": "2",
}

# --- Brand palette ----------------------------------------------------------
# "The Private Ledger" — the same tokens the browser preview commits to, so
# the two front ends read as one product. Warm paper, evergreen ink, one gold.
# "Night Console" — a dark operations terminal. The key names survive from
# the ledger era so every consumer keeps working; the values are the console's.
PALETTE = {
    "green_900": "#0B0E13",   # rail / deepest panel
    "green_800": "#10151C",
    "green_700": "#3D6FE0",   # primary action fill
    "green_600": "#5581E2",   # chart blue (validated on the dark surface)
    "green_100": "#1B2A45",   # accent tint
    "gold_600": "#D9A45B",    # amber text
    "gold_500": "#C08736",    # chart amber (validated)
    "gold_300": "#8A6A2B",
    "cream_100": "#0F1218",   # ground
    "cream_200": "#161C25",   # panel surface
    "cream_300": "#28313F",   # hairline border
    "ink": "#E7ECF3",
    "muted": "#93A0B4",
    "danger": "#E0685C",
    "warn": "#D9A54B",
    "ok": "#46B380",
}

STATUS_COLORS = {
    "pending": "#D9A54B",
    "acknowledged": "#58B7C4",
    "in_progress": "#5581E2",
    "completed": "#46B380",
    "escalated": "#E0685C",
}

OPEN_STATUSES = ("pending", "acknowledged", "in_progress", "escalated")
