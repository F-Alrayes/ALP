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
from atlas.ui import sidebar, theme  # noqa: E402
from views import agent_log, dashboard, directory, inbox, intake  # noqa: E402

st.set_page_config(
    page_title=f"{APP_NAME} — {APP_TAGLINE}",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
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

    actor_id = sidebar.render()
    sidebar.flash()

    pages = {
        "Intake": intake.render,
        "Requests": inbox.render,
        "Directory & Graph": directory.render,
        "Agent Log": agent_log.render,
        "Dashboard": dashboard.render,
    }
    choice = st.session_state.get("atlas_page", "Intake")
    if choice not in pages:
        choice = "Intake"

    columns = st.columns(len(pages))
    for column, name in zip(columns, pages):
        if column.button(
            name,
            key=f"nav_{name}",
            width="stretch",
            type="primary" if name == choice else "secondary",
        ):
            st.session_state["atlas_page"] = name
            st.rerun()

    st.markdown("")
    pages[choice](actor_id)


main()
