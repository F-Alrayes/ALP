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
PALETTE = {
    "green_900": "#0C2A21",
    "green_800": "#123528",
    "green_700": "#1B4D3E",
    "green_600": "#26654F",
    "green_100": "#DCE8E1",
    "gold_600": "#B08A1E",
    "gold_500": "#C9A227",
    "gold_300": "#E3C765",
    "cream_100": "#FBF8F0",
    "cream_200": "#F4EEE0",
    "cream_300": "#E8DFC9",
    "ink": "#1E2A25",
    "muted": "#6B7A72",
    "danger": "#A3332B",
    "warn": "#B4761C",
    "ok": "#2E6B4F",
}

STATUS_COLORS = {
    "pending": PALETTE["warn"],
    "acknowledged": PALETTE["green_600"],
    "in_progress": PALETTE["gold_600"],
    "completed": PALETTE["ok"],
    "escalated": PALETTE["danger"],
}

OPEN_STATUSES = ("pending", "acknowledged", "in_progress", "escalated")
