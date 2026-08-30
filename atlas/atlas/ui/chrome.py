"""The app shell, matched to the preview: a glass topbar instead of a sidebar.

Brand on the left, the three primary tabs beside it, a More menu for the
rest, and the identity switcher on the right — the same furniture in the
same places as the single-file preview. The demo controls that used to
live in the sidebar are a page now (views/demo.py), exactly as they are
in the preview.
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

PRIMARY = ("Ask", "People", "Requests")
MORE = ("Dashboard", "Agent log", "Demo controls")

# Old sidebar-era page names still arrive via stale session state.
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
    if page not in PRIMARY + MORE:
        page = "Ask"
    return page


def _go(page: str) -> None:
    st.session_state[PAGE_KEY] = page


def render() -> tuple[int, str]:
    """Draw the topbar; return (acting user id, current page)."""
    page = current_page()
    actor = current_actor_id()
    people = all_people()
    ids = [p[0] for p in people]
    labels = {p[0]: f"{p[1]} — {p[2]}" + ("  (OOO)" if p[3] else "") for p in people}

    with session_scope() as session:
        unread = unread_count(session, actor)

    with st.container(key="atlas_topbar"):
        brand, t1, t2, t3, more, spacer, who = st.columns(
            [2.45, 0.62, 0.82, 1.15, 0.95, 2.4, 2.6], vertical_alignment="center"
        )
        brand.markdown(
            f"""<div class="atlas-brand"><span class="mark">A</span>
                  <span class="name">{esc(APP_NAME.upper())}</span>
                  <span class="build">{esc(UI_BUILD)}</span></div>""",
            unsafe_allow_html=True,
        )
        for col, name in zip((t1, t2, t3), PRIMARY):
            label = name
            if name == "Requests" and unread:
                label = f"{name} · {unread}"
            col.button(
                label,
                key=f"nav_{name}",
                width="stretch",
                type="primary" if page == name else "secondary",
                on_click=_go,
                args=(name,),
            )
        with more:
            with st.popover(
                page if page in MORE else "More", width="stretch"
            ):
                for name in MORE:
                    st.button(
                        name,
                        key=f"nav_more_{name}",
                        width="stretch",
                        type="primary" if page == name else "secondary",
                        on_click=_go,
                        args=(name,),
                    )
        spacer.empty()
        chosen = who.selectbox(
            "You are",
            options=ids,
            index=ids.index(actor),
            format_func=lambda i: labels[i],
            label_visibility="collapsed",
            key="atlas_actor_select",
        )
        st.session_state[ACTOR_KEY] = chosen

    return chosen, current_page()


def flash() -> None:
    """The preview's bottom-right flash pill, not a banner across the page."""
    message = st.session_state.pop("atlas_flash", None)
    if message:
        st.markdown(f'<div class="flash">{esc(message)}</div>', unsafe_allow_html=True)
