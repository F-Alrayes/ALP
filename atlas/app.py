"""Atlas — Streamlit entry point.

Run it through ``python run.py`` (which seeds the database first) or directly
with ``streamlit run app.py`` once a database exists.
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))

from atlas import agent  # noqa: E402
from atlas.config import APP_NAME, APP_TAGLINE  # noqa: E402
from atlas.db import create_all, database_is_seeded  # noqa: E402
from atlas.ui import chrome, notify, theme  # noqa: E402
from views import agent_log, dashboard, demo, directory, inbox, intake  # noqa: E402

st.set_page_config(
    page_title=f"{APP_NAME} — {APP_TAGLINE}",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="collapsed",
)


@st.cache_resource(show_spinner=False)
def _bootstrap() -> bool:
    """Ensure the schema exists and start the agent — once per server process."""
    create_all()
    if not database_is_seeded():
        from atlas.seed import seed

        seed()
    agent.start()
    return True


def main() -> None:
    _bootstrap()
    theme.inject()

    if not database_is_seeded():
        st.error("The database is not seeded. Run `python run.py` from the atlas/ directory.")
        return

    actor_id, choice = chrome.render()
    notify.check(actor_id)
    chrome.flash()

    pages = {
        "Ask": intake.render,
        "People": directory.render,
        "Requests": inbox.render,
        "Dashboard": dashboard.render,
        "Agent log": agent_log.render,
        "Demo controls": demo.render,
    }
    pages[choice](actor_id)


main()
