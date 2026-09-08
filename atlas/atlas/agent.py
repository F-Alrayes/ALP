"""The Atlas agent.

A daemon thread that wakes every couple of seconds and evaluates its rules
against *simulated* time. Because the clock is a stored offset, advancing time
by 48h in the sidebar makes the agent genuinely execute the chase it would
otherwise perform two days later.

Rules
-----
R1  On send                  a request is dispatched to its assignee and logged.
R2  Unacknowledged 48h       chase the assignee (max 2 chases, 24h apart).
R3  Two chases, no response  hand over to whoever covers the assignee; if nobody
                             covers them, escalate to their manager. The
                             requester is notified either way.
R4  Assignee goes OOO        reroute immediately to their delegate with a note.

Every autonomous action writes both an Event (Agent Log + request timeline) and
a Message (the recipient's inbox).
"""

from __future__ import annotations

import threading
import traceback

from sqlalchemy.orm import Session

from .clock import fmt, now
from .config import OPEN_STATUSES
from .db import get_setting, session_scope, write_lock
from .models import Event, Person, Request
from .routing import cover_for, is_out_of_office
from .services import log_event, send_message, touch

AGENT_ACTOR = "atlas-agent"

_thread: threading.Thread | None = None
_thread_lock = threading.Lock()
_stop_event = threading.Event()
_last_tick: dict[str, object] = {"at": None, "actions": 0, "error": None}


# --- helpers ----------------------------------------------------------------


def _int_setting(session: Session, key: str, default: int) -> int:
    try:
        return int(float(get_setting(session, key, str(default)) or default))
    except (TypeError, ValueError):
        return default


def _has_event(session: Session, request_id: int, type_: str) -> bool:
    return (
        session.query(Event)
        .filter(Event.request_id == request_id, Event.type == type_)
        .count()
        > 0
    )


def _hours_since(at, reference) -> float:
    return (at - reference).total_seconds() / 3600.0


# --- rules ------------------------------------------------------------------


def _rule_ooo_reroute(session: Session, request: Request, at) -> int:
    """R4 — the assignee is out of office, so hand the work to their cover."""
    assignee = session.get(Person, request.assignee_id) if request.assignee_id else None
    if assignee is None or not is_out_of_office(assignee, at):
        return 0
    if request.process_id is None:
        return 0

    cover = cover_for(session, request.process_id, assignee.id, at)
    if cover is None:
        # Nothing to hand over to. Say so once, then leave it to the chase rules.
        if not _has_event(session, request.id, "ooo_no_cover"):
            log_event(
                session,
                request.id,
                "ooo_no_cover",
                f"{assignee.name} is out of office until {fmt(assignee.ooo_until, with_time=False)} "
                f"and no available delegate or backup is configured for "
                f"'{request.process.name if request.process else 'this process'}'. "
                "The request stays with them and will be chased.",
                at,
                actor=AGENT_ACTOR,
            )
            return 1
        return 0

    note = (
        f"{assignee.name} was marked out of office until "
        f"{fmt(assignee.ooo_until, with_time=False)}. Rerouted to {cover.name} ({cover.title})."
    )
    request.assignee_id = cover.id
    touch(request, at)
    log_event(session, request.id, "reroute_ooo", note, at, actor=AGENT_ACTOR)
    send_message(
        session,
        request_id=request.id,
        sender_id=None,
        recipient_id=cover.id,
        type_="reroute",
        body=(
            f"You are now covering '{request.title}'.\n\n{note}\n\n"
            "Atlas rerouted this automatically because you are the configured cover."
        ),
        at=at,
    )
    send_message(
        session,
        request_id=request.id,
        sender_id=None,
        recipient_id=request.requester_id,
        type_="status_update",
        body=f"'{request.title}' was rerouted: {note}",
        at=at,
    )
    return 1


def _rule_chase(session: Session, request: Request, at, chase_after: int, interval: int, max_chases: int) -> int:
    """R2 — the request is still pending, so chase the assignee."""
    if request.status != "pending" or request.assignee_id is None:
        return 0
    if request.chase_count >= max_chases:
        return 0

    threshold = chase_after if request.chase_count == 0 else interval
    elapsed = _hours_since(at, request.last_action_at)
    if elapsed < threshold:
        return 0

    assignee = session.get(Person, request.assignee_id)
    request.chase_count += 1
    touch(request, at)
    final = request.chase_count >= max_chases
    detail = (
        f"No acknowledgement after {int(elapsed)}h — chase {request.chase_count} of {max_chases} "
        f"sent to {assignee.name}."
        + (" This is the final reminder before escalation." if final else "")
    )
    log_event(session, request.id, "chase", detail, at, actor=AGENT_ACTOR)
    send_message(
        session,
        request_id=request.id,
        sender_id=None,
        recipient_id=assignee.id,
        type_="chase",
        body=(
            f"Reminder {request.chase_count} of {max_chases}: '{request.title}' is still awaiting "
            f"your acknowledgement. It was raised "
            f"{int(_hours_since(at, request.created_at))}h ago."
            + (" If it is not picked up it will be escalated." if final else "")
        ),
        at=at,
    )
    return 1


def _rule_handover_or_escalate(session: Session, request: Request, at, interval: int, max_chases: int) -> int:
    """R3 — chases are exhausted: reroute to a cover, otherwise escalate."""
    if request.status != "pending" or request.assignee_id is None:
        return 0
    if request.chase_count < max_chases:
        return 0
    if _hours_since(at, request.last_action_at) < interval:
        return 0

    assignee = session.get(Person, request.assignee_id)
    already_rerouted = _has_event(session, request.id, "reroute_chase")
    cover = (
        cover_for(session, request.process_id, assignee.id, at)
        if (request.process_id and not already_rerouted)
        else None
    )

    if cover is not None:
        detail = (
            f"{max_chases} chases went unanswered by {assignee.name}. Handed over to "
            f"{cover.name} ({cover.title}), the configured cover for "
            f"'{request.process.name if request.process else 'this process'}'. "
            "One further chase will be sent before escalation."
        )
        request.assignee_id = cover.id
        # The cover gets a shortened cycle: one chase, then escalation.
        request.chase_count = max(0, max_chases - 1)
        touch(request, at)
        log_event(session, request.id, "reroute_chase", detail, at, actor=AGENT_ACTOR)
        send_message(
            session,
            request_id=request.id,
            sender_id=None,
            recipient_id=cover.id,
            type_="reroute",
            body=f"'{request.title}' has been handed over to you.\n\n{detail}",
            at=at,
        )
        send_message(
            session,
            request_id=request.id,
            sender_id=None,
            recipient_id=request.requester_id,
            type_="status_update",
            body=f"'{request.title}' was rerouted: {detail}",
            at=at,
        )
        return 1

    manager = session.get(Person, assignee.manager_id) if assignee.manager_id else None
    if manager is None:
        if not _has_event(session, request.id, "escalation_blocked"):
            log_event(
                session,
                request.id,
                "escalation_blocked",
                f"{assignee.name} has no manager on record and no cover is configured, so this "
                "request cannot be escalated automatically. Flagged for the Atlas admin.",
                at,
                actor=AGENT_ACTOR,
            )
            return 1
        return 0

    reason = (
        "no cover is configured" if not already_rerouted else "the cover did not respond either"
    )
    detail = (
        f"{max_chases} chases went unanswered and {reason} for "
        f"'{request.process.name if request.process else 'this process'}'. "
        f"Escalated to {manager.name} ({manager.title})."
    )
    request.status = "escalated"
    request.assignee_id = manager.id
    touch(request, at)
    log_event(session, request.id, "escalation", detail, at, actor=AGENT_ACTOR)
    send_message(
        session,
        request_id=request.id,
        sender_id=None,
        recipient_id=manager.id,
        type_="escalation",
        body=(
            f"Escalation: '{request.title}'.\n\n{detail}\n\n"
            "It is now assigned to you."
        ),
        at=at,
    )
    send_message(
        session,
        request_id=request.id,
        sender_id=None,
        recipient_id=request.requester_id,
        type_="escalation",
        body=f"Your request '{request.title}' has been escalated to {manager.name}. {detail}",
        at=at,
    )
    return 1


# --- the loop ---------------------------------------------------------------


def tick() -> int:
    """Evaluate every rule once. Returns the number of autonomous actions taken."""
    actions = 0
    with write_lock, session_scope() as session:
        at = now(session)
        chase_after = _int_setting(session, "chase_after_hours", 48)
        interval = _int_setting(session, "chase_interval_hours", 24)
        max_chases = _int_setting(session, "max_chases", 2)

        requests = (
            session.query(Request)
            .filter(Request.status.in_(OPEN_STATUSES))
            .order_by(Request.id.asc())
            .all()
        )
        for request in requests:
            if request.status == "escalated":
                continue
            actions += _rule_ooo_reroute(session, request, at)
            actions += _rule_chase(session, request, at, chase_after, interval, max_chases)
            actions += _rule_handover_or_escalate(session, request, at, interval, max_chases)

    _last_tick["at"] = at
    _last_tick["actions"] = actions
    return actions


def run_until_settled(max_passes: int = 6) -> int:
    """Run ticks until nothing more fires. Used after advancing the clock."""
    total = 0
    for _ in range(max_passes):
        fired = tick()
        total += fired
        if fired == 0:
            break
    return total


def _loop(interval_seconds: float) -> None:  # pragma: no cover - thread body
    while not _stop_event.is_set():
        try:
            tick()
            _last_tick["error"] = None
        except Exception:
            _last_tick["error"] = traceback.format_exc(limit=3)
        _stop_event.wait(interval_seconds)


def start(interval_seconds: float | None = None) -> threading.Thread:
    """Start the agent thread once per process."""
    global _thread
    with _thread_lock:
        if _thread is not None and _thread.is_alive():
            return _thread
        if interval_seconds is None:
            with session_scope() as session:
                interval_seconds = float(_int_setting(session, "agent_tick_seconds", 2))
        _stop_event.clear()
        _thread = threading.Thread(
            target=_loop, args=(interval_seconds,), name="atlas-agent", daemon=True
        )
        _thread.start()
        return _thread


def stop() -> None:  # pragma: no cover - only used in tests/teardown
    _stop_event.set()


def status() -> dict[str, object]:
    running = _thread is not None and _thread.is_alive()
    return {
        "running": running,
        "last_tick_at": _last_tick["at"],
        "last_tick_actions": _last_tick["actions"],
        "error": _last_tick["error"],
    }


def recent_actions(session: Session, limit: int = 200) -> list[Event]:
    """The Agent Log: every autonomous action, newest first."""
    return (
        session.query(Event)
        .filter(Event.actor.in_([AGENT_ACTOR, "system", "router", "demo"]))
        .order_by(Event.created_at.desc(), Event.id.desc())
        .limit(limit)
        .all()
    )
