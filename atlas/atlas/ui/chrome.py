"""The console shell: a dark left rail instead of a topbar.

Brand at the top, all six pages as flat mono nav items (no More menu), the
identity switcher and the build stamp below. ``render()`` returns
(acting user id, current page) exactly as before.
"""

from __future__ import annotations

import streamlit as st

from .. import clock
from ..config import APP_NAME, UI_BUILD
from ..db import session_scope
from ..models import Person
from ..routing import is_out_of_office
from ..services import unread_count
from .components import esc

ACTOR_KEY = "atlas_actor_id"
PAGE_KEY = "atlas_page"
DEFAULT_ACTOR = "Noura Al-Sabah"

PAGES = ("Ask", "People", "Requests", "Dashboard", "Agent log", "Demo controls")

NAV_ICONS = {
    "Ask": ":material/chat:",
    "People": ":material/groups:",
    "Requests": ":material/inbox:",
    "Dashboard": ":material/monitoring:",
    "Agent log": ":material/receipt_long:",
    "Demo controls": ":material/tune:",
}

# Page names from earlier eras still arrive via stale session state.
_LEGACY = {
    "Intake": "Ask",
    "Directory & Graph": "People",
    "Agent Log": "Agent log",
}


def all_people() -> list[tuple[int, str, str, bool]]:
    with session_scope() as session:
        at = clock.now(session)
        rows = session.query(Person).order_by(Person.name).all()
        return [(p.id, p.name, p.title, is_out_of_office(p, at)) for p in rows]


def current_actor_id() -> int:
    people = all_people()
    if not people:
        raise RuntimeError("No people in the database — run the seed script.")
    valid = {p[0] for p in people}
    if st.session_state.get(ACTOR_KEY) not in valid:
        default = next((p[0] for p in people if p[1] == DEFAULT_ACTOR), people[0][0])
        st.session_state[ACTOR_KEY] = default
    return st.session_state[ACTOR_KEY]


def current_page() -> str:
    page = st.session_state.get(PAGE_KEY, "Ask")
    page = _LEGACY.get(page, page)
    if page not in PAGES:
        page = "Ask"
    return page


def _go(page: str) -> None:
    st.session_state[PAGE_KEY] = page


def render() -> tuple[int, str]:
    """Draw the rail; return (acting user id, current page)."""
    page = current_page()
    actor = current_actor_id()
    people = all_people()
    ids = [p[0] for p in people]
    labels = {p[0]: f"{p[1]} — {p[2]}" + ("  (OOO)" if p[3] else "") for p in people}

    with session_scope() as session:
        unread = unread_count(session, actor)

    with st.sidebar:
        st.markdown(
            f"""<div class="atlas-brand"><span class="name">{esc(APP_NAME.upper())}</span>
                  <span class="build">{esc(UI_BUILD)}</span></div>""",
            unsafe_allow_html=True,
        )
        for name in PAGES:
            label = name
            if name == "Requests" and unread:
                label = f"{name} · {unread}"
            st.button(
                label,
                key=f"nav_{name}",
                icon=NAV_ICONS.get(name),
                width="stretch",
                type="primary" if page == name else "secondary",
                on_click=_go,
                args=(name,),
            )
        st.markdown("---")
        st.markdown(
            "<div class='subtle' style='font-family:var(--mono);font-size:.62rem;"
            "text-transform:uppercase;letter-spacing:.12em'>Acting as</div>",
            unsafe_allow_html=True,
        )
        chosen = st.selectbox(
            "Acting as",
            options=ids,
            index=ids.index(actor),
            format_func=lambda i: labels[i],
            label_visibility="collapsed",
            key="atlas_actor_select",
        )
        st.session_state[ACTOR_KEY] = chosen

    return chosen, current_page()


def flash() -> None:
    """One-shot confirmation, bottom-right, console-styled."""
    message = st.session_state.pop("atlas_flash", None)
    if message:
        st.markdown(f'<div class="flash">{esc(message)}</div>', unsafe_allow_html=True)
