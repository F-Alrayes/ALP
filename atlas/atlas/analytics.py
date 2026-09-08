"""Analytics over the responsibility graph and the request queue.

Returns plain dicts and lists; the dashboard view turns them into Plotly charts
and tables. Everything is computed against simulated time.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from sqlalchemy.orm import Session

from .clock import now
from .config import OPEN_STATUSES
from .models import Department, Event, Person, Process, Request, Responsibility
from .routing import is_out_of_office
from .services import STATUS_LABELS


def _department_name(session: Session, person: Person | None) -> str:
    if person is None:
        return "Unassigned"
    if person.department_id is None:
        return "Executive"
    dept = session.get(Department, person.department_id)
    return dept.name if dept else "Unassigned"


def headline(session: Session) -> dict[str, float | int]:
    at = now(session)
    requests = session.query(Request).all()
    open_requests = [r for r in requests if r.status in OPEN_STATUSES]
    escalated_ids = {
        e.request_id
        for e in session.query(Event).filter(Event.type == "escalation").all()
        if e.request_id
    }
    ack_hours = [
        (r.acknowledged_at - r.created_at).total_seconds() / 3600.0
        for r in requests
        if r.acknowledged_at
    ]
    cycle_hours = [
        (r.completed_at - r.created_at).total_seconds() / 3600.0
        for r in requests
        if r.completed_at
    ]
    waiting = [
        (at - r.created_at).total_seconds() / 3600.0 for r in open_requests
    ]
    return {
        "total_requests": len(requests),
        "open_requests": len(open_requests),
        "completed_requests": sum(1 for r in requests if r.status == "completed"),
        "escalated_requests": len(escalated_ids),
        "escalation_rate": (len(escalated_ids) / len(requests) * 100.0) if requests else 0.0,
        "avg_ack_hours": (sum(ack_hours) / len(ack_hours)) if ack_hours else 0.0,
        "avg_cycle_hours": (sum(cycle_hours) / len(cycle_hours)) if cycle_hours else 0.0,
        "avg_queue_hours": (sum(waiting) / len(waiting)) if waiting else 0.0,
        "oldest_open_hours": max(waiting) if waiting else 0.0,
    }


def by_status(session: Session) -> list[dict]:
    counts: dict[str, int] = defaultdict(int)
    for request in session.query(Request).all():
        counts[request.status] += 1
    order = ["pending", "acknowledged", "in_progress", "escalated", "completed"]
    return [
        {"status": STATUS_LABELS.get(s, s), "key": s, "count": counts.get(s, 0)}
        for s in order
    ]


def open_by_department(session: Session) -> list[dict]:
    counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for request in session.query(Request).filter(Request.status.in_(OPEN_STATUSES)).all():
        assignee = session.get(Person, request.assignee_id) if request.assignee_id else None
        dept = _department_name(session, assignee)
        counts[dept][request.status] += 1
    rows: list[dict] = []
    for dept, statuses in counts.items():
        for status, count in statuses.items():
            rows.append(
                {"department": dept, "status": STATUS_LABELS.get(status, status), "count": count}
            )
    rows.sort(key=lambda r: (r["department"], r["status"]))
    return rows


def turnaround_by_department(session: Session) -> list[dict]:
    ack: dict[str, list[float]] = defaultdict(list)
    cycle: dict[str, list[float]] = defaultdict(list)
    for request in session.query(Request).all():
        assignee = session.get(Person, request.assignee_id) if request.assignee_id else None
        dept = _department_name(session, assignee)
        if request.acknowledged_at:
            ack[dept].append((request.acknowledged_at - request.created_at).total_seconds() / 3600.0)
        if request.completed_at:
            cycle[dept].append((request.completed_at - request.created_at).total_seconds() / 3600.0)
    departments = sorted(set(ack) | set(cycle))
    rows = []
    for dept in departments:
        rows.append(
            {
                "department": dept,
                "avg_ack_hours": round(sum(ack[dept]) / len(ack[dept]), 1) if ack[dept] else 0.0,
                "avg_complete_hours": round(sum(cycle[dept]) / len(cycle[dept]), 1)
                if cycle[dept]
                else 0.0,
                "sample": max(len(ack[dept]), len(cycle[dept])),
            }
        )
    return rows


def orphan_processes(session: Session) -> list[dict]:
    """Processes with no owner edge — work that has nowhere to go."""
    owned = {
        row.process_id
        for row in session.query(Responsibility).filter(Responsibility.role == "owner").all()
    }
    rows = []
    for process in session.query(Process).order_by(Process.name).all():
        if process.id in owned:
            continue
        open_count = (
            session.query(Request)
            .filter(Request.process_id == process.id, Request.status.in_(OPEN_STATUSES))
            .count()
        )
        other_roles = sorted(
            {
                r.role
                for r in session.query(Responsibility)
                .filter(Responsibility.process_id == process.id)
                .all()
            }
        )
        rows.append(
            {
                "process": process.name,
                "category": process.category,
                "open_requests": open_count,
                "other_roles": ", ".join(other_roles) if other_roles else "none",
            }
        )
    return rows


@dataclass
class SpofRow:
    person: str
    title: str
    department: str
    owns: int
    approves: int
    uncovered: list[str]
    open_load: int
    is_ooo: bool

    @property
    def total(self) -> int:
        return self.owns + self.approves


def single_points_of_failure(session: Session, threshold: int = 3) -> list[SpofRow]:
    """People carrying several processes, flagged by how many lack a live backstop."""
    at = now(session)
    by_person: dict[int, dict[str, list[Process]]] = defaultdict(lambda: defaultdict(list))
    for row in session.query(Responsibility).all():
        process = session.get(Process, row.process_id)
        if process is not None:
            by_person[row.person_id][row.role].append(process)

    rows: list[SpofRow] = []
    for person_id, roles in by_person.items():
        person = session.get(Person, person_id)
        if person is None:
            continue
        owns = roles.get("owner", [])
        approves = roles.get("approver", [])
        if len(owns) + len(approves) < threshold:
            continue

        uncovered = []
        for process in owns:
            covers = [
                r
                for r in session.query(Responsibility)
                .filter(
                    Responsibility.process_id == process.id,
                    Responsibility.role.in_(("delegate", "backup")),
                )
                .all()
            ]
            available = [
                session.get(Person, r.person_id)
                for r in covers
                if r.person_id != person_id
            ]
            if not any(p is not None and not is_out_of_office(p, at) for p in available):
                uncovered.append(process.name)

        rows.append(
            SpofRow(
                person=person.name,
                title=person.title,
                department=_department_name(session, person),
                owns=len(owns),
                approves=len(approves),
                uncovered=sorted(uncovered),
                open_load=session.query(Request)
                .filter(Request.assignee_id == person_id, Request.status.in_(OPEN_STATUSES))
                .count(),
                is_ooo=is_out_of_office(person, at),
            )
        )
    rows.sort(key=lambda r: (len(r.uncovered), r.total, r.open_load), reverse=True)
    return rows


def bottlenecks(session: Session, limit: int = 8) -> list[dict]:
    """The people the queue is actually piling up behind."""
    at = now(session)
    rows: dict[int, dict] = {}
    for request in session.query(Request).filter(Request.status.in_(OPEN_STATUSES)).all():
        if request.assignee_id is None:
            continue
        entry = rows.setdefault(
            request.assignee_id,
            {"person_id": request.assignee_id, "open": 0, "waiting_hours": []},
        )
        entry["open"] += 1
        entry["waiting_hours"].append((at - request.created_at).total_seconds() / 3600.0)

    out = []
    for entry in rows.values():
        person = session.get(Person, entry["person_id"])
        if person is None:
            continue
        waits = entry["waiting_hours"]
        out.append(
            {
                "person": person.name,
                "title": person.title,
                "department": _department_name(session, person),
                "open": entry["open"],
                "avg_wait_hours": round(sum(waits) / len(waits), 1),
                "oldest_wait_hours": round(max(waits), 1),
                "is_ooo": is_out_of_office(person, at),
            }
        )
    out.sort(key=lambda r: (r["open"], r["oldest_wait_hours"]), reverse=True)
    return out[:limit]


def queue_ages(session: Session) -> list[dict]:
    """Age of every open request, for the queue-time distribution chart."""
    at = now(session)
    rows = []
    for request in session.query(Request).filter(Request.status.in_(OPEN_STATUSES)).all():
        assignee = session.get(Person, request.assignee_id) if request.assignee_id else None
        rows.append(
            {
                "id": request.id,
                "title": request.title,
                "status": STATUS_LABELS.get(request.status, request.status),
                "department": _department_name(session, assignee),
                "assignee": assignee.name if assignee else "Unassigned",
                "age_hours": round((at - request.created_at).total_seconds() / 3600.0, 1),
                "chases": request.chase_count,
            }
        )
    rows.sort(key=lambda r: r["age_hours"], reverse=True)
    return rows


def process_stats(session: Session, process_id: int) -> dict:
    requests = session.query(Request).filter(Request.process_id == process_id).all()
    done = [r for r in requests if r.completed_at]
    turnaround = [
        (r.completed_at - r.created_at).total_seconds() / 3600.0 for r in done
    ]
    return {
        "total": len(requests),
        "open": sum(1 for r in requests if r.status in OPEN_STATUSES),
        "completed": len(done),
        "avg_turnaround_hours": round(sum(turnaround) / len(turnaround), 1) if turnaround else None,
    }


def person_stats(session: Session, person_id: int) -> dict:
    handled = session.query(Request).filter(Request.assignee_id == person_id).all()
    done = [r for r in handled if r.completed_at]
    turnaround = [(r.completed_at - r.created_at).total_seconds() / 3600.0 for r in done]
    acked = [
        (r.acknowledged_at - r.created_at).total_seconds() / 3600.0
        for r in handled
        if r.acknowledged_at
    ]
    return {
        "open_load": sum(1 for r in handled if r.status in OPEN_STATUSES),
        "completed": len(done),
        "avg_turnaround_hours": round(sum(turnaround) / len(turnaround), 1) if turnaround else None,
        "avg_ack_hours": round(sum(acked) / len(acked), 1) if acked else None,
    }


def responsibility_graph(session: Session, department: str | None = None) -> dict:
    """Nodes and edges for the responsibility network visualisation."""
    processes = session.query(Process).order_by(Process.name).all()
    rows = session.query(Responsibility).all()

    people_ids = {r.person_id for r in rows}
    nodes = []
    for process in processes:
        nodes.append(
            {"id": f"p{process.id}", "label": process.name, "kind": "process", "group": process.category}
        )
    for person_id in sorted(people_ids):
        person = session.get(Person, person_id)
        if person is None:
            continue
        dept = _department_name(session, person)
        if department and dept != department:
            continue
        nodes.append(
            {"id": f"h{person.id}", "label": person.name, "kind": "person", "group": dept}
        )

    node_ids = {n["id"] for n in nodes}
    edges = []
    for row in rows:
        source = f"h{row.person_id}"
        target = f"p{row.process_id}"
        if source in node_ids and target in node_ids:
            edges.append({"source": source, "target": target, "role": row.role})
    return {"nodes": nodes, "edges": edges}
