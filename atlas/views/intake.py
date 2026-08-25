"""Intake — free text in, an accountable person and a drafted request out."""

from __future__ import annotations

import streamlit as st

from atlas import clock
from atlas.db import session_scope, write_lock
from atlas.matching import match_processes, suggest_title
from atlas.models import Person, Process
from atlas.routing import resolve
from atlas.services import (
    create_request,
    draft_body,
    find_similar_open_requests,
    follow_existing,
    timeline,
)
from atlas.ui.components import (
    badge,
    empty_state,
    esc,
    kv,
    page_header,
    resolution_trace,
    status_badge,
    timeline_view,
)

QUERY_KEY = "atlas_intake_query"
OVERRIDE_KEY = "atlas_intake_override"
SENT_KEY = "atlas_intake_sent_id"

EXAMPLES = [
    "I need access to the data room for Project Falcon",
    "Invoice 88596 from Halcyon needs approving before Friday's payment run",
    "I am locked out of my account and cannot log in",
    "We need to renew the Bloomberg contract before it expires",
]


def _reset() -> None:
    for key in (QUERY_KEY, OVERRIDE_KEY, SENT_KEY, "atlas_intake_last_query"):
        st.session_state.pop(key, None)


def _use_example(example: str) -> None:
    # Widget state can only be written from a callback, never after the widget
    # has already been drawn this run.
    st.session_state[QUERY_KEY] = example
    st.session_state.pop(OVERRIDE_KEY, None)


def _sent_view(request_id: int) -> None:
    with session_scope() as session:
        from atlas.models import Request

        request = session.get(Request, request_id)
        if request is None:
            _reset()
            st.rerun()
        assignee = session.get(Person, request.assignee_id) if request.assignee_id else None
        events = timeline(session, request_id)
        process_name = request.process.name if request.process else "Unmatched"
        title = request.title
        status = request.status

    st.success(f"Request #{request_id} dispatched.")
    st.markdown(
        f"""<div class="card accent">
              <div class="card-title">#{request_id} — {esc(title)}</div>
              <div class="card-meta">{status_badge(status)} &nbsp; {esc(process_name)} ·
              assigned to {esc(assignee.name) if assignee else "the Atlas admin"}</div>
            </div>""",
        unsafe_allow_html=True,
    )
    st.markdown("#### Timeline")
    timeline_view(events)
    st.button("Raise another request", type="primary", on_click=_reset)


def render(actor_id: int) -> None:
    page_header(
        "Intake",
        "What do you need?",
        "Describe it in your own words. Atlas identifies the process, finds who is "
        "accountable right now, and drafts the request for you.",
    )

    if st.session_state.get(SENT_KEY):
        _sent_view(st.session_state[SENT_KEY])
        return

    st.text_area(
        "Your request",
        key=QUERY_KEY,
        height=110,
        placeholder="e.g. I need access to the data room for Project Falcon",
        label_visibility="collapsed",
    )

    cols = st.columns(len(EXAMPLES))
    for index, (col, example) in enumerate(zip(cols, EXAMPLES)):
        short = example if len(example) <= 34 else example[:31].rsplit(" ", 1)[0] + "..."
        col.button(
            short,
            key=f"atlas_example_{index}",
            help=example,
            width="stretch",
            on_click=_use_example,
            args=(example,),
        )

    query = (st.session_state.get(QUERY_KEY) or "").strip()
    if st.session_state.get("atlas_intake_last_query") != query:
        # A new question invalidates any manual process override.
        st.session_state["atlas_intake_last_query"] = query
        st.session_state.pop(OVERRIDE_KEY, None)
    if not query:
        st.markdown("")
        empty_state(
            "Nothing to route yet.",
            "Type a request above, or pick one of the examples to see the resolution trace.",
        )
        return

    with session_scope() as session:
        matches = match_processes(session, query, limit=3)
        all_processes = session.query(Process).order_by(Process.name).all()
        process_options = {p.id: f"{p.name} — {p.category}" for p in all_processes}

    st.markdown("## Process match")
    if not matches or matches[0].confidence < 25:
        st.warning(
            "No process matched with usable confidence. Pick one manually, or send it anyway "
            "and Atlas will park it for the admin."
        )
    top = matches[0] if matches else None

    if top is not None:
        tone = "gold" if top.confidence >= 70 else "muted"
        keywords = (
            " ".join(badge(k, "role") for k in top.matched_keywords[:6])
            or "<span class='subtle'>no direct keyword hits</span>"
        )
        st.markdown(
            f"""<div class="card accent">
                  <div class="card-title">{esc(top.process_name)} &nbsp; {badge(f"{top.confidence:.0f}% · {top.confidence_label}", tone)}</div>
                  <div class="card-meta">{esc(top.category)}</div>
                  <div class="card-body">{esc(top.why())}</div>
                  <div style="margin-top:0.5rem">{keywords}</div>
                </div>""",
            unsafe_allow_html=True,
        )
        with st.expander("Why this matched — signal breakdown"):
            for match in matches:
                st.markdown(
                    f"**{esc(match.process_name)}** — {match.confidence:.0f}%  \n"
                    + " · ".join(
                        f"{name}: {value * 100:.0f}%" for name, value in match.signals.items()
                    )
                )

    default_process_id = st.session_state.get(OVERRIDE_KEY) or (
        top.process_id if top and top.confidence >= 25 else None
    )
    option_ids = list(process_options)
    chosen_id = st.selectbox(
        "Route as",
        options=option_ids,
        index=option_ids.index(default_process_id) if default_process_id in option_ids else 0,
        format_func=lambda i: process_options[i],
    )
    if chosen_id != default_process_id:
        st.session_state[OVERRIDE_KEY] = chosen_id

    st.markdown("## Resolution trace")
    with session_scope() as session:
        process = session.get(Process, chosen_id)
        resolution = resolve(session, process)
        requester = session.get(Person, actor_id)
        default_title = suggest_title(query, process.name if process else None)
        duplicates = find_similar_open_requests(
            session,
            process_id=chosen_id,
            requester_id=actor_id,
            title=default_title,
        )
        duplicate_rows = [
            {
                "id": d.request.id,
                "title": d.request.title,
                "status": d.request.status,
                "assignee": (
                    session.get(Person, d.request.assignee_id).name
                    if d.request.assignee_id
                    else "Unassigned"
                ),
                "similarity": d.similarity,
                "reason": d.reason,
            }
            for d in duplicates
        ]
        default_body = draft_body(requester, process, resolution, query)

    resolution_trace(resolution)
    if resolution.needs_admin:
        st.error(resolution.summary)
    else:
        st.info(resolution.summary)

    if duplicate_rows:
        st.markdown("## Possible duplicate")
        st.warning(
            "An open request on this process already looks like yours. Follow it instead of "
            "adding another item to the same queue."
        )
        for row in duplicate_rows:
            card, action = st.columns([5, 1], vertical_alignment="center")
            card.markdown(
                f"""<div class="card">
                      <div class="card-title">#{row['id']} — {esc(row['title'])}</div>
                      <div class="card-meta">{status_badge(row['status'])} &nbsp;
                      with {esc(row['assignee'])} · {row['similarity']:.0f}% similar</div>
                      <div class="card-body">{esc(row['reason'])}</div>
                    </div>""",
                unsafe_allow_html=True,
            )
            if action.button("Follow", key=f"follow_{row['id']}", width="stretch"):
                with write_lock, session_scope() as session:
                    follow_existing(session, row["id"], actor_id)
                st.session_state[SENT_KEY] = row["id"]
                st.rerun()

    st.markdown("## Drafted request")
    title = st.text_input("Title", value=default_title)
    body = st.text_area("Message", value=default_body, height=210)

    target = resolution.assignee_name or "the Atlas admin (no owner resolved)"
    kv("Will be sent to", f"<strong>{esc(target)}</strong>")
    kv("Raised by", esc(requester.name if requester else ""))
    kv("Simulated time", esc(clock.fmt(clock.now())))

    send, clear = st.columns([1, 5])
    if send.button("Send request", type="primary", width="stretch"):
        with write_lock, session_scope() as session:
            created = create_request(
                session,
                requester_id=actor_id,
                process_id=chosen_id,
                assignee_id=resolution.assignee_id,
                title=title,
                body=body,
                resolution=resolution,
            )
            new_id = created.id
        st.session_state[SENT_KEY] = new_id
        st.rerun()
    if clear.button("Clear"):
        _reset()
        st.rerun()
