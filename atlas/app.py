"""Atlas — Streamlit entry point.

Run it through ``python run.py`` (which seeds the database first) or directly
with ``streamlit run app.py`` once a database exists.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))

from atlas import agent  # noqa: E402
from atlas.config import APP_NAME, APP_TAGLINE  # noqa: E402
from atlas.db import create_all, database_is_seeded  # noqa: E402
from atlas.ui import chrome, motion, notify, theme  # noqa: E402
from views import agent_log, ask, dashboard, demo, directory, inbox  # noqa: E402

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
    # Absorb the Gemini agent's cold start (imports + runner construction,
    # several seconds) now, off-thread, so the first chat turn is fast.
    import threading

    from atlas.agents.router import warm

    threading.Thread(target=warm, daemon=True, name="adk-warm").start()
    return True


def _bridge_secrets() -> None:
    """Streamlit Cloud keeps API keys in st.secrets; the brain reads env."""
    try:
        for key in ("ANTHROPIC_API_KEY", "GOOGLE_API_KEY", "GEMINI_API_KEY",
                    "ATLAS_ADK_MODEL"):
            if key in st.secrets and not os.environ.get(key):
                os.environ[key] = st.secrets[key]
    except Exception:
        pass  # no secrets file configured — the offline matcher takes over


def main() -> None:
    _bridge_secrets()
    _bootstrap()
    theme.inject()
    theme.mode_toggle()

    if not database_is_seeded():
        st.error("The database is not seeded. Run `python run.py` from the atlas/ directory.")
        return

    actor_id, choice = chrome.render()
    notify.check(actor_id)
    chrome.flash()

    pages = {
        "Ask": ask.render,
        "People": directory.render,
        "Requests": inbox.render,
        "Dashboard": dashboard.render,
        "Agent log": agent_log.render,
        "Demo controls": demo.render,
    }
    pages[choice](actor_id)
    motion.page_glide(choice)


main()
