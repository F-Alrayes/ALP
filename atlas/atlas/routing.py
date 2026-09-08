"""Responsibility resolution.

Given a process, work out who is actually accountable *right now* and record the
reasoning as a trace the UI can show step by step:

    owner -> out of office? -> delegate -> backup -> manager -> flag for admin

Nothing dead-ends: if every hop fails the resolution is marked ``needs_admin``
rather than silently dropping the request.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from sqlalchemy.orm import Session

from .clock import fmt, now
from .models import Person, Process, Responsibility

ROLE_ORDER = ["owner", "approver", "delegate", "backup"]


@dataclass
class TraceStep:
    label: str
    outcome: str            # "ok" | "warn" | "fail"
    detail: str
    person_id: int | None = None
    person_name: str | None = None


@dataclass
class Resolution:
    process_id: int | None
    process_name: str
    assignee_id: int | None = None
    assignee_name: str | None = None
    assignee_role: str | None = None      # which edge finally carried the work
    owner_id: int | None = None
    owner_name: str | None = None
    rerouted: bool = False
    needs_admin: bool = False
    steps: list[TraceStep] = field(default_factory=list)

    @property
    def summary(self) -> str:
        if self.needs_admin:
            return f"No owner configured for '{self.process_name}' — flagged for the Atlas admin."
        if self.rerouted:
            return (
                f"{self.owner_name} is out of office; routed to {self.assignee_name} "
                f"as {self.assignee_role}."
            )
        return f"Routed to {self.assignee_name}, the accountable owner of '{self.process_name}'."


def is_out_of_office(person: Person | None, at: datetime) -> bool:
    if person is None or not person.is_ooo:
        return False
    if person.ooo_until is None:
        return True
    return person.ooo_until >= at


def holders(session: Session, process_id: int, role: str) -> list[Person]:
    rows = (
        session.query(Responsibility)
        .filter(Responsibility.process_id == process_id, Responsibility.role == role)
        .all()
    )
    people = []
    for row in rows:
        person = session.get(Person, row.person_id)
        if person is not None:
            people.append(person)
    return people


def first_holder(session: Session, process_id: int, role: str) -> Person | None:
    people = holders(session, process_id, role)
    return people[0] if people else None


def resolve(session: Session, process: Process | None, at: datetime | None = None) -> Resolution:
    """Walk the responsibility graph and return who should receive the work."""
    at = at or now(session)

    if process is None:
        return Resolution(
            process_id=None,
            process_name="Unmatched request",
            needs_admin=True,
            steps=[
                TraceStep(
                    "Process match",
                    "fail",
                    "The request text did not match a known process, so no owner could be looked up.",
                )
            ],
        )

    res = Resolution(process_id=process.id, process_name=process.name)
    res.steps.append(
        TraceStep(
            "Process match",
            "ok",
            f"Resolved to '{process.name}' ({process.category}).",
        )
    )

    owner = first_holder(session, process.id, "owner")
    if owner is None:
        res.needs_admin = True
        res.steps.append(
            TraceStep(
                "Owner lookup",
                "fail",
                f"'{process.name}' is an orphan process — no owner edge exists in the "
                "responsibility graph. Flagged for the Atlas admin to assign an owner.",
            )
        )
        return res

    res.owner_id = owner.id
    res.owner_name = owner.name
    res.steps.append(
        TraceStep(
            "Owner lookup",
            "ok",
            f"{owner.name} ({owner.title}) owns this process.",
            owner.id,
            owner.name,
        )
    )

    if not is_out_of_office(owner, at):
        res.steps.append(
            TraceStep(
                "Availability check",
                "ok",
                f"{owner.name} is available.",
                owner.id,
                owner.name,
            )
        )
        res.assignee_id = owner.id
        res.assignee_name = owner.name
        res.assignee_role = "owner"
        return res

    res.rerouted = True
    res.steps.append(
        TraceStep(
            "Availability check",
            "warn",
            f"{owner.name} is out of office until {fmt(owner.ooo_until, with_time=False)}. "
            "Applying out-of-office failover.",
            owner.id,
            owner.name,
        )
    )

    for role in ("delegate", "backup"):
        candidate = first_holder(session, process.id, role)
        if candidate is None:
            res.steps.append(
                TraceStep(
                    f"{role.capitalize()} lookup",
                    "warn",
                    f"No {role} is configured for '{process.name}'.",
                )
            )
            continue
        if is_out_of_office(candidate, at):
            res.steps.append(
                TraceStep(
                    f"{role.capitalize()} lookup",
                    "warn",
                    f"{candidate.name} is the configured {role} but is also out of office "
                    f"until {fmt(candidate.ooo_until, with_time=False)}.",
                    candidate.id,
                    candidate.name,
                )
            )
            continue
        res.steps.append(
            TraceStep(
                f"{role.capitalize()} lookup",
                "ok",
                f"{candidate.name} ({candidate.title}) is the configured {role} and is available.",
                candidate.id,
                candidate.name,
            )
        )
        res.assignee_id = candidate.id
        res.assignee_name = candidate.name
        res.assignee_role = role
        return res

    manager = session.get(Person, owner.manager_id) if owner.manager_id else None
    if manager is not None and not is_out_of_office(manager, at):
        res.steps.append(
            TraceStep(
                "Manager fallback",
                "warn",
                f"No available delegate or backup. Routing to {owner.name}'s manager, "
                f"{manager.name} ({manager.title}). This process is a single point of failure.",
                manager.id,
                manager.name,
            )
        )
        res.assignee_id = manager.id
        res.assignee_name = manager.name
        res.assignee_role = "manager"
        return res

    res.needs_admin = True
    res.steps.append(
        TraceStep(
            "Escalation",
            "fail",
            f"Owner, delegate, backup and manager are all unavailable for '{process.name}'. "
            "Flagged for the Atlas admin.",
        )
    )
    return res


def cover_for(session: Session, process_id: int, person_id: int, at: datetime) -> Person | None:
    """Who covers ``person_id`` on this process — used when someone goes OOO."""
    for role in ("delegate", "backup"):
        for candidate in holders(session, process_id, role):
            if candidate.id == person_id:
                continue
            if not is_out_of_office(candidate, at):
                return candidate
    return None


def responsibilities_of(session: Session, person_id: int) -> dict[str, list[Process]]:
    """Everything a person owns / approves / covers, grouped by role."""
    rows = (
        session.query(Responsibility)
        .filter(Responsibility.person_id == person_id)
        .all()
    )
    grouped: dict[str, list[Process]] = {role: [] for role in ROLE_ORDER}
    for row in rows:
        process = session.get(Process, row.process_id)
        if process is not None:
            grouped.setdefault(row.role, []).append(process)
    for role in grouped:
        grouped[role].sort(key=lambda p: p.name)
    return grouped
