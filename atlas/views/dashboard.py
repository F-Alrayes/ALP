"""Dashboard — queue health, bottlenecks, orphans and single points of failure.

Charts follow the ledger's dataviz rules: thin marks with surface gaps, one
axis, recessive grid, status colors reserved for status, direct labels where
they earn their place, and a styled hover layer on every plot.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from atlas import analytics, clock
from atlas.config import PALETTE, STATUS_COLORS
from atlas.db import session_scope
from atlas.services import STATUS_LABELS
from atlas.ui import motion
from atlas.ui.components import badge, empty_state, esc, page_header, stat

SURFACE = PALETTE["cream_200"]         # panel surface: the bar-gap and hover color
INK = PALETTE["ink"]
MUTED = PALETTE["muted"]
GRID = "#ECE4CF"
SERIES_ACK = PALETTE["gold_500"]       # time to acknowledge (validated gold)
SERIES_DONE = PALETTE["green_600"]     # time to complete (validated green)
AGE_RAMP = ["#B9D6C5", "#7FB99A", "#3FA173", "#128A5E"]  # light → dark, one hue

STATUS_ORDER = ["pending", "acknowledged", "in_progress", "escalated", "completed"]

HOVER = {
    "bgcolor": SURFACE,
    "bordercolor": PALETTE["cream_300"],
    "font": {"color": INK, "size": 12, "family": "Instrument Sans, sans-serif"},
}


def _style(figure: go.Figure, height: int = 300) -> go.Figure:
    figure.update_layout(
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": INK, "size": 12, "family": "Instrument Sans, sans-serif"},
        margin={"l": 4, "r": 8, "t": 8, "b": 4},
        hoverlabel=HOVER,
        bargap=0.45,
    )
    figure.update_xaxes(gridcolor=GRID, zeroline=False, showline=False,
                        tickfont={"color": MUTED, "size": 11})
    figure.update_yaxes(gridcolor=GRID, zeroline=False, showline=False,
                        tickfont={"color": MUTED, "size": 11})
    return figure


def _legend_top(figure: go.Figure) -> go.Figure:
    figure.update_layout(legend={
        "orientation": "h", "y": 1.04, "yanchor": "bottom", "x": 0,
        "title": None, "font": {"color": MUTED, "size": 11},
    })
    return figure


def _plot(figure: go.Figure) -> None:
    st.plotly_chart(figure, width="stretch", config={"displayModeBar": False})


def render(actor_id: int) -> None:
    page_header(
        "Dashboard",
        "Where work is stuck",
        "Live against the simulated clock.",
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
        stat("Avg acknowledge", f"{head['avg_ack_hours']:.1f}h", "first response")
    with cols[2]:
        stat("Avg complete", f"{head['avg_cycle_hours']:.1f}h", "raised to closed")
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
    motion.count_up_stats()

    st.markdown("## Queue")
    left, right = st.columns(2)

    with left, st.container(border=True, key="card_status"):
        st.markdown("<div class='chart-head'>Requests by status</div>",
                    unsafe_allow_html=True)
        frame = pd.DataFrame(status_rows)
        if frame.empty or frame["count"].sum() == 0:
            empty_state("No requests yet.")
        else:
            order = [STATUS_LABELS[s] for s in STATUS_ORDER]
            frame["order"] = frame["status"].apply(
                lambda s: order.index(s) if s in order else 99)
            frame = frame.sort_values("order", ascending=False)
            colors = [STATUS_COLORS.get(row["key"], SERIES_DONE)
                      for _, row in frame.iterrows()]
            figure = go.Figure(go.Bar(
                x=frame["count"], y=frame["status"], orientation="h",
                marker={"color": colors,
                        "line": {"color": SURFACE, "width": 2}},
                text=frame["count"], textposition="outside", cliponaxis=False,
                textfont={"color": INK, "size": 12},
                hovertemplate="%{y}: %{x} request(s)<extra></extra>",
            ))
            figure.update_xaxes(showticklabels=False, showgrid=False)
            _plot(_style(figure, height=280))

    with right, st.container(border=True, key="card_dept"):
        st.markdown("<div class='chart-head'>Open requests by department</div>",
                    unsafe_allow_html=True)
        if not dept_rows:
            empty_state("Nothing open right now.", "Every queue is clear.")
        else:
            frame = pd.DataFrame(dept_rows)
            figure = go.Figure()
            for key in STATUS_ORDER:
                label = STATUS_LABELS[key]
                sub = frame[frame["status"] == label]
                if sub.empty:
                    continue
                figure.add_bar(
                    x=sub["department"], y=sub["count"], name=label,
                    marker={"color": STATUS_COLORS[key],
                            "line": {"color": SURFACE, "width": 2}},
                    hovertemplate="%{x} · " + label + ": %{y}<extra></extra>",
                )
            figure.update_layout(barmode="stack")
            figure.update_xaxes(tickangle=-20, showgrid=False)
            _plot(_legend_top(_style(figure, height=280)))

    left, right = st.columns(2)
    with left, st.container(border=True, key="card_turnaround"):
        st.markdown("<div class='chart-head'>Turnaround by department"
                    "<span class='chart-note'>simulated hours</span></div>",
                    unsafe_allow_html=True)
        if not turnaround_rows:
            empty_state("No completed requests yet.")
        else:
            frame = pd.DataFrame(turnaround_rows)
            figure = go.Figure()
            figure.add_bar(
                x=frame["department"], y=frame["avg_ack_hours"],
                name="Time to acknowledge",
                marker={"color": SERIES_ACK, "line": {"color": SURFACE, "width": 2}},
                hovertemplate="%{x} · acknowledged in %{y:.1f}h<extra></extra>",
            )
            figure.add_bar(
                x=frame["department"], y=frame["avg_complete_hours"],
                name="Time to complete",
                marker={"color": SERIES_DONE, "line": {"color": SURFACE, "width": 2}},
                hovertemplate="%{x} · completed in %{y:.1f}h<extra></extra>",
            )
            figure.update_layout(barmode="group", bargroupgap=0.12)
            figure.update_xaxes(tickangle=-20, showgrid=False)
            _plot(_legend_top(_style(figure, height=280)))

    with right, st.container(border=True, key="card_ages"):
        st.markdown("<div class='chart-head'>How long open items have waited"
                    "<span class='chart-note'>darker = older</span></div>",
                    unsafe_allow_html=True)
        if not queue_rows:
            empty_state("Nothing is waiting.")
        else:
            ages = [row["age_hours"] for row in queue_rows]
            buckets = ["under 24h", "24–48h", "48–96h", "over 96h"]
            counts = [
                sum(1 for a in ages if a < 24),
                sum(1 for a in ages if 24 <= a < 48),
                sum(1 for a in ages if 48 <= a < 96),
                sum(1 for a in ages if a >= 96),
            ]
            figure = go.Figure(go.Bar(
                x=buckets, y=counts,
                marker={"color": AGE_RAMP, "line": {"color": SURFACE, "width": 2}},
                text=counts, textposition="outside", cliponaxis=False,
                textfont={"color": INK, "size": 12},
                hovertemplate="%{x}: %{y} open request(s)<extra></extra>",
            ))
            figure.update_yaxes(showticklabels=False, showgrid=False)
            figure.update_xaxes(showgrid=False)
            _plot(_style(figure, height=280))

    st.markdown("## Bottlenecks")
    if not bottleneck_rows:
        empty_state("No queues are backing up.")
    else:
        frame = pd.DataFrame(bottleneck_rows).rename(columns={
            "person": "Person", "title": "Title", "department": "Department",
            "open": "Open", "avg_wait_hours": "Avg wait (h)",
            "oldest_wait_hours": "Oldest (h)", "is_ooo": "Out of office",
        })
        st.dataframe(
            frame, width="stretch", hide_index=True,
            column_config={
                "Open": st.column_config.ProgressColumn(
                    "Open", format="%d",
                    max_value=max(int(frame["Open"].max()), 1),
                ),
                "Avg wait (h)": st.column_config.NumberColumn(format="%.1f"),
                "Oldest (h)": st.column_config.NumberColumn(format="%.0f"),
            },
        )

    st.markdown("## Orphaned processes")
    st.caption("No owner to route to — these park with the admin.")
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
    st.caption("Uncovered = no delegate or backup behind them.")
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
                uncovered = f"Approves on {row.approves} process(es) but owns none outright."
            st.markdown(
                f"""<div class="card {'accent' if row.uncovered else ''}">
                      <div class="card-title">{esc(row.person)}</div>
                      <div class="card-meta">{esc(row.title)} · {esc(row.department)}</div>
                      <div style="margin-top:0.45rem">{chips}</div>
                      <div class="card-body">{esc(uncovered)}</div>
                    </div>""",
                unsafe_allow_html=True,
            )
