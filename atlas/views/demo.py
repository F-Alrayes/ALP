"""Demo controls — the simulated clock, OOO switches and the agent, as a page.

The same four cards as the preview's demo page. Nothing here exists in a
real deployment; it is how the prototype is driven.
"""

from __future__ import annotations

from datetime import timedelta

import streamlit as st

from atlas import agent, clock
from atlas.db import session_scope
from atlas.services import set_ooo
from atlas.ui.chrome import all_people
from atlas.ui.components import esc, page_header


def _flash(message: str) -> None:
    st.session_state["atlas_flash"] = message


def _clock_card() -> None:
    with st.container(border=True):
        st.markdown("**Simulated clock**")
        with session_scope() as session:
            simulated = clock.now(session)
        offset = clock.offset_hours()
        st.markdown(
            f"<div class='mono'>{esc(clock.fmt(simulated))}</div>"
            f"<div class='subtle'>{offset:+.0f}h from real time</div>",
            unsafe_allow_html=True,
        )
        st.caption("Move it forward and the agent's 48-hour rules fire now.")

        advanced = None
        col1, col2, col3 = st.columns(3)
        if col1.button("+1h", width="stretch", key="adv1"):
            advanced = 1
        if col2.button("+24h", width="stretch", key="adv24"):
            advanced = 24
        if col3.button("+48h", width="stretch", key="adv48"):
            advanced = 48
        custom = st.number_input(
            "Advance by (hours)", min_value=1, max_value=720, value=24, step=1,
            key="adv_custom_hours",
        )
        cadv, creset = st.columns(2)
        if cadv.button("Advance", width="stretch", key="adv_custom"):
            advanced = int(custom)
        if advanced:
            clock.advance(advanced)
            actions = agent.run_until_settled()
            _flash(f"Advanced {advanced}h. The agent took {actions} "
                   f"action{'s' if actions != 1 else ''}.")
            st.rerun()
        if creset.button("Reset", width="stretch", key="clock_reset"):
            clock.reset()
            _flash("Simulated clock reset to real time.")
            st.rerun()


def _ooo_card() -> None:
    with st.container(border=True):
        st.markdown("**Out of office**")
        st.caption("The agent reroutes their open work to a delegate.")
        people = all_people()
        ids = [p[0] for p in people]
        labels = {p[0]: p[1] + ("  (OOO)" if p[3] else "") for p in people}
        target = st.selectbox(
            "Person", options=ids, format_func=lambda i: labels[i],
            key="atlas_ooo_person", label_visibility="collapsed",
        )
        currently_ooo = next(p[3] for p in people if p[0] == target)
        days = st.number_input(
            "Away for (days)", min_value=1, max_value=60, value=5, step=1,
            key="atlas_ooo_days",
        )
        label = "Mark back in office" if currently_ooo else "Mark away"
        if st.button(label, width="stretch", key="atlas_ooo_toggle"):
            if currently_ooo:
                set_ooo(target, False)
            else:
                with session_scope() as session:
                    until = clock.now(session) + timedelta(days=int(days))
                set_ooo(target, True, until)
            actions = agent.run_until_settled()
            name = labels[target].replace("  (OOO)", "")
            _flash(f"{name} is now "
                   f"{'back in the office' if currently_ooo else 'out of office'}. "
                   f"The agent took {actions} action{'s' if actions != 1 else ''}.")
            st.rerun()


def _agent_card() -> None:
    with st.container(border=True):
        state = agent.status()
        dot = "🟢" if state["running"] else "⚪"
        st.markdown(f"**Agent** {dot}")
        last = state["last_tick_at"]
        st.markdown(
            f"<div class='subtle'>{'Every 2s' if state['running'] else 'Stopped'}"
            f" · last pass {esc(clock.fmt(last)) if last else '—'}</div>",
            unsafe_allow_html=True,
        )
        if state["error"]:
            st.error("Agent error — see the Agent log page.")
        if st.button("Run it now", width="stretch", key="agent_now"):
            actions = agent.run_until_settled()
            _flash(f"Agent evaluated its rules and took {actions} "
                   f"action{'s' if actions != 1 else ''}.")
            st.rerun()


def _reset_card() -> None:
    with st.container(border=True):
        st.markdown("**Start over**")
        st.caption("Back to the starting state.")
        if st.session_state.get("atlas_confirm_reset"):
            st.warning("This wipes all requests and reseeds.")
            col1, col2 = st.columns(2)
            if col1.button("Confirm", width="stretch", key="reset_yes", type="primary"):
                from atlas.seed import seed

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
            if st.button("Reset & reseed", width="stretch", key="reset_start"):
                st.session_state["atlas_confirm_reset"] = True
                st.rerun()


def render(actor_id: int) -> None:  # actor_id unused; the signature matches the other pages
    page_header(
        "Demo",
        "Demo controls",
        "None of this exists in a real deployment.",
    )
    col1, col2, col3 = st.columns(3)
    with col1:
        _clock_card()
    with col2:
        _ooo_card()
    with col3:
        _agent_card()
    col4, _ = st.columns([1, 2])
    with col4:
        _reset_card()
