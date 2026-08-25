#!/usr/bin/env python3
"""One command to run Atlas.

    python run.py

Creates the SQLite database if it is missing, seeds it with the demo firm, and
launches the Streamlit UI. Nothing here touches the network.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))


def ensure_database(force_reseed: bool = False) -> None:
    from atlas import config
    from atlas.db import create_all, database_is_seeded
    from atlas.seed import seed

    create_all()
    if force_reseed or not database_is_seeded():
        print("Seeding the Atlas demo database...")
        seed()
        print(f"  -> {config.DB_PATH}")
    else:
        print(f"Using the existing database at {config.DB_PATH}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Atlas prototype.")
    parser.add_argument("--port", type=int, default=8501, help="Streamlit port (default 8501)")
    parser.add_argument("--reseed", action="store_true", help="Wipe and reseed before launching")
    parser.add_argument("--seed-only", action="store_true", help="Seed the database and exit")
    parser.add_argument(
        "--headless", action="store_true", help="Do not try to open a browser window"
    )
    args = parser.parse_args()

    try:
        ensure_database(force_reseed=args.reseed)
    except ModuleNotFoundError as exc:  # pragma: no cover - first-run guidance
        print(f"Missing dependency: {exc.name}")
        print("Install the requirements first:  pip install -r requirements.txt")
        return 1

    if args.seed_only:
        return 0

    env = dict(os.environ)
    env.setdefault("STREAMLIT_BROWSER_GATHER_USAGE_STATS", "false")

    command = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(HERE / "app.py"),
        "--server.port",
        str(args.port),
        "--server.headless",
        "true" if args.headless else "false",
    ]
    print(f"Starting Atlas on http://localhost:{args.port}")
    try:
        return subprocess.call(command, cwd=str(HERE), env=env)
    except KeyboardInterrupt:  # pragma: no cover
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
