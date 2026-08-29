"""Small presentational helpers shared by every page."""

from __future__ import annotations

import html
from datetime import datetime

import streamlit as st

from ..clock import fmt, humanize_delta
from ..models import Event, Person, Request
from ..routing import Resolution, is_out_of_office
from ..services import STATUS_LABELS

AGENT_EVENT_TYPES = {"chase", "escalation", "reroute_ooo", "reroute_chase", "ooo_no_cover", "escalation_blocked"}
ALERT_EVENT_TYPES = {"escalation", "escalation_blocked", "orphan"}

EVENT_LABELS = {
    "created": "Request raised",
    "routing": "Routing",
    "dispatch": "Dispatched",
    "chase": "Chase sent",
    "escalation": "Escalated",
    "escalation_blocked": "Escalation blocked",
    "reroute": "Reassigned",
    "reroute_ooo": "Rerouted — out of office",
    "reroute_chase": "Rerouted — no response",
    "ooo_no_cover": "No cover available",
    "acknowledged": "Acknowledged",
    "status_update": "Status update",
    "completed": "Completed",
    "note": "Note",
    "follow": "Follower joined",
    "orphan": "No owner",
    "ooo_change": "Out-of-office change",
    "seed": "Database seeded",
}


def esc(text: object) -> str:
    return html.escape(str(text if text is not None else ""))


def page_header(eyebrow: str, title: str, subtitle: str = "") -> None:
    st.markdown(
        f"""<div class="page-head">
              <div class="eyebrow">{esc(eyebrow)}</div>
              <h1>{esc(title)}</h1>
              <p class="sub">{esc(subtitle)}</p>
            </div>""",
        unsafe_allow_html=True,
    )


def stat(label: str, value: str, delta: str = "", tone: str = "") -> None:
    st.markdown(
        f"""<div class="stat {tone}">
              <div class="label">{esc(label)}</div>
              <div class="value">{esc(value)}</div>
              <div class="delta">{esc(delta)}</div>
            </div>""",
        unsafe_allow_html=True,
    )


def status_badge(status: str) -> str:
    return f'<span class="badge {esc(status)}">{esc(STATUS_LABELS.get(status, status))}</span>'


def badge(text: str, kind: str = "muted") -> str:
    return f'<span class="badge {esc(kind)}">{esc(text)}</span>'


def empty_state(headline: str, hint: str = "") -> None:
    st.markdown(
        f"""<div class="empty"><div class="big">{esc(headline)}</div><div>{esc(hint)}</div></div>""",
        unsafe_allow_html=True,
    )


def person_line(person: Person | None, at: datetime | None = None) -> str:
    if person is None:
        return '<span class="subtle">Unassigned</span>'
    out = f"<strong>{esc(person.name)}</strong> <span class='subtle'>· {esc(person.title)}</span>"
    if at is not None and is_out_of_office(person, at):
        out += " " + badge("Out of office", "ooo")
    return out


def request_card(
    request: Request,
    *,
    at: datetime,
    counterpart: Person | None,
    counterpart_label: str,
    accent: bool = False,
) -> None:
    process_name = request.process.name if request.process else "Unmatched"
    chases = (
        f" · {request.chase_count} chase{'s' if request.chase_count != 1 else ''}"
        if request.chase_count
        else ""
    )
    age = humanize_delta(at - request.created_at)
    st.markdown(
        f"""<div class="card {'accent' if accent else ''}">
              <div class="card-title">#{request.id} — {esc(request.title)}</div>
              <div class="card-meta">
                {status_badge(request.status)} &nbsp; {esc(process_name)} ·
                {esc(counterpart_label)} {esc(counterpart.name) if counterpart else "—"} ·
                raised {esc(age)} ago{esc(chases)}
              </div>
            </div>""",
        unsafe_allow_html=True,
    )


def resolution_trace(resolution: Resolution) -> None:
    steps = "".join(
        f"""<div class="step {esc(step.outcome)}">
              <div class="label">{esc(step.label)}</div>
              <div class="detail">{esc(step.detail)}</div>
            </div>"""
        for step in resolution.steps
    )
    st.markdown(f'<div class="trace">{steps}</div>', unsafe_allow_html=True)


def timeline_view(events: list[Event]) -> None:
    if not events:
        empty_state("Nothing has happened yet.", "Events appear here as the request moves.")
        return
    entries = []
    for event in events:
        css = "entry"
        if event.type in ALERT_EVENT_TYPES:
            css += " alert"
        elif event.actor == "atlas-agent" or event.type in AGENT_EVENT_TYPES:
            css += " agent"
        label = EVENT_LABELS.get(event.type, event.type.replace("_", " ").title())
        entries.append(
            f"""<div class="{css}">
                  <div class="when">{esc(fmt(event.created_at))} · <span class="who">{esc(event.actor)}</span></div>
                  <div class="what"><strong>{esc(label)}</strong> — {esc(event.detail)}</div>
                </div>"""
        )
    st.markdown(f'<div class="timeline">{"".join(entries)}</div>', unsafe_allow_html=True)


def kv(label: str, value: str) -> None:
    st.markdown(
        f'<div class="kv"><span class="k">{esc(label)}</span>{value}</div>',
        unsafe_allow_html=True,
    )
