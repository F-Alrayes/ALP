"""Agent Log — every autonomous action, with its reason and timestamp."""

from __future__ import annotations

import streamlit as st

from atlas import agent, clock
from atlas.db import session_scope
from atlas.models import Event, Request
from atlas.ui.components import (
    AGENT_EVENT_TYPES,
    EVENT_LABELS,
    badge,
    empty_state,
    esc,
    page_header,
    stat,
)

FILTERS = {
    "Autonomous actions": sorted(AGENT_EVENT_TYPES),
    "Chases": ["chase"],
    "Reroutes": ["reroute", "reroute_ooo", "reroute_chase"],
    "Escalations": ["escalation", "escalation_blocked"],
    "Routing decisions": ["routing", "dispatch", "orphan"],
    "Everything": [],
}


def render(actor_id: int) -> None:
    state = agent.status()
    page_header(
        "Agent log",
        "What the agent did, and why",
        "No entry here was triggered by a human.",
    )

    with session_scope() as session:
        at = clock.now(session)
        totals = {
            "chase": session.query(Event).filter(Event.type == "chase").count(),
            "reroute": session.query(Event)
            .filter(Event.type.in_(("reroute_ooo", "reroute_chase")))
            .count(),
            "escalation": session.query(Event).filter(Event.type == "escalation").count(),
        }

    cols = st.columns(4)
    with cols[0]:
        stat("Agent", "Running" if state["running"] else "Stopped",
             f"last pass {clock.fmt(state['last_tick_at'])}" if state["last_tick_at"] else "not yet run",
             "ok" if state["running"] else "warn")
    with cols[1]:
        stat("Chases sent", str(totals["chase"]), "unacknowledged after 48h")
    with cols[2]:
        stat("Reroutes", str(totals["reroute"]), "cover picked up the work")
    with cols[3]:
        stat("Escalations", str(totals["escalation"]), "handed to a manager", "danger" if totals["escalation"] else "")

    if state["error"]:
        with st.expander("Last agent error", expanded=False):
            st.code(str(state["error"]))

    col1, col2 = st.columns([2, 1], vertical_alignment="bottom")
    choice = col1.selectbox("Show", list(FILTERS), key="agent_log_filter")
    if col2.button("Run the agent now", width="stretch"):
        actions = agent.run_until_settled()
        st.toast(f"Agent took {actions} action{'s' if actions != 1 else ''}.")
        st.rerun()

    types = FILTERS[choice]
    with session_scope() as session:
        query = session.query(Event)
        if types:
            query = query.filter(Event.type.in_(types))
        events = query.order_by(Event.created_at.desc(), Event.id.desc()).limit(200).all()
        rows = []
        for event in events:
            request = session.get(Request, event.request_id) if event.request_id else None
            rows.append(
                {
                    "when": clock.fmt(event.created_at),
                    "ago": clock.humanize_delta(at - event.created_at),
                    "type": event.type,
                    "label": EVENT_LABELS.get(event.type, event.type.replace("_", " ").title()),
                    "detail": event.detail,
                    "actor": event.actor,
                    "request_id": event.request_id,
                    "request_title": request.title if request else None,
                }
            )

    st.caption(f"{len(rows)} entries · simulated time {clock.fmt(at)}")
    if not rows:
        empty_state(
            "The agent has not needed to act yet.",
            "Advance the simulated clock in the sidebar to make chases and escalations fire.",
        )
        return

    for row in rows:
        tone = "escalated" if row["type"].startswith("escalation") else (
            "gold" if row["type"] in AGENT_EVENT_TYPES else "muted"
        )
        context = (
            f"#{row['request_id']} — {row['request_title']}"
            if row["request_id"] and row["request_title"]
            else "no request"
        )
        st.markdown(
            f"""<div class="card">
                  <div class="card-meta">{badge(row['label'], tone)} &nbsp;
                    {esc(row['when'])} · {esc(row['ago'])} ago ·
                    <strong>{esc(row['actor'])}</strong> · {esc(context)}</div>
                  <div class="card-body">{esc(row['detail'])}</div>
                </div>""",
            unsafe_allow_html=True,
        )
