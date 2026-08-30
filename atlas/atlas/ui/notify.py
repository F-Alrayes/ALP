"""Assignment notifications — a toast when a request lands on you.

Mirror of the preview's #notify banner. Streamlit reruns the whole script
per interaction, so "new" is a diff against the set of open requests that
were already assigned to the acting user on the previous run. Switching who
you act as re-baselines silently: the toast announces things that happen
while you watch, not a recap of your inbox.
"""

from __future__ import annotations

import streamlit as st

from ..config import OPEN_STATUSES
from ..db import session_scope
from ..models import Person, Request

SEEN_KEY = "atlas_notify_seen"       # (actor_id, frozenset of request ids)
MAX_TOASTS = 3


def _assigned_now(actor_id: int) -> dict[int, tuple[str, str]]:
    """Open requests sitting with the actor: id -> (title, requester name)."""
    with session_scope() as session:
        rows = (
            session.query(Request)
            .filter(Request.status.in_(OPEN_STATUSES), Request.assignee_id == actor_id)
            .all()
        )
        out: dict[int, tuple[str, str]] = {}
        for request in rows:
            if request.requester_id == actor_id:
                continue  # your own request landing back on you is not news
            requester = (
                session.get(Person, request.requester_id) if request.requester_id else None
            )
            out[request.id] = (request.title, requester.name if requester else "the agent")
        return out


def check(actor_id: int) -> None:
    """Raise a toast for every request newly routed to the acting user."""
    assigned = _assigned_now(actor_id)
    previous = st.session_state.get(SEEN_KEY)

    if previous is None or previous[0] != actor_id:
        st.session_state[SEEN_KEY] = (actor_id, frozenset(assigned))
        return

    fresh = [rid for rid in assigned if rid not in previous[1]]
    for rid in fresh[-MAX_TOASTS:]:
        title, requester = assigned[rid]
        st.toast(
            f"**New request for you**  \n#{rid} — {title}  \nfrom {requester} · "
            "open the Requests page",
            icon="🔔",
        )
    st.session_state[SEEN_KEY] = (actor_id, frozenset(assigned))
