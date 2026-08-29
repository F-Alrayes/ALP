"""Dashboard — queue health, bottlenecks, orphans and single points of failure."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from atlas import analytics, clock
from atlas.config import PALETTE, STATUS_COLORS
from atlas.db import session_scope
from atlas.ui.components import badge, empty_state, esc, page_header, stat

CHART_LAYOUT = {
    "paper_bgcolor": "rgba(0,0,0,0)",
    "plot_bgcolor": "rgba(0,0,0,0)",
    "font": {"color": PALETTE["ink"], "size": 12},
    "margin": {"l": 10, "r": 10, "t": 46, "b": 10},
    # Above the plot: angled department labels below would otherwise run into it.
    "legend": {"orientation": "h", "y": 1.06, "yanchor": "bottom", "x": 0, "title": None},
}

STATUS_LABEL_COLORS = {
    "Pending": STATUS_COLORS["pending"],
    "Acknowledged": STATUS_COLORS["acknowledged"],
    "In progress": STATUS_COLORS["in_progress"],
    "Escalated": STATUS_COLORS["escalated"],
    "Completed": STATUS_COLORS["completed"],
}


def _style(figure: go.Figure, height: int = 320, tickangle: int | None = None) -> go.Figure:
    figure.update_layout(height=height, **CHART_LAYOUT)
    figure.update_xaxes(gridcolor=PALETTE["cream_300"], zeroline=False)
    figure.update_yaxes(gridcolor=PALETTE["cream_300"], zeroline=False)
    if tickangle is not None:
        # Department names are long; angling them keeps them off the legend.
        figure.update_layout(margin={"l": 10, "r": 10, "t": 46, "b": 96})
        figure.update_xaxes(tickangle=tickangle)
    return figure


def render(actor_id: int) -> None:
    page_header(
        "Dashboard",
        "Where work is actually stuck",
        "Queue times, bottlenecks, orphaned processes and single points of failure — "
        "computed live against simulated time.",
    )

    with session_scope() as session:
        at = clock.now(session)
        head = analytics.headline(session)
        status_rows = analytics.by_status(session)
        dept_rows = analytics.open_by_department(session)
        turnaround_rows = analytics.turnaround_by_department(session)
        orphans = analytics.orphan_processes(session)
        spofs = analytics.single_points_of_failure(session, threshold=2)
        bottleneck_rows = analytics.bottlenecks(session)
        queue_rows = analytics.queue_ages(session)

    st.caption(f"Simulated time: {clock.fmt(at)}")

    cols = st.columns(5)
    with cols[0]:
        stat("Open requests", str(head["open_requests"]), f"of {head['total_requests']} raised")
    with cols[1]:
        stat("Avg time to acknowledge", f"{head['avg_ack_hours']:.1f}h", "first response")
    with cols[2]:
        stat("Avg time to complete", f"{head['avg_cycle_hours']:.1f}h", "raised to closed")
    with cols[3]:
        stat(
            "Escalation rate",
            f"{head['escalation_rate']:.0f}%",
            f"{head['escalated_requests']} escalated",
            "danger" if head["escalation_rate"] >= 20 else "",
        )
    with cols[4]:
        stat(
            "Oldest open item",
            f"{head['oldest_open_hours']:.0f}h",
            "still waiting",
            "warn" if head["oldest_open_hours"] >= 48 else "",
        )

    st.markdown("## Queue")
    left, right = st.columns(2)

    with left:
        st.markdown("#### Requests by status")
        frame = pd.DataFrame(status_rows)
        if frame["count"].sum() == 0:
            empty_state("No requests yet.")
        else:
            figure = px.bar(
                frame,
                x="count",
                y="status",
                orientation="h",
                color="status",
                color_discrete_map=STATUS_LABEL_COLORS,
                text="count",
            )
            figure.update_traces(showlegend=False, textposition="outside", cliponaxis=False)
            figure.update_layout(xaxis_title=None, yaxis_title=None)
            st.plotly_chart(_style(figure), width="stretch",
                            config={"displayModeBar": False})

    with right:
        st.markdown("#### Open requests by department")
        if not dept_rows:
            empty_state("Nothing open right now.", "Every queue is clear.")
        else:
            frame = pd.DataFrame(dept_rows)
            figure = px.bar(
                frame,
                x="department",
                y="count",
                color="status",
                color_discrete_map=STATUS_LABEL_COLORS,
                barmode="stack",
            )
            figure.update_layout(xaxis_title=None, yaxis_title="open requests")
            st.plotly_chart(_style(figure, tickangle=-25), width="stretch",
                            config={"displayModeBar": False})

    left, right = st.columns(2)
    with left:
        st.markdown("#### Turnaround by department")
        if not turnaround_rows:
            empty_state("No completed requests yet.")
        else:
            frame = pd.DataFrame(turnaround_rows)
            melted = frame.melt(
                id_vars="department",
                value_vars=["avg_ack_hours", "avg_complete_hours"],
                var_name="metric",
                value_name="hours",
            )
            melted["metric"] = melted["metric"].map(
                {"avg_ack_hours": "Time to acknowledge", "avg_complete_hours": "Time to complete"}
            )
            figure = px.bar(
                melted,
                x="department",
                y="hours",
                color="metric",
                barmode="group",
                color_discrete_sequence=[PALETTE["gold_500"], PALETTE["green_700"]],
            )
            figure.update_layout(xaxis_title=None, yaxis_title="simulated hours")
            st.plotly_chart(_style(figure, tickangle=-25), width="stretch",
                            config={"displayModeBar": False})

    with right:
        st.markdown("#### How long open items have been waiting")
        if not queue_rows:
            empty_state("Nothing is waiting.")
        else:
            frame = pd.DataFrame(queue_rows)
            figure = px.histogram(
                frame,
                x="age_hours",
                nbins=12,
                color_discrete_sequence=[PALETTE["green_600"]],
            )
            figure.update_layout(xaxis_title="age in simulated hours", yaxis_title="requests")
            st.plotly_chart(_style(figure), width="stretch",
                            config={"displayModeBar": False})

    st.markdown("## Bottlenecks")
    if not bottleneck_rows:
        empty_state("No queues are backing up.")
    else:
        frame = pd.DataFrame(bottleneck_rows)
        frame = frame.rename(
            columns={
                "person": "Person",
                "title": "Title",
                "department": "Department",
                "open": "Open",
                "avg_wait_hours": "Avg wait (h)",
                "oldest_wait_hours": "Oldest (h)",
                "is_ooo": "Out of office",
            }
        )
        st.dataframe(frame, width="stretch", hide_index=True)

    st.markdown("## Orphaned processes")
    st.caption("Requests matched to these have no owner to route to — they park for the admin.")
    if not orphans:
        st.success("Every process has an owner.")
    else:
        for row in orphans:
            st.markdown(
                f"""<div class="card accent">
                      <div class="card-title">{esc(row['process'])} {badge('No owner', 'escalated')}</div>
                      <div class="card-meta">{esc(row['category'])} ·
                        {row['open_requests']} open request(s) ·
                        other roles configured: {esc(row['other_roles'])}</div>
                    </div>""",
                unsafe_allow_html=True,
            )

    st.markdown("## Single points of failure")
    st.caption(
        "People carrying several processes. 'Uncovered' means the process has no available "
        "delegate or backup behind them."
    )
    if not spofs:
        st.success("No individual carries enough uncovered processes to be a concern.")
    else:
        for row in spofs:
            tone = "escalated" if row.uncovered else "role"
            chips = badge(f"{row.owns} owned", "role") + " " + badge(f"{row.approves} approved", "role")
            chips += " " + badge(f"{row.open_load} open", "gold" if row.open_load else "muted")
            if row.is_ooo:
                chips += " " + badge("Out of office", "ooo")
            if row.uncovered:
                chips += " " + badge(f"{len(row.uncovered)} uncovered", tone)
            if row.uncovered:
                uncovered = "Uncovered: " + ", ".join(row.uncovered)
            elif row.owns:
                uncovered = "Every process they own has a delegate or backup."
            else:
                uncovered = (
                    f"Approves on {row.approves} process(es) but owns none outright."
                )
            st.markdown(
                f"""<div class="card {'accent' if row.uncovered else ''}">
                      <div class="card-title">{esc(row.person)}</div>
                      <div class="card-meta">{esc(row.title)} · {esc(row.department)}</div>
                      <div style="margin-top:0.45rem">{chips}</div>
                      <div class="card-body">{esc(uncovered)}</div>
                    </div>""",
                unsafe_allow_html=True,
            )
