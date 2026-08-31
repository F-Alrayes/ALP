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
UI_BUILD = "Paper Console · build 13"

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
# "Paper Console" — the console layout wearing the original ledger palette:
# warm cream ground, evergreen ink, one gold accent. Key names are structural
# slots (accent fill, chart series, surfaces), not literal colors.
PALETTE = {
    "green_900": "#122A20",   # rail — the dark evergreen study
    "green_800": "#0F2B21",
    "green_700": "#14382A",   # primary action fill
    "green_600": "#128A5E",   # chart green (validated on the cream surface)
    "green_100": "#E4F0E8",   # accent tint
    "gold_600": "#83660A",    # gold text
    "gold_500": "#A8820F",    # chart gold (validated)
    "gold_300": "#D9BC5C",
    "cream_100": "#FAF6EB",   # ground
    "cream_200": "#FFFDF6",   # panel surface
    "cream_300": "#E3DAC2",   # hairline border
    "ink": "#1B2721",
    "muted": "#566158",
    "danger": "#BE3E2F",
    "warn": "#B0741B",
    "ok": "#128A5E",
}

STATUS_COLORS = {
    "pending": "#B0741B",
    "acknowledged": "#128A5E",
    "in_progress": "#83660A",
    "completed": "#128A5E",
    "escalated": "#BE3E2F",
}

OPEN_STATUSES = ("pending", "acknowledged", "in_progress", "escalated")
