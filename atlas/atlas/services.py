"""Request lifecycle operations.

Every state change goes through this module so that the audit trail (events),
the inboxes (messages) and the request row itself stay in lockstep. Timestamps
always come from :mod:`atlas.clock`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from rapidfuzz import fuzz
from sqlalchemy import or_
from sqlalchemy.orm import Session

from .config import OPEN_STATUSES
from .clock import now
from .db import session_scope, write_lock
from .models import Event, Message, Person, Process, Request
from .routing import Resolution

STATUS_LABELS = {
    "pending": "Pending",
    "acknowledged": "Acknowledged",
    "in_progress": "In progress",
    "completed": "Completed",
    "escalated": "Escalated",
}


# --- low level helpers ------------------------------------------------------


def log_event(
    session: Session,
    request_id: int | None,
    type_: str,
    detail: str,
    at: datetime,
    actor: str = "system",
) -> Event:
    event = Event(
        request_id=request_id, type=type_, detail=detail, actor=actor, created_at=at
    )
    session.add(event)
    return event


def send_message(
    session: Session,
    *,
    request_id: int,
    sender_id: int | None,
    recipient_id: int,
    type_: str,
    body: str,
    at: datetime,
) -> Message:
    message = Message(
        request_id=request_id,
        sender_id=sender_id,
        recipient_id=recipient_id,
        type=type_,
        body=body,
        created_at=at,
        read=False,
    )
    session.add(message)
    return message


def touch(request: Request, at: datetime) -> None:
    request.updated_at = at
    request.last_action_at = at


# --- drafting & dedup -------------------------------------------------------


def draft_body(requester: Person, process: Process | None, resolution: Resolution, query: str) -> str:
    """The editable message Atlas proposes on the intake page."""
    target = resolution.assignee_name or "the Atlas admin"
    process_name = process.name if process else "an unmatched request"
    lines = [
        f"Hi {target.split()[0] if resolution.assignee_name else 'there'},",
        "",
        f"{requester.name} ({requester.title}) has raised a request under {process_name}:",
        "",
        f"    {query.strip()}",
        "",
    ]
    if resolution.rerouted and resolution.owner_name:
        lines.append(
            f"You are receiving this because {resolution.owner_name} is out of office and you are "
            f"the configured {resolution.assignee_role} for this process."
        )
        lines.append("")
    lines.append("Atlas will chase this automatically if it is not acknowledged.")
    return "\n".join(lines)


@dataclass
class DuplicateCandidate:
    request: Request
    similarity: float
    reason: str


def find_similar_open_requests(
    session: Session,
    *,
    process_id: int | None,
    requester_id: int,
    title: str,
    threshold: float = 62.0,
) -> list[DuplicateCandidate]:
    """Open requests on the same process that look like this one."""
    if process_id is None:
        return []
    rows = (
        session.query(Request)
        .filter(Request.process_id == process_id, Request.status.in_(OPEN_STATUSES))
        .order_by(Request.created_at.desc())
        .all()
    )
    candidates: list[DuplicateCandidate] = []
    for row in rows:
        similarity = float(fuzz.token_set_ratio((title or "").lower(), (row.title or "").lower()))
        if row.requester_id == requester_id:
            reason = "You already have an open request on this process."
            similarity = max(similarity, threshold)
        elif similarity >= threshold:
            reason = "An open request with very similar wording is already in flight."
        else:
            continue
        candidates.append(DuplicateCandidate(request=row, similarity=round(similarity, 1), reason=reason))
    candidates.sort(key=lambda c: c.similarity, reverse=True)
    return candidates[:3]


# --- lifecycle --------------------------------------------------------------


def create_request(
    session: Session,
    *,
    requester_id: int,
    process_id: int | None,
    assignee_id: int | None,
    title: str,
    body: str,
    resolution: Resolution | None = None,
) -> Request:
    at = now(session)
    requester = session.get(Person, requester_id)
    request = Request(
        requester_id=requester_id,
        process_id=process_id,
        assignee_id=assignee_id,
        original_assignee_id=assignee_id,
        title=title.strip() or "New request",
        body=body,
        status="pending",
        created_at=at,
        updated_at=at,
        last_action_at=at,
        chase_count=0,
    )
    session.add(request)
    session.flush()

    process_name = resolution.process_name if resolution else "an unmatched request"
    log_event(
        session,
        request.id,
        "created",
        f"{requester.name} raised a request under '{process_name}'.",
        at,
        actor=requester.name,
    )

    if resolution is not None:
        for step in resolution.steps:
            log_event(
                session,
                request.id,
                "routing",
                f"{step.label}: {step.detail}",
                at,
                actor="router",
            )

    if assignee_id is None:
        log_event(
            session,
            request.id,
            "orphan",
            "No accountable person could be resolved. Request is parked for the Atlas admin.",
            at,
        )
    else:
        assignee = session.get(Person, assignee_id)
        log_event(
            session,
            request.id,
            "dispatch",
            f"Dispatched to {assignee.name} ({assignee.title}).",
            at,
        )
        send_message(
            session,
            request_id=request.id,
            sender_id=requester_id,
            recipient_id=assignee_id,
            type_="dispatch",
            body=body,
            at=at,
        )
    return request


def follow_existing(session: Session, request_id: int, follower_id: int) -> Request:
    at = now(session)
    request = session.get(Request, request_id)
    follower = session.get(Person, follower_id)
    log_event(
        session,
        request.id,
        "follow",
        f"{follower.name} joined this request instead of raising a duplicate.",
        at,
        actor=follower.name,
    )
    if request.assignee_id:
        send_message(
            session,
            request_id=request.id,
            sender_id=follower_id,
            recipient_id=request.assignee_id,
            type_="status_update",
            body=f"{follower.name} is also waiting on this request.",
            at=at,
        )
    touch(request, at)
    return request


def can_withdraw(session: Session, request_id: int, actor_id: int) -> bool:
    """Can the requester still take this back?

    Only while nobody has touched it. Once the assignee acknowledges it, or the
    agent chases or reroutes it, the request is real: it has to be resolved in
    the open rather than quietly deleted.
    """
    request = session.get(Request, request_id)
    if request is None:
        return False
    return (
        request.requester_id == actor_id
        and request.status == "pending"
        and request.acknowledged_at is None
        and request.chase_count == 0
        and request.assignee_id == request.original_assignee_id
    )


def withdraw_request(session: Session, request_id: int, actor_id: int) -> bool:
    """Undo a request, taking its trail with it. Returns False if it is too late."""
    if not can_withdraw(session, request_id, actor_id):
        return False
    session.query(Event).filter(Event.request_id == request_id).delete()
    session.query(Message).filter(Message.request_id == request_id).delete()
    session.query(Request).filter(Request.id == request_id).delete()
    session.flush()
    return True


def _notify_requester(session: Session, request: Request, body: str, at: datetime) -> None:
    send_message(
        session,
        request_id=request.id,
        sender_id=request.assignee_id,
        recipient_id=request.requester_id,
        type_="status_update",
        body=body,
        at=at,
    )


def acknowledge(session: Session, request_id: int, actor_id: int) -> Request:
    at = now(session)
    request = session.get(Request, request_id)
    actor = session.get(Person, actor_id)
    if request.status in ("completed",):
        return request
    if request.acknowledged_at is None:
        request.acknowledged_at = at
    request.status = "acknowledged"
    touch(request, at)
    log_event(session, request.id, "acknowledged", f"{actor.name} acknowledged the request.", at, actor=actor.name)
    _notify_requester(session, request, f"{actor.name} has acknowledged '{request.title}'.", at)
    return request


def start_progress(session: Session, request_id: int, actor_id: int) -> Request:
    at = now(session)
    request = session.get(Request, request_id)
    actor = session.get(Person, actor_id)
    if request.status == "completed":
        return request
    if request.acknowledged_at is None:
        request.acknowledged_at = at
    request.status = "in_progress"
    touch(request, at)
    log_event(session, request.id, "status_update", f"{actor.name} moved the request to In progress.", at, actor=actor.name)
    _notify_requester(session, request, f"{actor.name} is working on '{request.title}'.", at)
    return request


def complete(session: Session, request_id: int, actor_id: int, note: str = "") -> Request:
    at = now(session)
    request = session.get(Request, request_id)
    actor = session.get(Person, actor_id)
    if request.status == "completed":
        return request
    if request.acknowledged_at is None:
        request.acknowledged_at = at
    request.status = "completed"
    request.completed_at = at
    touch(request, at)
    detail = f"{actor.name} completed the request."
    if note.strip():
        detail += f" Note: {note.strip()}"
    log_event(session, request.id, "completed", detail, at, actor=actor.name)
    body = f"'{request.title}' has been completed by {actor.name}."
    if note.strip():
        body += f"\n\n{note.strip()}"
    _notify_requester(session, request, body, at)
    return request


def reassign(session: Session, request_id: int, actor_id: int, new_assignee_id: int, reason: str) -> Request:
    at = now(session)
    request = session.get(Request, request_id)
    actor = session.get(Person, actor_id)
    new_assignee = session.get(Person, new_assignee_id)
    previous = session.get(Person, request.assignee_id) if request.assignee_id else None
    request.assignee_id = new_assignee_id
    if request.status == "escalated":
        request.status = "pending"
    touch(request, at)
    detail = (
        f"{actor.name} reassigned the request "
        f"{'from ' + previous.name + ' ' if previous else ''}to {new_assignee.name}."
    )
    if reason.strip():
        detail += f" Reason: {reason.strip()}"
    log_event(session, request.id, "reroute", detail, at, actor=actor.name)
    send_message(
        session,
        request_id=request.id,
        sender_id=actor_id,
        recipient_id=new_assignee_id,
        type_="reroute",
        body=f"'{request.title}' has been reassigned to you by {actor.name}. {reason.strip()}".strip(),
        at=at,
    )
    return request


def add_note(session: Session, request_id: int, actor_id: int, note: str) -> Request:
    at = now(session)
    request = session.get(Request, request_id)
    actor = session.get(Person, actor_id)
    log_event(session, request.id, "note", f"{actor.name}: {note.strip()}", at, actor=actor.name)
    recipient_id = (
        request.requester_id if actor_id == request.assignee_id else request.assignee_id
    )
    if recipient_id:
        send_message(
            session,
            request_id=request.id,
            sender_id=actor_id,
            recipient_id=recipient_id,
            type_="status_update",
            body=note.strip(),
            at=at,
        )
    touch(request, at)
    return request


def mark_read(session: Session, person_id: int, request_id: int | None = None) -> int:
    query = session.query(Message).filter(
        Message.recipient_id == person_id, Message.read.is_(False)
    )
    if request_id is not None:
        query = query.filter(Message.request_id == request_id)
    rows = query.all()
    for row in rows:
        row.read = True
    return len(rows)


# --- queries used across the UI --------------------------------------------


def inbox_for(session: Session, person_id: int, include_closed: bool = False) -> list[Request]:
    query = session.query(Request).filter(Request.assignee_id == person_id)
    if not include_closed:
        query = query.filter(Request.status.in_(OPEN_STATUSES))
    return query.order_by(Request.last_action_at.desc()).all()


def requests_by(session: Session, person_id: int, include_closed: bool = True) -> list[Request]:
    query = session.query(Request).filter(Request.requester_id == person_id)
    if not include_closed:
        query = query.filter(Request.status.in_(OPEN_STATUSES))
    return query.order_by(Request.created_at.desc()).all()


def unread_count(session: Session, person_id: int) -> int:
    return (
        session.query(Message)
        .filter(Message.recipient_id == person_id, Message.read.is_(False))
        .count()
    )


def timeline(session: Session, request_id: int) -> list[Event]:
    return (
        session.query(Event)
        .filter(Event.request_id == request_id)
        .order_by(Event.created_at.asc(), Event.id.asc())
        .all()
    )


def messages_for_request(session: Session, request_id: int) -> list[Message]:
    return (
        session.query(Message)
        .filter(Message.request_id == request_id)
        .order_by(Message.created_at.asc(), Message.id.asc())
        .all()
    )


def open_load(session: Session, person_id: int) -> int:
    return (
        session.query(Request)
        .filter(Request.assignee_id == person_id, Request.status.in_(OPEN_STATUSES))
        .count()
    )


def set_ooo(person_id: int, is_ooo: bool, until: datetime | None = None) -> None:
    """Toggle a person's out-of-office flag. The agent reacts on its next tick."""
    with write_lock, session_scope() as session:
        person = session.get(Person, person_id)
        if person is None:
            return
        at = now(session)
        person.is_ooo = is_ooo
        person.ooo_until = until if is_ooo else None
        log_event(
            session,
            None,
            "ooo_change",
            f"{person.name} marked {'out of office' if is_ooo else 'back in the office'}"
            + (f" until {until:%d %b %Y}." if is_ooo and until else "."),
            at,
            actor="demo",
        )


def people_search(session: Session, term: str) -> list[Person]:
    term = (term or "").strip()
    query = session.query(Person)
    if term:
        like = f"%{term}%"
        query = query.filter(or_(Person.name.ilike(like), Person.title.ilike(like)))
    return query.order_by(Person.name).all()
