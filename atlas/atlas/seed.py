"""Seed script — the only fake part of Atlas.

Builds a coherent 40-person investment firm, a 14-process responsibility graph,
and a back catalogue of requests so that every dashboard, inbox and report is
alive on first launch. The demo conditions at the bottom of this file (who is
out of office, which processes are orphaned, who is a single point of failure)
are deliberate: they are what the pitch walks through.
"""

from __future__ import annotations

import random
from datetime import timedelta

from sqlalchemy.orm import Session

from . import config
from .clock import now
from .db import create_all, drop_all, session_scope, set_setting
from .models import (
    Department,
    Event,
    Message,
    Person,
    Process,
    Request,
    Responsibility,
)

DEPARTMENTS = [
    "Investments / Deal Team",
    "Finance",
    "Legal & Compliance",
    "IT",
    "Operations / HR",
]

# (name, title, department, manager name or None)
PEOPLE: list[tuple[str, str, str | None, str | None]] = [
    ("Khalid Al-Rayes", "Chief Executive Officer", None, None),
    # --- Investments / Deal Team ---
    ("Faisal Al-Otaibi", "Managing Director, Investments", "Investments / Deal Team", "Khalid Al-Rayes"),
    ("Sarah Whitfield", "Investment Director", "Investments / Deal Team", "Faisal Al-Otaibi"),
    ("Omar Haddad", "Principal", "Investments / Deal Team", "Faisal Al-Otaibi"),
    ("Layla Mansour", "Senior Associate", "Investments / Deal Team", "Sarah Whitfield"),
    ("James Okonkwo", "Associate", "Investments / Deal Team", "Sarah Whitfield"),
    ("Noura Al-Sabah", "Associate", "Investments / Deal Team", "Omar Haddad"),
    ("Marco Bianchi", "Investment Analyst", "Investments / Deal Team", "Omar Haddad"),
    ("Yousef Darwish", "Investment Analyst", "Investments / Deal Team", "Layla Mansour"),
    ("Sofia Marchetti", "Investment Analyst", "Investments / Deal Team", "Layla Mansour"),
    # --- Finance ---
    ("Amira Haddadin", "Chief Financial Officer", "Finance", "Khalid Al-Rayes"),
    ("Daniel Reyes", "Finance Director", "Finance", "Amira Haddadin"),
    ("Huda Al-Najjar", "Financial Controller", "Finance", "Amira Haddadin"),
    ("Peter Lindqvist", "Senior Accountant", "Finance", "Huda Al-Najjar"),
    ("Rania Khoury", "Accounts Payable Lead", "Finance", "Daniel Reyes"),
    ("Tomas Ferreira", "Treasury Analyst", "Finance", "Daniel Reyes"),
    ("Mariam Al-Balushi", "Fund Accountant", "Finance", "Huda Al-Najjar"),
    ("Karim El-Masri", "Payroll Specialist", "Finance", "Daniel Reyes"),
    # --- Legal & Compliance ---
    ("Nadia Suleiman", "General Counsel", "Legal & Compliance", "Khalid Al-Rayes"),
    ("Robert Ashby", "Deputy General Counsel", "Legal & Compliance", "Nadia Suleiman"),
    ("Zainab Al-Hashimi", "Head of Compliance", "Legal & Compliance", "Nadia Suleiman"),
    ("Eleanor Voss", "Senior Legal Counsel", "Legal & Compliance", "Robert Ashby"),
    ("Tariq Benali", "Compliance Officer, KYC", "Legal & Compliance", "Zainab Al-Hashimi"),
    ("Grace Mwangi", "Legal Counsel", "Legal & Compliance", "Robert Ashby"),
    ("Hassan Al-Farsi", "Paralegal", "Legal & Compliance", "Eleanor Voss"),
    # --- IT ---
    ("Vikram Chandra", "Head of Technology", "IT", "Khalid Al-Rayes"),
    ("Elena Petrova", "Infrastructure Lead", "IT", "Vikram Chandra"),
    ("Ahmed Zaki", "Systems Administrator", "IT", "Elena Petrova"),
    ("Chloe Dubois", "Security Engineer", "IT", "Vikram Chandra"),
    ("Bilal Rahman", "IT Support Lead", "IT", "Vikram Chandra"),
    ("Ivan Kovacs", "Application Support Analyst", "IT", "Bilal Rahman"),
    ("Fatima Al-Zahrani", "Data Engineer", "IT", "Elena Petrova"),
    # --- Operations / HR ---
    ("Claire Donovan", "Chief Operating Officer", "Operations / HR", "Khalid Al-Rayes"),
    ("Salma Bouzid", "Head of Human Resources", "Operations / HR", "Claire Donovan"),
    ("Michael Trent", "Operations Manager", "Operations / HR", "Claire Donovan"),
    ("Dina Al-Kaabi", "HR Business Partner", "Operations / HR", "Salma Bouzid"),
    ("Anna Sorenson", "Office Manager", "Operations / HR", "Michael Trent"),
    ("Youssef Karim", "Procurement Lead", "Operations / HR", "Michael Trent"),
    ("Priya Nair", "Executive Assistant to the CEO", "Operations / HR", "Claire Donovan"),
    ("Hamza Al-Dosari", "Travel & Facilities Coordinator", "Operations / HR", "Anna Sorenson"),
]

# (name, category, description, keywords)
PROCESSES: list[tuple[str, str, str, str]] = [
    (
        "Data Room Access",
        "Deal Support",
        "Grant a colleague or counterparty access to a project virtual data room, "
        "including folder-level permissions and NDA verification.",
        "data room, dataroom, virtual data room, vdr, deal documents, project access, "
        "folder access, diligence documents, deal folder, project falcon",
    ),
    (
        "Invoice Approval",
        "Finance",
        "Approve a supplier invoice for payment once goods or services are confirmed received.",
        "invoice, approve invoice, supplier payment, pay invoice, billing, accounts payable, "
        "ap, invoice sign off, payment run",
    ),
    (
        "IT Access Provisioning",
        "IT",
        "Provision system access, licences or shared drive permissions for a colleague, "
        "including password resets and locked accounts.",
        "access, permissions, system access, provisioning, licence, license, vpn access, "
        "shared drive, new account, joiner setup, password, reset password, locked out, "
        "mfa, login issue, cannot log in, account locked",
    ),
    (
        "Travel Approval",
        "Operations",
        "Approve business travel and book flights, hotels and ground transport.",
        "travel, flight, flights, trip, hotel, business travel, travel request, itinerary, "
        "travel booking, visa",
    ),
    (
        "Expense Reimbursement",
        "Finance",
        "Reimburse out-of-pocket business expenses against submitted receipts.",
        "expense, expenses, reimbursement, reimburse, claim, receipts, out of pocket, "
        "expense report, mileage",
    ),
    (
        "Valuation Sign-off",
        "Finance",
        "Quarterly fair-value sign-off for portfolio holdings feeding the NAV.",
        "valuation, nav, fair value, portfolio valuation, sign off, mark, quarterly valuation, "
        "pricing, net asset value",
    ),
    (
        "Purchase Order Approval",
        "Procurement",
        "Raise and approve a purchase order before committing firm spend.",
        "purchase order, po, raise po, procurement request, spend approval, commit spend, "
        "buy, order form",
    ),
    (
        "Policy Exception Approval",
        "Compliance",
        "Approve a documented deviation from an internal policy, with rationale and expiry.",
        "policy exception, waiver, exemption, deviation, override, policy breach, "
        "one off approval, dispensation",
    ),
]

# process name -> {role: [person names]}
RESPONSIBILITIES: dict[str, dict[str, list[str]]] = {
    "Data Room Access": {
        "owner": ["Layla Mansour"],
        "approver": ["Faisal Al-Otaibi"],
        "delegate": ["James Okonkwo"],
        "backup": ["Omar Haddad"],
    },
    "Invoice Approval": {
        "owner": ["Rania Khoury"],
        "approver": ["Huda Al-Najjar"],
        "delegate": ["Karim El-Masri"],
        "backup": ["Tomas Ferreira"],
    },
    "IT Access Provisioning": {
        "owner": ["Bilal Rahman"],
        "approver": ["Vikram Chandra"],
        "delegate": ["Ivan Kovacs"],
        "backup": ["Ahmed Zaki"],
    },
    "Travel Approval": {
        "owner": ["Hamza Al-Dosari"],
        "approver": ["Michael Trent", "Huda Al-Najjar"],
        "delegate": ["Anna Sorenson"],
    },
    "Expense Reimbursement": {
        "owner": ["Peter Lindqvist"],
        "approver": ["Huda Al-Najjar"],
        "delegate": ["Mariam Al-Balushi"],
    },
    # Deliberate single point of failure: owner is Huda, no delegate, no backup.
    "Valuation Sign-off": {
        "owner": ["Huda Al-Najjar"],
        "approver": ["Amira Haddadin"],
    },
    # Orphans — deliberately nobody owns these.
    "Purchase Order Approval": {},
    "Policy Exception Approval": {},
}

# name -> days out of office from the simulated "now"
OOO_PEOPLE = {
    "Layla Mansour": 6,   # owner of Data Room Access — the headline demo
    "Eleanor Voss": 3,
    "Ahmed Zaki": 2,
    "Huda Al-Najjar": 4,  # single point of failure, no delegate configured
}


def _email(name: str) -> str:
    parts = [p for p in name.replace("-", " ").split() if p]
    first = parts[0].lower()
    last = parts[-1].lower()
    return f"{first}.{last}@atlas-capital.example"


def _add_event(
    session: Session,
    request: Request,
    type_: str,
    detail: str,
    created_at,
    actor: str = "system",
) -> None:
    session.add(
        Event(
            request_id=request.id,
            type=type_,
            detail=detail,
            actor=actor,
            created_at=created_at,
        )
    )


def _seed_request(
    session: Session,
    *,
    requester: Person,
    process: Process,
    assignee: Person,
    title: str,
    body: str,
    status: str,
    created_at,
    ack_after_hours: float | None = None,
    complete_after_hours: float | None = None,
    chase_count: int = 0,
    last_action_offset_hours: float | None = None,
) -> Request:
    request = Request(
        requester_id=requester.id,
        process_id=process.id,
        assignee_id=assignee.id,
        original_assignee_id=assignee.id,
        title=title,
        body=body,
        status=status,
        created_at=created_at,
        updated_at=created_at,
        last_action_at=created_at,
        chase_count=chase_count,
    )
    session.add(request)
    session.flush()

    _add_event(
        session,
        request,
        "created",
        f"{requester.name} raised a request under '{process.name}'.",
        created_at,
        actor=requester.name,
    )
    _add_event(
        session,
        request,
        "dispatch",
        f"Dispatched to {assignee.name} ({assignee.title}) as accountable owner.",
        created_at,
    )
    session.add(
        Message(
            request_id=request.id,
            sender_id=requester.id,
            recipient_id=assignee.id,
            type="dispatch",
            body=body,
            created_at=created_at,
            read=status != "pending",
        )
    )

    last_action = created_at
    if ack_after_hours is not None:
        acked = created_at + timedelta(hours=ack_after_hours)
        request.acknowledged_at = acked
        last_action = acked
        _add_event(
            session,
            request,
            "acknowledged",
            f"{assignee.name} acknowledged the request.",
            acked,
            actor=assignee.name,
        )
    if status == "in_progress":
        started = last_action + timedelta(hours=1.5)
        last_action = started
        _add_event(
            session,
            request,
            "status_update",
            f"{assignee.name} moved the request to In progress.",
            started,
            actor=assignee.name,
        )
    if complete_after_hours is not None:
        done = created_at + timedelta(hours=complete_after_hours)
        request.completed_at = done
        last_action = done
        _add_event(
            session,
            request,
            "completed",
            f"{assignee.name} completed the request.",
            done,
            actor=assignee.name,
        )
        session.add(
            Message(
                request_id=request.id,
                sender_id=assignee.id,
                recipient_id=requester.id,
                type="status_update",
                body=f"Your request '{title}' has been completed.",
                created_at=done,
                read=False,
            )
        )

    if last_action_offset_hours is not None:
        last_action = created_at + timedelta(hours=last_action_offset_hours)

    request.last_action_at = last_action
    request.updated_at = last_action
    return request


def seed(reset: bool = True) -> None:
    """Build a fresh database. Destroys any existing one when ``reset`` is set."""
    if reset:
        drop_all()
    create_all()

    rng = random.Random(20240517)

    with session_scope() as session:
        for key, value in config.DEFAULT_SETTINGS.items():
            set_setting(session, key, value)
        session.flush()

        base = now(session)

        departments: dict[str, Department] = {}
        for name in DEPARTMENTS:
            dept = Department(name=name)
            session.add(dept)
            departments[name] = dept
        session.flush()

        people: dict[str, Person] = {}
        for name, title, dept_name, _manager in PEOPLE:
            person = Person(
                name=name,
                title=title,
                department_id=departments[dept_name].id if dept_name else None,
                email=_email(name),
                is_ooo=False,
            )
            session.add(person)
            people[name] = person
        session.flush()

        for name, _title, _dept, manager_name in PEOPLE:
            if manager_name:
                people[name].manager_id = people[manager_name].id

        for name, days in OOO_PEOPLE.items():
            people[name].is_ooo = True
            people[name].ooo_until = base + timedelta(days=days)

        processes: dict[str, Process] = {}
        for name, category, description, keywords in PROCESSES:
            proc = Process(
                name=name, category=category, description=description, keywords=keywords
            )
            session.add(proc)
            processes[name] = proc
        session.flush()

        for process_name, roles in RESPONSIBILITIES.items():
            for role, holders in roles.items():
                for holder in holders:
                    session.add(
                        Responsibility(
                            process_id=processes[process_name].id,
                            person_id=people[holder].id,
                            role=role,
                        )
                    )
        session.flush()

        _seed_history(session, rng, base, people, processes)

        session.add(
            Event(
                request_id=None,
                type="seed",
                detail=(
                    f"Database seeded: {len(people)} people, {len(departments)} departments, "
                    f"{len(processes)} processes."
                ),
                actor="system",
                created_at=base,
            )
        )
        set_setting(session, "seeded_at", base.isoformat())


def _seed_history(session, rng, base, people, processes) -> None:
    """Historical requests in mixed states, including overdue ones."""

    def hours_ago(h: float):
        return base - timedelta(hours=h)

    completed = [
        (
            "Expense Reimbursement", "Marco Bianchi", "Peter Lindqvist",
            "Reimbursement for Riyadh site visit",
            "Three nights and taxis for the Riyadh management meeting. Receipts attached.",
            410.0, 3.5, 29.0,
        ),
        (
            "IT Access Provisioning", "Sofia Marchetti", "Bilal Rahman",
            "Access to the portfolio monitoring drive",
            "I need read access to the portfolio monitoring shared drive for the quarterly pack.",
            330.0, 1.5, 8.0,
        ),
        (
            "IT Access Provisioning", "Anna Sorenson", "Bilal Rahman",
            "Locked out of the expenses portal",
            "MFA re-enrolment failed after my phone was replaced.",
            220.0, 0.5, 2.0,
        ),
        (
            "Invoice Approval", "Youssef Karim", "Rania Khoury",
            "Invoice 88412 — Meridian Advisory",
            "Q1 advisory retainer, goods receipted. Please approve for the Friday payment run.",
            190.0, 4.0, 26.0,
        ),
        (
            "Travel Approval", "Noura Al-Sabah", "Hamza Al-Dosari",
            "Travel to Manama for portfolio review",
            "Two nights, flying out Tuesday morning, returning Thursday evening.",
            150.0, 2.0, 12.0,
        ),
        (
            "Data Room Access", "Omar Haddad", "Layla Mansour",
            "Data room access for the Northgate diligence team",
            "Three analysts need read access to the Northgate folder before Monday.",
            120.0, 5.0, 41.0,
        ),
    ]
    for proc, requester, assignee, title, body, created_h, ack_h, done_h in completed:
        _seed_request(
            session,
            requester=people[requester],
            process=processes[proc],
            assignee=people[assignee],
            title=title,
            body=body,
            status="completed",
            created_at=hours_ago(created_h),
            ack_after_hours=ack_h,
            complete_after_hours=done_h,
        )

    in_progress = [
        (
            "Travel Approval", "Michael Trent", "Hamza Al-Dosari",
            "Flights for the Halcyon site visit",
            "Two of us, out Wednesday back Friday. Fares are moving so worth booking early.",
            70.0, 5.0,
        ),
        (
            "Expense Reimbursement", "Anna Sorenson", "Peter Lindqvist",
            "Office supplies bought on a personal card",
            "The card on file was declined, so I paid for the print cartridges myself.",
            58.0, 9.0,
        ),
        (
            "IT Access Provisioning", "Khalid Al-Rayes", "Bilal Rahman",
            "Board portal access for the new committee member",
            "Please set up an account before the next investment committee.",
            44.0, 2.0,
        ),
    ]
    for proc, requester, assignee, title, body, created_h, ack_h in in_progress:
        _seed_request(
            session,
            requester=people[requester],
            process=processes[proc],
            assignee=people[assignee],
            title=title,
            body=body,
            status="in_progress",
            created_at=hours_ago(created_h),
            ack_after_hours=ack_h,
        )

    acknowledged = [
        (
            "Valuation Sign-off", "Amira Haddadin", "Huda Al-Najjar",
            "Q1 valuation sign-off — Falcon and Cedar holdings",
            "Both marks need controller sign-off before the NAV is struck on the 15th.",
            36.0, 4.0,
        ),
        (
            "Expense Reimbursement", "Yousef Darwish", "Peter Lindqvist",
            "Client dinner — Cedarline management",
            "Dinner with the Cedarline management team after the site visit.",
            30.0, 3.0,
        ),
        (
            "IT Access Provisioning", "Dina Al-Kaabi", "Bilal Rahman",
            "HR system access for new joiner",
            "New HR business partner starts Monday and needs the usual joiner bundle.",
            26.0, 1.0,
        ),
    ]
    for proc, requester, assignee, title, body, created_h, ack_h in acknowledged:
        _seed_request(
            session,
            requester=people[requester],
            process=processes[proc],
            assignee=people[assignee],
            title=title,
            body=body,
            status="acknowledged",
            created_at=hours_ago(created_h),
            ack_after_hours=ack_h,
        )

    fresh_pending = [
        (
            "Invoice Approval", "Anna Sorenson", "Rania Khoury",
            "Invoice 88596 — Halcyon Facilities",
            "First invoice from the new facilities contractor. Please approve.",
            9.0,
        ),
        (
            "Travel Approval", "Marco Bianchi", "Hamza Al-Dosari",
            "Travel to London for the Cedarline signing",
            "One night, needs to be booked this week while fares hold.",
            5.0,
        ),
        (
            "Expense Reimbursement", "Sarah Whitfield", "Peter Lindqvist",
            "Taxis during the Sandpiper roadshow",
            "Four days of client meetings across the city. Receipts are in the folder.",
            3.0,
        ),
    ]
    for proc, requester, assignee, title, body, created_h in fresh_pending:
        _seed_request(
            session,
            requester=people[requester],
            process=processes[proc],
            assignee=people[assignee],
            title=title,
            body=body,
            status="pending",
            created_at=hours_ago(created_h),
        )

    # Deliberately overdue: the agent picks these up on its first tick, so the
    # Agent Log is never empty when the demo starts.
    overdue = [
        (
            "Invoice Approval", "Tomas Ferreira", "Rania Khoury",
            "Invoice 88604 — custodian quarterly fee",
            "The custodian fee is due at the end of the week.",
            53.0,
        ),
        (
            "Travel Approval", "Claire Donovan", "Hamza Al-Dosari",
            "Ops offsite — flights and hotel",
            "Six of us, two nights, the week after next.",
            51.0,
        ),
    ]
    for proc, requester, assignee, title, body, created_h in overdue:
        _seed_request(
            session,
            requester=people[requester],
            process=processes[proc],
            assignee=people[assignee],
            title=title,
            body=body,
            status="pending",
            created_at=hours_ago(created_h),
        )

    # A historical escalation so the dashboard's escalation rate is non-zero.
    escalated = _seed_request(
        session,
        requester=people["Fatima Al-Zahrani"],
        process=processes["Valuation Sign-off"],
        assignee=people["Huda Al-Najjar"],
        title="Valuation inputs for the data warehouse feed",
        body="I need the signed-off marks to backfill the warehouse before quarter end.",
        status="pending",
        created_at=hours_ago(146.0),
    )
    t0 = escalated.created_at
    escalated.chase_count = 2
    _add_event(session, escalated, "chase", "No acknowledgement after 48h — chase 1 of 2 sent to Huda Al-Najjar.", t0 + timedelta(hours=48))
    _add_event(session, escalated, "chase", "Still unacknowledged — chase 2 of 2 sent to Huda Al-Najjar.", t0 + timedelta(hours=72))
    _add_event(
        session,
        escalated,
        "escalation",
        "Two chases went unanswered and no delegate is configured for 'Valuation Sign-off'. "
        "Escalated to Amira Haddadin (Chief Financial Officer).",
        t0 + timedelta(hours=96),
    )
    escalated.status = "escalated"
    escalated.assignee_id = people["Amira Haddadin"].id
    escalated.last_action_at = t0 + timedelta(hours=96)
    escalated.updated_at = t0 + timedelta(hours=96)
    session.add(
        Message(
            request_id=escalated.id,
            sender_id=None,
            recipient_id=people["Amira Haddadin"].id,
            type="escalation",
            body=(
                "Escalated: 'Valuation inputs for the data warehouse feed' was not picked up by "
                "Huda Al-Najjar after two chases."
            ),
            created_at=t0 + timedelta(hours=96),
            read=False,
        )
    )
    # rng is used to jitter read flags so inboxes look lived-in rather than uniform.
    for message in session.query(Message).all():
        if message.type == "dispatch" and rng.random() < 0.35:
            message.read = True


if __name__ == "__main__":  # pragma: no cover
    seed()
    print(f"Seeded {config.DB_PATH}")
