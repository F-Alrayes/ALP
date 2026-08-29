"""Sidebar: identity switcher, simulated clock and the demo controls."""

from __future__ import annotations

from datetime import timedelta

import streamlit as st

from .. import agent, clock
from ..config import APP_NAME, APP_TAGLINE, UI_BUILD
from ..db import session_scope
from ..models import Person
from ..routing import is_out_of_office
from ..services import set_ooo, unread_count
from .components import esc

ACTOR_KEY = "atlas_actor_id"
DEFAULT_ACTOR = "Noura Al-Sabah"


def _all_people() -> list[tuple[int, str, str, bool]]:
    with session_scope() as session:
        at = clock.now(session)
        rows = session.query(Person).order_by(Person.name).all()
        return [(p.id, p.name, p.title, is_out_of_office(p, at)) for p in rows]


def current_actor_id() -> int:
    people = _all_people()
    if not people:
        raise RuntimeError("No people in the database — run the seed script.")
    valid = {p[0] for p in people}
    if st.session_state.get(ACTOR_KEY) not in valid:
        default = next((p[0] for p in people if p[1] == DEFAULT_ACTOR), people[0][0])
        st.session_state[ACTOR_KEY] = default
    return st.session_state[ACTOR_KEY]


def _brand() -> None:
    st.sidebar.markdown(
        f"""<div class="atlas-brand">
              <span class="mark">A</span>
              <span class="name">{esc(APP_NAME.upper())}</span><br/>
              <span class="tag">{esc(APP_TAGLINE)}</span><br/>
              <span class="tag" style="opacity:.55">{esc(UI_BUILD)}</span>
            </div>""",
        unsafe_allow_html=True,
    )


def _actor_switcher() -> int:
    people = _all_people()
    current = current_actor_id()
    ids = [p[0] for p in people]
    labels = {p[0]: f"{p[1]} — {p[2]}" + ("  (OOO)" if p[3] else "") for p in people}

    st.sidebar.markdown("**Acting as**")
    chosen = st.sidebar.selectbox(
        "Acting as",
        options=ids,
        index=ids.index(current),
        format_func=lambda i: labels[i],
        label_visibility="collapsed",
        key="atlas_actor_select",
    )
    # No st.rerun() here: the selectbox has already triggered one, and the
    # sidebar renders before the page body, so writing the state is enough.
    # Forcing a second run re-mounts the widget and pops the list back open.
    st.session_state[ACTOR_KEY] = chosen

    with session_scope() as session:
        unread = unread_count(session, chosen)
    if unread:
        st.sidebar.caption(f"{unread} unread message{'s' if unread != 1 else ''} in your inbox.")
    else:
        st.sidebar.caption("Inbox clear.")
    return chosen


def _clock_panel() -> None:
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Simulated clock**")
    with session_scope() as session:
        simulated = clock.now(session)
    offset = clock.offset_hours()
    st.sidebar.markdown(
        f"<div class='subtle'>{esc(clock.fmt(simulated))}<br/>offset {offset:+.0f}h from real time</div>",
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.sidebar.columns(3)
    advanced = None
    if col1.button("+1h", width="stretch", key="adv1"):
        advanced = 1
    if col2.button("+24h", width="stretch", key="adv24"):
        advanced = 24
    if col3.button("+48h", width="stretch", key="adv48"):
        advanced = 48

    custom = st.sidebar.number_input(
        "Advance by (hours)", min_value=1, max_value=720, value=24, step=1, key="adv_custom_hours"
    )
    if st.sidebar.button("Advance clock", width="stretch", key="adv_custom"):
        advanced = int(custom)

    if advanced:
        clock.advance(advanced)
        actions = agent.run_until_settled()
        st.session_state["atlas_flash"] = (
            f"Advanced {advanced}h. The agent took {actions} action{'s' if actions != 1 else ''}."
        )
        st.rerun()

    if st.sidebar.button("Reset clock to real time", width="stretch", key="clock_reset"):
        clock.reset()
        st.session_state["atlas_flash"] = "Simulated clock reset to real time."
        st.rerun()


def _ooo_panel() -> None:
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Out of office**")
    people = _all_people()
    ids = [p[0] for p in people]
    labels = {p[0]: p[1] + ("  (OOO)" if p[3] else "") for p in people}
    target = st.sidebar.selectbox(
        "Person",
        options=ids,
        format_func=lambda i: labels[i],
        key="atlas_ooo_person",
        label_visibility="collapsed",
    )
    currently_ooo = next(p[3] for p in people if p[0] == target)
    days = st.sidebar.number_input(
        "Away for (days)", min_value=1, max_value=60, value=5, step=1, key="atlas_ooo_days"
    )
    label = "Mark back in office" if currently_ooo else "Mark out of office"
    if st.sidebar.button(label, width="stretch", key="atlas_ooo_toggle"):
        if currently_ooo:
            set_ooo(target, False)
        else:
            with session_scope() as session:
                until = clock.now(session) + timedelta(days=int(days))
            set_ooo(target, True, until)
        actions = agent.run_until_settled()
        name = labels[target].replace("  (OOO)", "")
        st.session_state["atlas_flash"] = (
            f"{name} is now {'back in the office' if currently_ooo else 'out of office'}. "
            f"The agent took {actions} action{'s' if actions != 1 else ''}."
        )
        st.rerun()


def _agent_panel() -> None:
    st.sidebar.markdown("---")
    state = agent.status()
    dot = "🟢" if state["running"] else "⚪"
    st.sidebar.markdown(f"**Agent** {dot}")
    last = state["last_tick_at"]
    st.sidebar.markdown(
        f"<div class='subtle'>{'Running every 2s' if state['running'] else 'Stopped'}<br/>"
        f"last evaluated {esc(clock.fmt(last)) if last else '—'}</div>",
        unsafe_allow_html=True,
    )
    if state["error"]:
        st.sidebar.error("Agent error — see the Agent Log page.")
    if st.sidebar.button("Run agent now", width="stretch", key="agent_now"):
        actions = agent.run_until_settled()
        st.session_state["atlas_flash"] = (
            f"Agent evaluated its rules and took {actions} action{'s' if actions != 1 else ''}."
        )
        st.rerun()


def _reset_panel() -> None:
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Database**")
    if st.session_state.get("atlas_confirm_reset"):
        st.sidebar.warning("This wipes all requests and reseeds.")
        col1, col2 = st.sidebar.columns(2)
        if col1.button("Confirm", width="stretch", key="reset_yes", type="primary"):
            from ..seed import seed

            seed()
            for key in list(st.session_state.keys()):
                if key.startswith("atlas_"):
                    del st.session_state[key]
            st.session_state["atlas_flash"] = "Database reset and reseeded."
            st.rerun()
        if col2.button("Cancel", width="stretch", key="reset_no"):
            st.session_state["atlas_confirm_reset"] = False
            st.rerun()
    else:
        if st.sidebar.button("Reset & reseed", width="stretch", key="reset_start"):
            st.session_state["atlas_confirm_reset"] = True
            st.rerun()


def render() -> int:
    """Draw the whole sidebar and return the acting user's id."""
    _brand()
    actor_id = _actor_switcher()
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Demo controls**")
    st.sidebar.caption("Nothing here exists in a real deployment — it is how the prototype is driven.")
    _clock_panel()
    _ooo_panel()
    _agent_panel()
    _reset_panel()
    return actor_id


def flash() -> None:
    """Show and clear the one-shot message set by the demo controls."""
    message = st.session_state.pop("atlas_flash", None)
    if message:
        st.success(message)
