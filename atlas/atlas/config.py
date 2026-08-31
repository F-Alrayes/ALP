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
UI_BUILD = "Private Ledger · build 7"

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
PALETTE = {
    "green_900": "#122A20",
    "green_800": "#0F2B21",
    "green_700": "#14382A",
    "green_600": "#128A5E",
    "green_100": "#E4F0E8",
    "gold_600": "#83660A",
    "gold_500": "#A8820F",
    "gold_300": "#D9BC5C",
    "cream_100": "#FAF6EB",
    "cream_200": "#F4EEDD",
    "cream_300": "#E3DAC2",
    "ink": "#1B2721",
    "muted": "#566158",
    "danger": "#BE3E2F",
    "warn": "#B0741B",
    "ok": "#128A5E",
}

STATUS_COLORS = {
    "pending": PALETTE["warn"],
    "acknowledged": PALETTE["green_600"],
    "in_progress": PALETTE["gold_600"],
    "completed": PALETTE["ok"],
    "escalated": PALETTE["danger"],
}

OPEN_STATUSES = ("pending", "acknowledged", "in_progress", "escalated")
