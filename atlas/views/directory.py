"""Directory & Graph — browse the org, the processes, and the edges between them."""

from __future__ import annotations

import math

import plotly.graph_objects as go
import streamlit as st

from atlas import analytics, clock
from atlas.config import OPEN_STATUSES, PALETTE
from atlas.db import session_scope
from atlas.models import Department, Person, Process, Request, Responsibility
from atlas.routing import holders, is_out_of_office, responsibilities_of
from atlas.ui.components import (
    badge,
    empty_state,
    esc,
    kv,
    page_header,
    status_badge,
)

PERSON_KEY = "atlas_directory_person"
PROCESS_KEY = "atlas_directory_process"

ROLE_COLORS = {
    "owner": PALETTE["green_700"],
    "approver": PALETTE["gold_600"],
    "delegate": PALETTE["green_600"],
    "backup": PALETTE["muted"],
}


# --- profiles ---------------------------------------------------------------


def _person_profile(person_id: int) -> None:
    with session_scope() as session:
        person = session.get(Person, person_id)
        if person is None:
            st.session_state.pop(PERSON_KEY, None)
            st.rerun()
            return
        at = clock.now(session)
        dept = session.get(Department, person.department_id) if person.department_id else None
        manager = session.get(Person, person.manager_id) if person.manager_id else None
        reports = (
            session.query(Person)
            .filter(Person.manager_id == person.id)
            .order_by(Person.name)
            .all()
        )
        grouped = responsibilities_of(session, person_id)
        stats = analytics.person_stats(session, person_id)
        recent = (
            session.query(Request)
            .filter(Request.assignee_id == person_id)
            .order_by(Request.last_action_at.desc())
            .limit(6)
            .all()
        )
        recent_rows = [
            {
                "id": r.id,
                "title": r.title,
                "status": r.status,
                "process": r.process.name if r.process else "Unmatched",
                "age": clock.humanize_delta(at - r.created_at),
            }
            for r in recent
        ]
        report_names = [p.name for p in reports]
        role_map = {role: [p.name for p in procs] for role, procs in grouped.items() if procs}
        ooo = is_out_of_office(person, at)
        ooo_until = clock.fmt(person.ooo_until, with_time=False) if person.ooo_until else None
        person_view = {
            "name": person.name,
            "title": person.title,
            "email": person.email,
            "dept": dept.name if dept else "Executive",
            "manager": manager.name if manager else "—",
        }

    if st.button("← Back", key="back_person"):
        st.session_state.pop(PERSON_KEY, None)
        st.rerun()

    st.markdown(
        f"""<div class="card accent">
              <div class="card-title">{esc(person_view['name'])}
                {badge('Out of office until ' + ooo_until, 'ooo') if ooo and ooo_until else ''}</div>
              <div class="card-meta">{esc(person_view['title'])} · {esc(person_view['dept'])} ·
                {esc(person_view['email'])}</div>
            </div>""",
        unsafe_allow_html=True,
    )

    cols = st.columns(4)
    with cols[0]:
        from atlas.ui.components import stat

        stat("Open load", str(stats["open_load"]), "requests with them now",
             "warn" if stats["open_load"] >= 3 else "")
    with cols[1]:
        stat("Completed", str(stats["completed"]), "all time")
    with cols[2]:
        stat(
            "Avg turnaround",
            f"{stats['avg_turnaround_hours']:.0f}h" if stats["avg_turnaround_hours"] else "—",
            "raised to completed",
        )
    with cols[3]:
        stat(
            "Avg to acknowledge",
            f"{stats['avg_ack_hours']:.0f}h" if stats["avg_ack_hours"] else "—",
            "first response",
        )

    left, right = st.columns(2)
    with left:
        st.markdown("#### Reporting line")
        kv("Manager", esc(person_view["manager"]))
        kv("Direct reports", esc(", ".join(report_names) if report_names else "—"))

        st.markdown("#### Responsibilities")
        if not role_map:
            st.markdown("<div class='subtle'>No edges in the responsibility graph.</div>", unsafe_allow_html=True)
        for role in ("owner", "approver", "delegate", "backup"):
            names = role_map.get(role)
            if not names:
                continue
            chips = " ".join(badge(n, "role") for n in names)
            st.markdown(
                f"<div class='kv'><span class='k'>{esc(role.capitalize())}</span>{chips}</div>",
                unsafe_allow_html=True,
            )

    with right:
        st.markdown("#### Recent requests")
        if not recent_rows:
            empty_state("No requests routed here yet.")
        for row in recent_rows:
            st.markdown(
                f"""<div class="card">
                      <div class="card-title">#{row['id']} — {esc(row['title'])}</div>
                      <div class="card-meta">{status_badge(row['status'])} &nbsp;
                        {esc(row['process'])} · {esc(row['age'])} old</div>
                    </div>""",
                unsafe_allow_html=True,
            )


def _process_profile(process_id: int) -> None:
    with session_scope() as session:
        process = session.get(Process, process_id)
        if process is None:
            st.session_state.pop(PROCESS_KEY, None)
            st.rerun()
            return
        at = clock.now(session)
        roles = {
            role: [
                {
                    "name": p.name,
                    "title": p.title,
                    "ooo": is_out_of_office(p, at),
                }
                for p in holders(session, process_id, role)
            ]
            for role in ("owner", "approver", "delegate", "backup")
        }
        stats = analytics.process_stats(session, process_id)
        recent = (
            session.query(Request)
            .filter(Request.process_id == process_id)
            .order_by(Request.created_at.desc())
            .limit(8)
            .all()
        )
        recent_rows = [
            {
                "id": r.id,
                "title": r.title,
                "status": r.status,
                "assignee": (
                    session.get(Person, r.assignee_id).name if r.assignee_id else "Unassigned"
                ),
                "age": clock.humanize_delta(at - r.created_at),
            }
            for r in recent
        ]
        view = {
            "name": process.name,
            "category": process.category,
            "description": process.description,
            "keywords": process.keyword_list,
        }

    if st.button("← Back", key="back_process"):
        st.session_state.pop(PROCESS_KEY, None)
        st.rerun()

    orphan = not roles["owner"]
    st.markdown(
        f"""<div class="card accent">
              <div class="card-title">{esc(view['name'])}
                {badge('Orphan — no owner', 'escalated') if orphan else ''}</div>
              <div class="card-meta">{esc(view['category'])}</div>
              <div class="card-body">{esc(view['description'])}</div>
            </div>""",
        unsafe_allow_html=True,
    )

    cols = st.columns(4)
    from atlas.ui.components import stat

    with cols[0]:
        stat("Requests", str(stats["total"]), "all time")
    with cols[1]:
        stat("Open now", str(stats["open"]), "in the queue", "warn" if stats["open"] else "")
    with cols[2]:
        stat("Completed", str(stats["completed"]), "all time")
    with cols[3]:
        stat(
            "Avg turnaround",
            f"{stats['avg_turnaround_hours']:.0f}h" if stats["avg_turnaround_hours"] else "—",
            "raised to completed",
        )

    left, right = st.columns(2)
    with left:
        st.markdown("#### Who is accountable")
        if orphan:
            st.error(
                "Nobody owns this process. Requests matched to it are parked for the Atlas admin."
            )
        for role in ("owner", "approver", "delegate", "backup"):
            people = roles[role]
            if not people:
                st.markdown(
                    f"<div class='kv'><span class='k'>{esc(role.capitalize())}</span>"
                    "<span class='subtle'>not configured</span></div>",
                    unsafe_allow_html=True,
                )
                continue
            chips = " ".join(
                badge(p["name"] + (" · OOO" if p["ooo"] else ""), "ooo" if p["ooo"] else "role")
                for p in people
            )
            st.markdown(
                f"<div class='kv'><span class='k'>{esc(role.capitalize())}</span>{chips}</div>",
                unsafe_allow_html=True,
            )

        st.markdown("#### Matching keywords")
        st.markdown(
            " ".join(badge(k, "muted") for k in view["keywords"]) or "<span class='subtle'>none</span>",
            unsafe_allow_html=True,
        )

    with right:
        st.markdown("#### Recent requests")
        if not recent_rows:
            empty_state("No requests have used this process yet.")
        for row in recent_rows:
            st.markdown(
                f"""<div class="card">
                      <div class="card-title">#{row['id']} — {esc(row['title'])}</div>
                      <div class="card-meta">{status_badge(row['status'])} &nbsp;
                        with {esc(row['assignee'])} · {esc(row['age'])} old</div>
                    </div>""",
                unsafe_allow_html=True,
            )


# --- graph ------------------------------------------------------------------


def _graph_figure(nodes: list[dict], edges: list[dict]) -> go.Figure:
    """Two rings: people inside, processes outside with labels pointing outward."""
    processes = [n for n in nodes if n["kind"] == "process"]
    people = [n for n in nodes if n["kind"] == "person"]
    positions: dict[str, tuple[float, float]] = {}
    angles: dict[str, float] = {}

    for i, node in enumerate(people):
        angle = 2 * math.pi * i / max(len(people), 1) - math.pi / 2
        positions[node["id"]] = (0.52 * math.cos(angle), 0.52 * math.sin(angle))
        angles[node["id"]] = angle
    for i, node in enumerate(processes):
        angle = 2 * math.pi * i / max(len(processes), 1) - math.pi / 2
        positions[node["id"]] = (math.cos(angle), math.sin(angle))
        angles[node["id"]] = angle

    figure = go.Figure()
    for role, color in ROLE_COLORS.items():
        xs: list[float | None] = []
        ys: list[float | None] = []
        for edge in edges:
            if edge["role"] != role:
                continue
            if edge["source"] not in positions or edge["target"] not in positions:
                continue
            x0, y0 = positions[edge["source"]]
            x1, y1 = positions[edge["target"]]
            xs += [x0, x1, None]
            ys += [y0, y1, None]
        if not xs:
            continue
        figure.add_trace(
            go.Scatter(
                x=xs,
                y=ys,
                mode="lines",
                line={"width": 1.5 if role == "owner" else 1.0, "color": color},
                opacity=0.9 if role == "owner" else 0.4,
                hoverinfo="skip",
                name=role.capitalize(),
            )
        )

    figure.add_trace(
        go.Scatter(
            x=[positions[n["id"]][0] for n in people],
            y=[positions[n["id"]][1] for n in people],
            mode="markers",
            marker={"size": 11, "color": PALETTE["green_700"], "line": {"width": 1.5, "color": "#FFFFFF"}},
            hovertext=[f"{n['label']}<br>{n['group']}" for n in people],
            hoverinfo="text",
            name="People",
        )
    )
    figure.add_trace(
        go.Scatter(
            x=[positions[n["id"]][0] for n in processes],
            y=[positions[n["id"]][1] for n in processes],
            mode="markers",
            marker={"size": 15, "color": PALETTE["gold_500"], "line": {"width": 1.5, "color": "#FFFFFF"}},
            hovertext=[f"{n['label']}<br>{n['group']}" for n in processes],
            hoverinfo="text",
            name="Processes",
        )
    )

    for node in processes:
        x, y = positions[node["id"]]
        angle = angles[node["id"]]
        on_right = math.cos(angle) >= 0
        figure.add_annotation(
            x=x + (0.045 if on_right else -0.045),
            y=y,
            text=node["label"],
            showarrow=False,
            xanchor="left" if on_right else "right",
            yanchor="middle",
            font={"size": 11, "color": PALETTE["green_900"]},
            bgcolor="rgba(255,255,255,0.88)",
            bordercolor=PALETTE["cream_300"],
            borderwidth=1,
            borderpad=3,
        )

    figure.update_layout(
        showlegend=True,
        legend={"orientation": "h", "y": -0.04},
        height=640,
        margin={"l": 10, "r": 10, "t": 10, "b": 10},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis={"visible": False, "range": [-1.95, 1.95]},
        yaxis={"visible": False, "range": [-1.18, 1.18]},
    )
    return figure


# --- page -------------------------------------------------------------------


def render(actor_id: int) -> None:
    page_header(
        "People",
        "Who owns the work",
        "Responsibility, not the reporting line.",
    )

    if st.session_state.get(PERSON_KEY):
        _person_profile(st.session_state[PERSON_KEY])
        return
    if st.session_state.get(PROCESS_KEY):
        _process_profile(st.session_state[PROCESS_KEY])
        return

    tab_people, tab_processes, tab_graph = st.tabs(["People", "Processes", "Responsibility graph"])

    with tab_people:
        with session_scope() as session:
            at = clock.now(session)
            departments = ["All departments"] + [
                d.name for d in session.query(Department).order_by(Department.name).all()
            ]
        col1, col2 = st.columns([2, 2])
        term = col1.text_input("Search people", placeholder="name or title", key="dir_person_q")
        dept_choice = col2.selectbox("Department", departments, key="dir_dept")

        with session_scope() as session:
            at = clock.now(session)
            query = session.query(Person)
            if term.strip():
                like = f"%{term.strip()}%"
                query = query.filter(Person.name.ilike(like) | Person.title.ilike(like))
            rows = []
            for person in query.order_by(Person.name).all():
                dept = (
                    session.get(Department, person.department_id).name
                    if person.department_id
                    else "Executive"
                )
                if dept_choice != "All departments" and dept != dept_choice:
                    continue
                owned = (
                    session.query(Responsibility)
                    .filter(
                        Responsibility.person_id == person.id,
                        Responsibility.role.in_(("owner", "approver")),
                    )
                    .count()
                )
                load = (
                    session.query(Request)
                    .filter(
                        Request.assignee_id == person.id, Request.status.in_(OPEN_STATUSES)
                    )
                    .count()
                )
                rows.append(
                    {
                        "id": person.id,
                        "name": person.name,
                        "title": person.title,
                        "dept": dept,
                        "owned": owned,
                        "load": load,
                        "ooo": is_out_of_office(person, at),
                        "ooo_until": clock.fmt(person.ooo_until, with_time=False)
                        if person.ooo_until
                        else "",
                    }
                )

        st.caption(f"{len(rows)} people")
        if not rows:
            empty_state("Nobody matches that search.")
        for row in rows:
            card, action = st.columns([6, 1], vertical_alignment="center")
            chips = badge(f"{row['owned']} owned/approved", "role") + " " + badge(
                f"{row['load']} open", "gold" if row["load"] else "muted"
            )
            if row["ooo"]:
                chips += " " + badge(f"OOO until {row['ooo_until']}", "ooo")
            card.markdown(
                f"""<div class="card">
                      <div class="card-title">{esc(row['name'])}</div>
                      <div class="card-meta">{esc(row['title'])} · {esc(row['dept'])}</div>
                      <div style="margin-top:0.45rem">{chips}</div>
                    </div>""",
                unsafe_allow_html=True,
            )
            if action.button("View", key=f"person_{row['id']}", width="stretch"):
                st.session_state[PERSON_KEY] = row["id"]
                st.rerun()

    with tab_processes:
        with session_scope() as session:
            at = clock.now(session)
            rows = []
            for process in session.query(Process).order_by(Process.name).all():
                owners = holders(session, process.id, "owner")
                delegates = holders(session, process.id, "delegate")
                open_count = (
                    session.query(Request)
                    .filter(
                        Request.process_id == process.id, Request.status.in_(OPEN_STATUSES)
                    )
                    .count()
                )
                rows.append(
                    {
                        "id": process.id,
                        "name": process.name,
                        "category": process.category,
                        "owner": owners[0].name if owners else None,
                        "owner_ooo": bool(owners) and is_out_of_office(owners[0], at),
                        "delegate": delegates[0].name if delegates else None,
                        "open": open_count,
                    }
                )
        for row in rows:
            card, action = st.columns([6, 1], vertical_alignment="center")
            if row["owner"]:
                chips = badge(f"Owner: {row['owner']}", "ooo" if row["owner_ooo"] else "role")
            else:
                chips = badge("Orphan — no owner", "escalated")
            if row["delegate"]:
                chips += " " + badge(f"Delegate: {row['delegate']}", "muted")
            chips += " " + badge(f"{row['open']} open", "gold" if row["open"] else "muted")
            card.markdown(
                f"""<div class="card">
                      <div class="card-title">{esc(row['name'])}</div>
                      <div class="card-meta">{esc(row['category'])}</div>
                      <div style="margin-top:0.45rem">{chips}</div>
                    </div>""",
                unsafe_allow_html=True,
            )
            if action.button("View", key=f"process_{row['id']}", width="stretch"):
                st.session_state[PROCESS_KEY] = row["id"]
                st.rerun()

    with tab_graph:
        st.caption("Gold = processes · green = people · lines = roles.")
        with session_scope() as session:
            departments = ["All departments"] + [
                d.name for d in session.query(Department).order_by(Department.name).all()
            ]
        choice = st.selectbox("Filter people by department", departments, key="graph_dept")
        with session_scope() as session:
            graph = analytics.responsibility_graph(
                session, None if choice == "All departments" else choice
            )
        if not graph["edges"]:
            empty_state("No responsibility edges to draw for that filter.")
        else:
            st.plotly_chart(
                _graph_figure(graph["nodes"], graph["edges"]),
                width="stretch",
                config={"displayModeBar": False},
            )
