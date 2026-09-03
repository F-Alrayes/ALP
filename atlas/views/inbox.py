"""My Inbox / My Requests — both sides of every request, for the acting user."""

from __future__ import annotations

import streamlit as st

from atlas import clock
from atlas.config import OPEN_STATUSES
from atlas.db import session_scope, write_lock
from atlas.models import Message, Person, Request
from atlas.services import (

    acknowledge,
    add_note,
    complete,
    inbox_for,
    mark_read,
    messages_for_request,
    reassign,
    requests_by,
    start_progress,
    timeline,
    unread_count,
)
from atlas.ui.components import (
    badge,
    empty_state,
    esc,
    kv,
    page_header,
    status_badge,
    timeline_view,
)

OPEN_REQUEST_KEY = "atlas_open_request_id"

def _summary(session, request: Request, at) -> dict:
    assignee = session.get(Person, request.assignee_id) if request.assignee_id else None
    requester = session.get(Person, request.requester_id)
    return {
        "id": request.id,
        "title": request.title,
        "status": request.status,
        "process": request.process.name if request.process else "Unmatched",
        "assignee": assignee.name if assignee else "Unassigned",
        "requester": requester.name if requester else "—",
        "age": clock.humanize_delta(at - request.created_at),
        "since": clock.humanize_delta(at - request.last_action_at),
        "chases": request.chase_count,
        "unread": (
            session.query(Message)
            .filter(Message.request_id == request.id, Message.read.is_(False))
            .count()
        ),
    }

def _request_list(
    rows: list[dict],
    *,
    counterpart_key: str,
    counterpart_label: str,
    prefix: str,
    empty: tuple[str, str] = (
        "Nothing here.",
        "Requests will appear as they are raised or routed to you.",
    ),
) -> None:
    if not rows:
        empty_state(*empty)
        return
    for row in rows:
        card, action = st.columns([6, 1], vertical_alignment="center")
        chase_note = (
            f" · {row['chases']} chase{'s' if row['chases'] != 1 else ''}" if row["chases"] else ""
        )
        card.markdown(
            f"""<div class="card {'accent' if row['status'] in ('pending', 'escalated') else ''}">
                  <div class="card-title">#{row['id']} — {esc(row['title'])}</div>
                  <div class="card-meta">
                    {status_badge(row['status'])} &nbsp; {esc(row['process'])} ·
                    {esc(counterpart_label)} {esc(row[counterpart_key])} ·
                    {esc(row['age'])} old · quiet {esc(row['since'])}{esc(chase_note)}
                  </div>
                </div>""",
            unsafe_allow_html=True,
        )
        label = "Open" if not row["unread"] else f"Open ({row['unread']})"
        if action.button(label, icon=":material/arrow_forward:",
                         key=f"{prefix}_open_{row['id']}", width="stretch"):
            st.session_state[OPEN_REQUEST_KEY] = row["id"]
            st.rerun()

def _detail(request_id: int, actor_id: int) -> None:
    with write_lock, session_scope() as session:
        mark_read(session, actor_id, request_id)

    with session_scope() as session:
        request = session.get(Request, request_id)
        if request is None:
            st.session_state.pop(OPEN_REQUEST_KEY, None)
            st.rerun()
            return
        at = clock.now(session)
        assignee = session.get(Person, request.assignee_id) if request.assignee_id else None
        requester = session.get(Person, request.requester_id)
        original = (
            session.get(Person, request.original_assignee_id)
            if request.original_assignee_id
            else None
        )
        events = timeline(session, request_id)
        messages = [
            {
                "type": m.type,
                "body": m.body,
                "when": clock.fmt(m.created_at),
                "from": session.get(Person, m.sender_id).name if m.sender_id else "Atlas agent",
                "to": session.get(Person, m.recipient_id).name if m.recipient_id else "—",
            }
            for m in messages_for_request(session, request_id)
        ]
        people = [
            (p.id, f"{p.name} — {p.title}")
            for p in session.query(Person).order_by(Person.name).all()
        ]
        snapshot = {
            "title": request.title,
            "status": request.status,
            "body": request.body,
            "process": request.process.name if request.process else "Unmatched",
            "created": clock.fmt(request.created_at),
            "age": clock.humanize_delta(at - request.created_at),
            "chases": request.chase_count,
            "acknowledged": clock.fmt(request.acknowledged_at) if request.acknowledged_at else None,
            "completed": clock.fmt(request.completed_at) if request.completed_at else None,
            "assignee_id": request.assignee_id,
        }

    if st.button("Back to inbox", icon=":material/arrow_back:", key="back_request"):
        st.session_state.pop(OPEN_REQUEST_KEY, None)
        st.rerun()
    page_header("Requests", f"#{request_id} — {snapshot['title']}")

    st.markdown(
        f"""<div class="card accent">
              <div class="card-meta">{status_badge(snapshot['status'])} &nbsp;
                {esc(snapshot['process'])} · raised {esc(snapshot['age'])} ago</div>
              <div class="card-body">{esc(snapshot['body'])}</div>
            </div>""",
        unsafe_allow_html=True,
    )

    is_assignee = snapshot["assignee_id"] == actor_id
    is_open = snapshot["status"] in OPEN_STATUSES
    status = snapshot["status"]

    if not is_open:
        st.caption("This request is closed.")
    elif is_assignee:
        col1, col2, col3 = st.columns(3)
        if col1.button(
            "Acknowledge", icon=":material/check:", width="stretch",
            type="primary" if status in ("pending", "escalated") else "secondary",
            disabled=status not in ("pending", "escalated"),
        ):
            with write_lock, session_scope() as session:
                acknowledge(session, request_id, actor_id)
            st.rerun()
        if col2.button(
            "Mark in progress", icon=":material/pending_actions:", width="stretch",
            type="primary" if status == "acknowledged" else "secondary",
            disabled=status == "in_progress",
        ):
            with write_lock, session_scope() as session:
                start_progress(session, request_id, actor_id)
            st.rerun()
        if col3.button(
            "Complete", icon=":material/task_alt:", width="stretch",
            type="primary" if status == "in_progress" else "secondary",
        ):
            with write_lock, session_scope() as session:
                complete(session, request_id, actor_id, st.session_state.get("atlas_note_box", ""))
            st.rerun()

        note = st.text_input("Add a note (sent to the requester)", key="atlas_note_box")
        if st.button("Send note", icon=":material/send:", disabled=not note.strip()):
            with write_lock, session_scope() as session:
                add_note(session, request_id, actor_id, note)
            st.rerun()

        with st.expander("Hand this to someone else"):
            ids = [p[0] for p in people]
            labels = dict(people)
            target = st.selectbox(
                "New assignee", options=ids, format_func=lambda i: labels[i], key="atlas_reassign_to"
            )
            reason = st.text_input("Reason", key="atlas_reassign_reason")
            if st.button("Reassign", icon=":material/swap_horiz:", key="atlas_reassign_go"):
                with write_lock, session_scope() as session:
                    reassign(session, request_id, actor_id, target, reason)
                st.rerun()
    else:
        st.caption("Watching only — switch to the assignee to act.")

    left, right = st.columns([3, 2])
    with left:
        st.markdown("#### Timeline")
        timeline_view(events)

    with right:
        st.markdown("#### Detail")
        kv("Requester", esc(requester.name if requester else "—"))
        kv("Assignee", esc(assignee.name if assignee else "Unassigned"))
        if original and assignee and original.id != assignee.id:
            kv("Originally", esc(original.name) + " " + badge("rerouted", "gold"))
        kv("Raised", esc(snapshot["created"]))
        kv("Acknowledged", esc(snapshot["acknowledged"] or "—"))
        kv("Completed", esc(snapshot["completed"] or "—"))
        kv("Chases sent", esc(snapshot["chases"]))

        st.markdown("#### Messages")
        for message in messages:
            st.markdown(
                f"""<div class="card">
                      <div class="card-meta">{badge(message['type'].replace('_', ' '), 'role')}
                        &nbsp; {esc(message['from'])} → {esc(message['to'])} · {esc(message['when'])}</div>
                      <div class="card-body">{esc(message['body'])}</div>
                    </div>""",
                unsafe_allow_html=True,
            )


def render(actor_id: int) -> None:
    with session_scope() as session:
        actor = session.get(Person, actor_id)
        at = clock.now(session)
        unread = unread_count(session, actor_id)
        incoming = [_summary(session, r, at) for r in inbox_for(session, actor_id)]
        incoming_closed = [
            _summary(session, r, at)
            for r in inbox_for(session, actor_id, include_closed=True)
            if r.status == "completed"
        ]
        outgoing = [_summary(session, r, at) for r in requests_by(session, actor_id)]

    if st.session_state.get(OPEN_REQUEST_KEY):
        _detail(st.session_state[OPEN_REQUEST_KEY], actor_id)
        return

    page_header(
        "Requests",
        f"{actor.name}'s desk",
        f"{len(incoming)} open · {len(outgoing)} raised · {unread} unread",
    )

    tab_inbox, tab_mine, tab_done = st.tabs(
        [f"My inbox ({len(incoming)})", f"My requests ({len(outgoing)})", "Completed by me"]
    )
    inbox_empty = (
        "Nothing waiting on you.",
        f"Your raised requests have {unread} unread update{'s' if unread != 1 else ''}"
        " — see My requests."
        if unread and outgoing
        else "Requests routed to you land here.",
    )
    with tab_inbox:
        _request_list(
            incoming, counterpart_key="requester", counterpart_label="from", prefix="in",
            empty=inbox_empty,
        )
    with tab_mine:
        _request_list(
            outgoing, counterpart_key="assignee", counterpart_label="with", prefix="out",
            empty=("You haven't raised anything yet.",
                   "Ask Atlas on the Ask page and the request lands here."),
        )
    with tab_done:
        _request_list(
            incoming_closed, counterpart_key="requester", counterpart_label="from", prefix="done",
            empty=("Nothing completed yet.",
                   "Requests you close will be listed here."),
        )
