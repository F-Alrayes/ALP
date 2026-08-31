"""Ask — the conversation. The preview's chat, in the Streamlit body.

One message list in session state; every bubble is re-rendered from live data
each run so status changes show up. Understanding comes from atlas.brain
(Claude when a key is configured, the deterministic matcher otherwise);
routing always comes from the responsibility graph.
"""

from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components

from atlas import brain, clock
from atlas.config import OPEN_STATUSES
from atlas.db import session_scope, write_lock
from atlas.models import Person, Process, Request
from atlas.routing import is_out_of_office, resolve
from atlas.services import (
    create_request,
    draft_body,
    find_similar_open_requests,
    follow_existing,
    withdraw_request,
)
from atlas.ui.components import esc, resolution_trace, status_badge

CHAT_KEY = "atlas_chat"
DRAFT_KEY = "atlas_draft"
PENDING_KEY = "atlas_chat_pending"
SEEN_KEY = "atlas_chat_seen"

# (label shown on the chip, full ask sent to the bot)
SUGGESTIONS = [
    ("Fix my laptop", "Who do I contact to get my laptop fixed?",
     ":material/build:"),
    ("Data room access", "Email whoever owns the data room and ask them for access",
     ":material/key:"),
    ("Expense sign-off", "Ask whoever approves expenses to sign off my claim",
     ":material/approval:"),
    ("What's in my inbox?", "What's in my inbox?",
     ":material/mail:"),
]

GREETING = (
    "What can I take off your plate? Describe the problem — I find who is "
    "accountable and draft the request."
)


def _messages() -> list[dict]:
    if CHAT_KEY not in st.session_state:
        st.session_state[CHAT_KEY] = [
            {"role": "bot", "kind": "text", "text": GREETING},
        ]
    return st.session_state[CHAT_KEY]


def _push(role: str, kind: str, **data) -> None:
    _messages().append({"role": role, "kind": kind, **data})


def _queue(text: str) -> None:
    st.session_state[PENDING_KEY] = text


# --- bubble rendering --------------------------------------------------------


def _bub_user(text: str) -> str:
    return f'<div class="msg user"><div class="bub">{esc(text)}</div></div>'


def _bub_bot(inner_html: str) -> str:
    return (
        '<div class="msg bot"><span class="ava">A</span>'
        f'<div class="bub">{inner_html}</div></div>'
    )


def _render_message(session, message: dict) -> str:
    kind = message["kind"]
    if message["role"] == "user":
        return _bub_user(message.get("text", ""))
    if kind == "text":
        body = "".join(f"<p>{esc(p)}</p>" for p in message["text"].split("\n") if p)
        return _bub_bot(body)
    if kind in ("sent", "followed"):
        request = session.get(Request, message["id"])
        if request is None:
            return _bub_bot("<p>That request no longer exists.</p>")
        assignee = session.get(Person, request.assignee_id) if request.assignee_id else None
        verb = "You're now following it" if kind == "followed" else "Sent"
        note = esc(message.get("note", ""))
        return _bub_bot(
            (f"<p>{note}</p>" if note else "")
            + f"""<div class="chatcard">
              <div class="cc-title">#{request.id} — {esc(request.title)}</div>
              <div class="cc-meta">{status_badge(request.status)} &nbsp; with
                <strong>{esc(assignee.name) if assignee else 'the Atlas admin'}</strong>
                {('· ' + esc(assignee.title)) if assignee else ''}</div>
            </div>
            <p class="small">{esc(verb)} — I'll chase in 48h and escalate if it
            stalls. Track it under Requests.</p>"""
        )
    if kind == "reqlist":
        rows = (
            session.query(Request)
            .filter(Request.id.in_(message["ids"]))
            .order_by(Request.last_action_at.desc())
            .all()
            if message["ids"]
            else []
        )
        if not rows:
            return _bub_bot(f"<p>{esc(message.get('empty', 'Nothing there.'))}</p>")
        items = []
        for request in rows[:6]:
            mine = message.get("mine", False)
            other_id = request.assignee_id if mine else request.requester_id
            other = session.get(Person, other_id) if other_id else None
            with_word = "with" if mine else "from"
            items.append(
                f"""<div class="chatrow">
                  <span class="cc-title">#{request.id} — {esc(request.title)}</span>
                  <span class="cc-meta">{status_badge(request.status)} &nbsp;
                    {with_word} {esc(other.name) if other else 'the Atlas admin'}</span>
                </div>"""
            )
        more = len(rows) - 6
        tail = f"<p class='small'>…and {more} more on the Requests page.</p>" if more > 0 else ""
        return _bub_bot("".join(items) + tail)
    if kind == "ooo":
        people = session.query(Person).filter(Person.id.in_(message["ids"])).all()
        if not people:
            return _bub_bot("<p>Nobody is marked out of office right now.</p>")
        items = "".join(
            f"""<div class="chatrow"><span class="cc-title">{esc(p.name)}</span>
                <span class="cc-meta">{esc(p.title)} · back {esc(clock.fmt(p.ooo_until))
                if p.ooo_until else 'date unknown'}</span></div>"""
            for p in people
        )
        return _bub_bot(f"<p>Away right now:</p>{items}")
    if kind == "person":
        person = session.get(Person, message["id"])
        if person is None:
            return _bub_bot("<p>I couldn't find them.</p>")
        away = is_out_of_office(person, clock.now(session))
        return _bub_bot(
            f"""<div class="chatcard">
              <div class="cc-title">{esc(person.name)}{' · away' if away else ''}</div>
              <div class="cc-meta">{esc(person.title)}
                {('· ' + esc(person.department.name)) if person.department else ''}</div>
            </div>
            <p class="small">Ask me for something and I'll route it.</p>"""
        )
    return _bub_bot("<p>…</p>")


# --- understanding & handlers ------------------------------------------------


def _handle(text: str, actor_id: int) -> None:
    with session_scope() as session:
        actor = session.get(Person, actor_id)
        reading = brain.understand(session, text, actor)

        if reading.intent == "help":
            _push("bot", "text", text=reading.reply or (
                "Tell me what you need and I'll route it. I can also show "
                "your inbox, your requests, and who is away."
            ))
            return
        if reading.intent == "inbox":
            ids = [r.id for r in session.query(Request)
                   .filter(Request.assignee_id == actor_id,
                           Request.status.in_(OPEN_STATUSES)).all()]
            _push("bot", "reqlist", ids=ids, mine=False,
                  empty="Nothing is sitting with you right now.")
            return
        if reading.intent == "my_requests":
            ids = [r.id for r in session.query(Request)
                   .filter(Request.requester_id == actor_id).all()]
            _push("bot", "reqlist", ids=ids, mine=True,
                  empty="You haven't raised anything yet. Tell me what you need "
                        "and I'll route it.")
            return
        if reading.intent == "ooo":
            at = clock.now(session)
            ids = [p.id for p in session.query(Person).all()
                   if is_out_of_office(p, at)]
            _push("bot", "ooo", ids=sorted(ids))
            return
        if reading.intent == "about_person":
            person = None
            if reading.person_name:
                person = (session.query(Person)
                          .filter(Person.name.ilike(reading.person_name)).first())
            if person is None:
                _push("bot", "text", text="I couldn't find them. Try their full "
                                          "name, or browse People.")
            else:
                _push("bot", "person", id=person.id)
            return

        # A request: explain the reading, then ask for approval on the draft.
        lines = [reading.rationale] if reading.rationale else []
        if reading.process_id is None:
            if reading.contact_line:
                lines.append(reading.contact_line)
            lines.append("Pick a type below — or send it and I'll park it "
                         "with the admin.")
        else:
            lines.append(f"{reading.confidence:.0f}% confident in this route — "
                         "approve the draft below and I'll send it.")
        st.session_state[DRAFT_KEY] = {
            "query": text,
            "process_id": reading.process_id,
            "matched_id": reading.process_id,   # the model's own pick, immutable
            "confidence": reading.confidence,
            "title": reading.title or "",
            "source": reading.source,
            "body_for": None,
        }
        for stale in ("ask_draft_title", "ask_draft_body", "ask_draft_process"):
            st.session_state.pop(stale, None)
        if lines:
            _push("bot", "text", text="\n".join(lines))


# --- the draft card ----------------------------------------------------------


def _draft_card(actor_id: int) -> None:
    draft = st.session_state.get(DRAFT_KEY)
    if not draft:
        return

    # Read everything for display in one short-lived scope; the button
    # handlers below open their own write scopes so a st.rerun() can never
    # roll a commit back.
    with session_scope() as session:
        actor = session.get(Person, actor_id)
        processes = session.query(Process).order_by(Process.name).all()
        options = [p.id for p in processes]
        names = {p.id: f"{p.name} — {p.category}" for p in processes}
        if draft["process_id"] is None:
            # Nothing matched: don't guess a route — park with the admin unless
            # the requester picks a type themselves.
            options = [None] + options
            names[None] = "No matching type — park with the Atlas admin"
        default = draft["process_id"] if draft["process_id"] in options else options[0]

        chosen = st.session_state.get("ask_draft_process", default)
        process = session.get(Process, chosen) if chosen is not None else None
        resolution = resolve(session, process)
        if chosen != draft.get("body_for"):
            draft["process_id"] = chosen
            draft["body_for"] = chosen
            # A new route re-drafts the message for the new owner; the title
            # stays — it's the requester's words.
            st.session_state["ask_draft_body"] = draft_body(
                actor, process, resolution, draft["query"]
            )
            st.session_state.setdefault("ask_draft_title", draft["title"])

        title_now = st.session_state.get("ask_draft_title", draft["title"])
        duplicates = [
            {"id": d.request.id, "title": d.request.title,
             "similarity": d.similarity}
            for d in find_similar_open_requests(
                session, process_id=chosen, requester_id=actor_id,
                title=title_now,
            )[:2]
        ]
        target = resolution.assignee_name or "the Atlas admin (no owner resolved)"
        summary = resolution.summary

    src_label = {
        "claude": "read by Claude",
        "open model": "read by an open model",
    }.get(draft["source"], "matched by keywords")
    with st.container(border=True, key="ask_draft"):
        st.markdown(
            f"<div class='draft-head'>Approve this request?"
            f"<span class='draft-src'>{src_label}</span></div>",
            unsafe_allow_html=True,
        )
        st.selectbox(
            "Route as", options=options, key="ask_draft_process",
            index=options.index(chosen), format_func=lambda i: names[i],
        )
        st.markdown(
            f"<div class='draft-route'>→ <strong>{esc(target)}</strong>"
            f" &nbsp;<span class='subtle'>{esc(summary)}</span></div>",
            unsafe_allow_html=True,
        )
        # The meter speaks for the model's own match; a manual re-route is
        # the requester's call, so it needs no score.
        conf = float(draft.get("confidence") or 0)
        if chosen is not None and chosen == draft.get("matched_id") and conf > 0:
            band = " high" if conf >= 70 else ("" if conf >= 40 else " low")
            st.markdown(
                f"<div class='confmeter{band}'>"
                f"<div class='confhead'><span>Route confidence</span>"
                f"<b>{conf:.0f}%</b></div>"
                f"<div class='track'><span class='fill' "
                f"style='width:{conf:.0f}%'></span></div></div>",
                unsafe_allow_html=True,
            )
        with st.expander("Why — the resolution trace", icon=":material/alt_route:"):
            resolution_trace(resolution)

        title = st.text_input("Title", key="ask_draft_title")
        body = st.text_area("Message", key="ask_draft_body", height=180)

        for dup in duplicates:
            col_a, col_b = st.columns([4, 1], vertical_alignment="center")
            col_a.warning(
                f"#{dup['id']} — {dup['title']} looks "
                f"{dup['similarity']:.0f}% like this. Follow it instead?"
            )
            if col_b.button("Follow", key=f"ask_follow_{dup['id']}",
                            icon=":material/notification_add:", width="stretch"):
                with write_lock, session_scope() as writer:
                    follow_existing(writer, dup["id"], actor_id)
                _push("bot", "followed", id=dup["id"], note="Done — no duplicate raised.")
                _clear_draft()
                st.rerun()

        send_col, drop_col, _ = st.columns([1.7, 1, 2.5])
        if send_col.button("Approve & send", type="primary", width="stretch",
                           icon=":material/send:", key="ask_draft_send"):
            with write_lock, session_scope() as writer:
                writer_process = (
                    writer.get(Process, chosen) if chosen is not None else None
                )
                writer_resolution = resolve(writer, writer_process)
                created = create_request(
                    writer, requester_id=actor_id, process_id=chosen,
                    assignee_id=writer_resolution.assignee_id, title=title,
                    body=body, resolution=writer_resolution,
                )
                writer.flush()
                new_id = created.id
            _push("bot", "sent", id=new_id)
            _clear_draft()
            st.rerun()
        if drop_col.button("Discard", width="stretch",
                           icon=":material/delete:", key="ask_draft_drop"):
            _clear_draft()
            _push("bot", "text", text="Dropped. What else can I sort out?")
            st.rerun()


def _clear_draft() -> None:
    st.session_state[DRAFT_KEY] = None
    for stale in ("ask_draft_title", "ask_draft_body", "ask_draft_process"):
        st.session_state.pop(stale, None)


# --- page --------------------------------------------------------------------


def render(actor_id: int) -> None:
    messages = _messages()
    pending = st.session_state.pop(PENDING_KEY, None)

    with session_scope() as session:
        log = "".join(_render_message(session, m) for m in messages)
        if pending:
            log += _bub_user(pending)
    st.markdown(f'<div class="chatlog">{log}</div>', unsafe_allow_html=True)

    if pending:
        # The reply is being worked out — show a conversation, not a spinner.
        st.markdown(
            '<div class="chatlog"><div class="msg bot"><span class="ava">A</span>'
            '<div class="bub typing"><span></span><span></span><span></span></div>'
            "</div></div>",
            unsafe_allow_html=True,
        )
        _scroll_to_end(force=True)
        _push("user", "text", text=pending)
        _handle(pending, actor_id)
        st.rerun()
        return

    _draft_card(actor_id)

    # Undo lives under the log while the last thing sent can still be recalled.
    last = messages[-1] if messages else None
    if last and last["kind"] == "sent" and not st.session_state.get(DRAFT_KEY):
        if st.button("Undo — withdraw it", icon=":material/undo:", key="ask_undo"):
            with write_lock, session_scope() as writer:
                ok = withdraw_request(writer, last["id"], actor_id)
            if ok:
                messages.pop()
                _push("bot", "text", text="Withdrawn — nothing was left in "
                                          "anyone's queue. What else?")
            else:
                _push("bot", "text", text="Too late to withdraw — it's already "
                                          "being worked on.")
            st.rerun()

    if not st.session_state.get(DRAFT_KEY):
        chips = st.columns(len(SUGGESTIONS))
        for index, (col, (label, ask, glyph)) in enumerate(zip(chips, SUGGESTIONS)):
            with col:
                with st.container(key=f"chip_{index}"):
                    st.button(
                        label, key=f"ask_chip_{index}", help=ask, icon=glyph,
                        width="stretch", on_click=_queue, args=(ask,),
                    )

    typed = st.chat_input("Tell Atlas what you need…")
    if typed:
        _queue(typed)
        st.rerun()

    _scroll_to_end()


def _scroll_to_end(force: bool = False) -> None:
    count = len(_messages())
    if force or st.session_state.get(SEEN_KEY) != count:
        st.session_state[SEEN_KEY] = count
        # Instant jump, and only when the conversation actually changed.
        components.html(
            """<script>
              const doc = window.parent.document;
              const logs = doc.querySelectorAll('.chatlog');
              const last = logs[logs.length - 1];
              if (last) last.scrollIntoView({block: 'end'});
            </script>""",
            height=0,
        )
