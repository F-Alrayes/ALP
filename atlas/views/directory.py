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
from atlas.ui import theme
from atlas.ui.components import (
    badge,
    empty_state,
    esc,
    kv,
    page_header,
    status_badge,
)

def _ring() -> str:
    return "#16281F" if theme.is_dark() else PALETTE["cream_200"]


def _chart_ui() -> dict:
    from .dashboard import _ui

    return _ui()


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

    if st.button("Back to people", icon=":material/arrow_back:", key="back_person"):
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

    if st.button("Back to people", icon=":material/arrow_back:", key="back_process"):
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


# --- org tree ---------------------------------------------------------------


def _initials(name: str) -> str:
    parts = name.split()
    return (parts[0][0] + parts[-1][0]).upper() if len(parts) > 1 else name[:2].upper()


_LEAVE_REASONS = ("Annual leave", "Parental leave", "Business trip", "Medical leave")


def _org_status(person, away: bool, at) -> tuple[str, str]:
    """leave / notin / online, derived from OOO state and the simulated clock.
    Arrival is staggered per person (08:00-11:30) so the board shows life."""
    if away:
        return "leave", "On leave"
    hour = at.hour + at.minute / 60.0
    start = 8.0 + ((person.id * 37) % 15) / 4.0
    if hour < start:
        return "notin", "Not in office yet"
    if hour >= 18.5:
        return "notin", "Not in office"
    return "online", "Online"


def _org_node(person, dept, kids, hit, status, info) -> str:
    import html as _html
    import json as _json

    code, _label = status
    pill = (f'<button class="okids" data-n="{kids}">{kids}</button>' if kids else "")
    payload = _html.escape(_json.dumps(info), quote=True)
    return (
        f'<div class="onode {code}{" hit" if hit else ""}" data-info="{payload}">'
        f'<span class="odot {code}"></span>'
        f'<span class="oava">{esc(_initials(person.name))}</span>'
        f'<div class="oname">{esc(person.name)}</div>'
        f'<div class="orole">{esc(person.title)}</div>'
        f'<div class="odept">{esc(dept)}</div>'
        f"{pill}</div>"
    )


def _org_branch(person, ctx, highlight_id) -> str:
    children = ctx["children"].get(person.id, [])
    node = _org_node(
        person, ctx["dept"].get(person.department_id, "Executive"),
        len(children), person.id == highlight_id,
        ctx["status"][person.id], ctx["info"][person.id],
    )
    if not children:
        return f"<li>{node}</li>"
    kids = "".join(_org_branch(c, ctx, highlight_id) for c in children)
    return f'<li class="branch">{node}<ul>{kids}</ul></li>'


def _org_palette(dark: bool) -> dict:
    if dark:
        return {"card": "rgba(22,40,30,.88)", "line": "rgba(236,239,232,.18)",
                "ink": "#ECEFE8", "muted": "#9DAA9E", "amber": "#D9B254",
                "accent": "#E9C25C", "strong": "#1E4433",
                "tipbg": "#101E17", "btnbg": "rgba(236,239,232,.08)",
                "ring": "rgba(14,27,21,.9)",
                "online": "#3FBF8C", "notin": "#D9A441", "leave": "#E06B5B"}
    return {"card": "rgba(255,253,246,.88)", "line": "#E3DAC2",
            "ink": "#1B2721", "muted": "#566158", "amber": "#83660A",
            "accent": "#A8820F", "strong": "#14382A",
            "tipbg": "#FFFDF6", "btnbg": "rgba(255,253,246,.7)",
            "ring": "rgba(255,253,246,.94)",
            "online": "#128A5E", "notin": "#B0741B", "leave": "#BE3E2F"}


def _org_doc(branches: str) -> str:
    """A self-contained interactive chart: live search, zoom, collapse, status,
    hover cards."""
    from atlas.ui import theme as _theme
    from atlas.ui.theme import _font_css

    dark = _theme.is_dark()
    c = _org_palette(dark)
    scheme = "dark" if dark else "light"
    css = f"""
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; background: transparent; height: 100vh;
      display: flex; flex-direction: column; overflow: hidden;
      font-family: 'Instrument Sans', ui-sans-serif, system-ui, sans-serif; }}
    .mono {{ font-family: 'IBM Plex Mono', ui-monospace, monospace; }}
    .bar {{ display: flex; gap: 6px; align-items: center; margin: 0 0 6px;
      flex: none; flex-wrap: wrap; row-gap: 6px; }}
    .bar button {{ font-family: 'IBM Plex Mono', monospace; font-size: 12px;
      color: {c['ink']}; background: {c['btnbg']}; border: 1px solid {c['line']};
      border-radius: 9px; padding: 4px 10px; cursor: pointer;
      backdrop-filter: blur(8px); }}
    .bar button:hover {{ border-color: {c['accent']}; }}
    #zpct {{ font-family: 'IBM Plex Mono', monospace; font-size: 12px;
      color: {c['muted']}; min-width: 44px; text-align: center; }}
    .legend {{ margin-left: auto; display: flex; gap: 12px; align-items: center;
      flex-wrap: wrap; font-size: 11px; color: {c['muted']}; }}
    .legend span {{ display: inline-flex; gap: 5px; align-items: center; }}
    .ldot {{ width: 8px; height: 8px; border-radius: 50%; display: inline-block; }}
    :root {{ color-scheme: {scheme}; }}
    #wrap {{ overflow: auto; flex: 1; min-height: 0; border-radius: 14px;
      border: 1px solid {c['line']}; padding: 18px 8px 12px;
      cursor: grab; user-select: none; -webkit-user-select: none;
      overscroll-behavior: contain;
      scrollbar-width: thin; scrollbar-color: {c['line']} transparent; }}
    #wrap.grabbing {{ cursor: grabbing; }}
    #wrap.grabbing .onode {{ pointer-events: none; }}
    #tree {{ min-width: max-content; margin-inline: auto; }}
    #tree ul {{ display: flex; justify-content: center; padding: 20px 0 0;
      margin: 0; position: relative; list-style: none; }}
    #tree li {{ list-style: none; position: relative; padding: 20px 8px 10px;
      margin: 0; display: flex; flex-direction: column; align-items: center; }}
    #tree li::before, #tree li::after {{ content: ""; position: absolute; top: 0;
      right: 50%; width: 50%; height: 20px; border-top: 1.5px solid {c['line']}; }}
    #tree li::after {{ right: auto; left: 50%; border-left: 1.5px solid {c['line']}; }}
    #tree li:only-child::before, #tree li:only-child::after {{ display: none; }}
    #tree li:only-child {{ padding-top: 0; }}
    #tree li:first-child::before, #tree li:last-child::after {{ border: 0 none; }}
    #tree li:last-child::before {{ border-right: 1.5px solid {c['line']};
      border-radius: 0 8px 0 0; }}
    #tree li:first-child::after {{ border-radius: 8px 0 0 0; }}
    #tree ul ul::before {{ content: ""; position: absolute; top: 0; left: 50%;
      height: 20px; border-left: 1.5px solid {c['line']}; }}
    #tree > ul {{ padding-top: 0; }}
    #tree > ul > li {{ padding-top: 0; }}
    #tree > ul > li::before, #tree > ul > li::after {{ display: none; }}
    #tree li.closed > ul {{ display: none; }}
    .onode {{ position: relative; width: 156px; background: {c['card']};
      border: 1px solid {c['line']}; border-radius: 12px;
      padding: 11px 10px 9px; text-align: center; cursor: default;
      backdrop-filter: blur(10px) saturate(1.35);
      box-shadow: inset 0 3px 0 {c['strong']},
                  inset 0 4px 0 rgba(255,255,255,.35),
                  0 10px 24px -18px rgba(0,0,0,.45);
      transition: transform 160ms cubic-bezier(.23,1,.32,1),
                  border-color 160ms ease; }}
    @media (hover: hover) and (pointer: fine) {{
      .onode:hover {{ transform: translateY(-2px); border-color: {c['accent']}; }}
    }}
    .onode.hit {{ box-shadow: inset 0 3px 0 {c['accent']}, 0 0 0 2px {c['accent']}55,
      0 10px 24px -18px rgba(0,0,0,.45); }}
    .odot {{ position: absolute; top: -5px; left: 10px; width: 11px; height: 11px;
      border-radius: 50%; box-shadow: 0 0 0 3px {c['ring']}; }}
    .odot.online {{ background: {c['online']}; }}
    .odot.notin  {{ background: {c['notin']}; }}
    .odot.leave  {{ background: {c['leave']}; }}
    .oava {{ position: absolute; top: -12px; right: 9px; width: 26px; height: 26px;
      border-radius: 50%; background: {c['accent']}; color: #122019;
      font-family: 'IBM Plex Mono', monospace; font-weight: 600; font-size: 11px;
      display: grid; place-items: center; box-shadow: 0 0 0 3px {c['ring']},
      inset 0 1px 0 rgba(255,255,255,.35); }}
    .oname {{ font-weight: 600; font-size: 13px; color: {c['ink']}; line-height: 1.2; }}
    .orole {{ font-size: 11px; color: {c['muted']}; margin-top: 2px; line-height: 1.25; }}
    .odept {{ font-family: 'IBM Plex Mono', monospace; font-size: 11px;
      text-transform: uppercase; letter-spacing: .08em; color: {c['amber']};
      margin-top: 3px; }}
    .okids {{ position: absolute; left: 50%; bottom: -8px; transform: translateX(-50%);
      min-width: 19px; height: 19px; padding: 0 5px; border-radius: 5px; border: 0;
      background: {c['strong']}; color: #F3EEE0;
      font-family: 'IBM Plex Mono', monospace; font-size: 11px; font-weight: 600;
      display: grid; place-items: center; cursor: pointer;
      box-shadow: 0 0 0 2px {c['ring']}; }}
    li.closed .okids {{ background: {c['accent']}; color: #122019; }}
    #tip {{ position: fixed; z-index: 10; display: none; width: 264px;
      animation: tipin 125ms cubic-bezier(.23,1,.32,1) both;
      background: {c['tipbg']}; border: 1px solid {c['line']}; border-radius: 12px;
      padding: 11px 13px; font-size: 12px; color: {c['ink']};
      box-shadow: 0 18px 40px -18px rgba(0,0,0,.5); pointer-events: none; }}
    #tip .tname {{ font-weight: 600; font-size: 13px; }}
    #tip .tsub {{ color: {c['muted']}; margin-top: 1px; }}
    #tip .trow {{ margin-top: 7px; display: flex; gap: 6px; align-items: baseline; }}
    #tip .tkey {{ font-family: 'IBM Plex Mono', monospace; font-size: 11px;
      text-transform: uppercase; letter-spacing: .06em; color: {c['muted']};
      flex: none; min-width: 66px; }}
    #tip .tdot {{ width: 8px; height: 8px; border-radius: 50%;
      display: inline-block; margin-right: 5px; }}
    #tip .leaveline {{ color: {c['leave']}; }}
    .search {{ position: relative; flex: none; }}
    #q {{ font-family: 'Instrument Sans', ui-sans-serif, system-ui, sans-serif;
      font-size: 12.5px; color: {c['ink']}; background: {c['btnbg']};
      border: 1px solid {c['line']}; border-radius: 9px; padding: 5px 11px;
      width: 218px; outline: none; backdrop-filter: blur(8px); }}
    #q::placeholder {{ color: {c['muted']}; }}
    #q:focus {{ border-color: {c['accent']}; }}
    #sugg {{ position: absolute; top: calc(100% + 5px); left: 0; z-index: 30;
      width: 264px; display: none; background: {c['tipbg']};
      border: 1px solid {c['line']}; border-radius: 11px; padding: 4px;
      max-height: 262px; overflow: auto;
      box-shadow: 0 18px 40px -18px rgba(0,0,0,.5); }}
    .sg {{ padding: 6px 9px; border-radius: 8px; cursor: pointer; }}
    .sg .sn {{ display: block; font-weight: 600; font-size: 12.5px;
      color: {c['ink']}; }}
    .sg .sm {{ display: block; font-size: 11px; color: {c['muted']};
      margin-top: 1px; }}
    .sg.active {{ background: {c['btnbg']};
      box-shadow: inset 2px 0 0 {c['accent']}; }}
    .sg.none {{ cursor: default; font-size: 12px; color: {c['muted']};
      padding: 8px 9px; }}
    #sugg {{ transform-origin: top left;
      animation: popin 160ms cubic-bezier(.23,1,.32,1) both; }}
    #q::-webkit-search-cancel-button {{ -webkit-appearance: none; }}
    .bar button:focus-visible, #q:focus-visible, .okids:focus-visible {{
      outline: none; box-shadow: 0 0 0 3px {c['accent']}59;
      border-color: {c['accent']}; }}
    @keyframes tipin {{ from {{ opacity: 0; transform: translateY(4px); }} }}
    @keyframes popin {{ from {{ opacity: 0; transform: translateY(-4px) scale(.97); }} }}
    @keyframes orgin {{ from {{ opacity: 0; transform: translateY(-4px); }} }}
    @media (prefers-reduced-motion: no-preference) {{
      #tree li.branch:not(.closed) > ul {{
        animation: orgin 180ms cubic-bezier(.23,1,.32,1) both; }}
    }}
    @media (prefers-reduced-motion: reduce) {{
      #tip, #sugg {{ animation: none; }}
      .onode {{ transition: border-color 160ms ease; }}
      .onode:hover {{ transform: none; }}
    }}
    """
    return f"""<!DOCTYPE html><html><head><style>{_font_css()}</style>
<style>{css}</style></head><body>
<div class="bar">
  <div class="search">
    <input id="q" type="search" placeholder="Search people…" autocomplete="off"
           spellcheck="false">
    <div id="sugg"></div>
  </div>
  <button id="zo" title="Zoom out">−</button>
  <span id="zpct">100%</span>
  <button id="zi" title="Zoom in">+</button>
  <button id="zr">Fit</button>
  <button id="xall">Expand all</button>
  <button id="call">Collapse all</button>
  <div class="legend">
    <span><i class="ldot" style="background:{c['online']}"></i>Online</span>
    <span><i class="ldot" style="background:{c['notin']}"></i>Not in yet</span>
    <span><i class="ldot" style="background:{c['leave']}"></i>On leave</span>
  </div>
</div>
<div id="wrap"><div id="tree"><ul>{branches}</ul></div></div>
<div id="tip"></div>
<script>
const wrap = document.getElementById('wrap'), tree = document.getElementById('tree');
const tip = document.getElementById('tip'), zpct = document.getElementById('zpct');
let z = 1;
const setz = v => {{ z = Math.min(2, Math.max(.4, v)); tree.style.zoom = z;
  zpct.textContent = Math.round(z * 100) + '%'; }};
document.getElementById('zi').onclick = () => setz(z + .15);
document.getElementById('zo').onclick = () => setz(z - .15);
document.getElementById('zr').onclick = () => {{ setz(1); center(); }};
wrap.addEventListener('wheel', e => {{
  if (e.ctrlKey || e.metaKey) {{ e.preventDefault(); setz(z + (e.deltaY < 0 ? .1 : -.1)); }}
}}, {{passive: false}});
const setPill = li => {{ const b = li.querySelector(':scope > .onode .okids');
  if (b) b.textContent = (li.classList.contains('closed') ? '+' : '') + b.dataset.n; }};
document.querySelectorAll('.okids').forEach(b => b.addEventListener('click', e => {{
  e.stopPropagation(); const li = b.closest('li');
  li.classList.toggle('closed'); setPill(li); hide();
}}));
document.getElementById('xall').onclick = () => document.querySelectorAll('li.branch')
  .forEach(li => {{ li.classList.remove('closed'); setPill(li); }});
document.getElementById('call').onclick = () => document.querySelectorAll('li.branch')
  .forEach(li => {{ if (li.parentElement.parentElement !== tree) li.classList.add('closed');
                    setPill(li); }});
const hide = () => tip.style.display = 'none';
const pos = e => {{
  const w = 264, h = tip.offsetHeight || 160;
  tip.style.left = Math.min(e.clientX + 16, innerWidth - w - 10) + 'px';
  tip.style.top = (e.clientY + 18 + h > innerHeight
                   ? e.clientY - h - 12 : e.clientY + 18) + 'px'; }};
document.querySelectorAll('.onode').forEach(n => {{
  n.addEventListener('mouseenter', e => {{
    const d = JSON.parse(n.dataset.info);
    let rows = `<div class="tname">${{d.name}}</div>` +
      `<div class="tsub">${{d.title}} · ${{d.dept}}</div>` +
      `<div class="trow"><span class="tkey">Status</span>` +
      `<span><i class="tdot" style="background:${{d.dotColor}}"></i>${{d.status}}</span></div>`;
    if (d.leave) rows += `<div class="trow"><span class="tkey">Leave</span>` +
      `<span class="leaveline">${{d.leave.reason}} · back ${{d.leave.back}}</span></div>`;
    rows += `<div class="trow"><span class="tkey">Manager</span><span>${{d.manager}}</span></div>` +
      `<div class="trow"><span class="tkey">Email</span><span>${{d.email}}</span></div>`;
    (d.resp || []).forEach(r => rows +=
      `<div class="trow"><span class="tkey">${{r[0]}}</span><span>${{r[1]}}</span></div>`);
    tip.innerHTML = rows; tip.style.display = 'block'; pos(e);
  }});
  n.addEventListener('mousemove', pos);
  n.addEventListener('mouseleave', hide);
}});
wrap.addEventListener('scroll', hide);
let drag = null;
wrap.addEventListener('pointerdown', e => {{
  if (e.button !== 0 || e.target.closest('.okids')) return;
  drag = {{x: e.clientX, y: e.clientY,
          sl: wrap.scrollLeft, st: wrap.scrollTop, moved: false}};
  wrap.setPointerCapture(e.pointerId);
}});
wrap.addEventListener('pointermove', e => {{
  if (!drag) return;
  const dx = e.clientX - drag.x, dy = e.clientY - drag.y;
  if (!drag.moved && Math.abs(dx) + Math.abs(dy) > 4) {{
    drag.moved = true; hide(); wrap.classList.add('grabbing');
  }}
  if (drag.moved) {{ wrap.scrollLeft = drag.sl - dx; wrap.scrollTop = drag.st - dy; }}
}});
const endDrag = () => {{ drag = null; wrap.classList.remove('grabbing'); }};
wrap.addEventListener('pointerup', endDrag);
wrap.addEventListener('pointercancel', endDrag);
const center = () => wrap.scrollLeft = (wrap.scrollWidth - wrap.clientWidth) / 2;
requestAnimationFrame(center);

/* ---- live search: suggestions as you type ---- */
const q = document.getElementById('q'), sugg = document.getElementById('sugg');
const idx = [...document.querySelectorAll('.onode')].map(n => {{
  const d = JSON.parse(n.dataset.info);
  return {{n, name: d.name, sub: d.title + ' · ' + d.dept,
          low: (d.name + ' ' + d.title + ' ' + d.dept).toLowerCase()}};
}});
let items = [], sel = -1;
const clearHits = () =>
  document.querySelectorAll('.onode.hit').forEach(x => x.classList.remove('hit'));
const closeSugg = () => {{ sugg.style.display = 'none'; items = []; sel = -1; }};
const paint = () => sugg.querySelectorAll('.sg[data-i]').forEach(el =>
  el.classList.toggle('active', +el.dataset.i === sel));
const choose = it => {{
  q.value = it.name; closeSugg(); clearHits(); hide();
  for (let li = it.n.closest('li'); li; li = li.parentElement.closest('li')) {{
    li.classList.remove('closed'); setPill(li);
  }}
  it.n.classList.add('hit');
  const nr = it.n.getBoundingClientRect(), wr = wrap.getBoundingClientRect();
  wrap.scrollTo({{
    left: wrap.scrollLeft + (nr.left + nr.width / 2) - (wr.left + wr.width / 2),
    top: wrap.scrollTop + (nr.top + nr.height / 2) - (wr.top + wr.height / 2),
    behavior: 'smooth'}});
}};
const renderSugg = () => {{
  const v = q.value.trim().toLowerCase();
  if (!v) {{ closeSugg(); clearHits(); return; }}
  items = idx.filter(x => x.low.includes(v)).slice(0, 7);
  if (!items.length) {{
    sugg.innerHTML = '<div class="sg none">No one matches</div>';
    sugg.style.display = 'block'; sel = -1; return;
  }}
  sel = 0;
  sugg.innerHTML = items.map((x, i) =>
    `<div class="sg" data-i="${{i}}"><span class="sn">${{x.name}}</span>` +
    `<span class="sm">${{x.sub}}</span></div>`).join('');
  sugg.style.display = 'block'; paint();
  sugg.querySelectorAll('.sg[data-i]').forEach(el => {{
    el.addEventListener('mousedown', e => {{
      e.preventDefault(); choose(items[+el.dataset.i]); }});
    el.addEventListener('mouseenter', () => {{ sel = +el.dataset.i; paint(); }});
  }});
}};
q.addEventListener('input', renderSugg);
q.addEventListener('focus', renderSugg);
q.addEventListener('blur', () => setTimeout(closeSugg, 120));
q.addEventListener('keydown', e => {{
  if (e.key === 'ArrowDown' && items.length) {{
    e.preventDefault(); sel = (sel + 1) % items.length; paint();
  }} else if (e.key === 'ArrowUp' && items.length) {{
    e.preventDefault(); sel = (sel - 1 + items.length) % items.length; paint();
  }} else if (e.key === 'Enter' && sel >= 0 && items[sel]) {{
    e.preventDefault(); choose(items[sel]);
  }} else if (e.key === 'Escape') {{ closeSugg(); q.blur(); }}
}});
</script></body></html>"""


def _org_chart_tab() -> None:
    import streamlit.components.v1 as components

    with session_scope() as session:
        at = clock.now(session)
        people = session.query(Person).order_by(Person.name).all()
        dept_map = {d.id: d.name for d in session.query(Department).all()}
        by_id = {p.id: p for p in people}
        away_ids = {p.id for p in people if is_out_of_office(p, at)}
        children_map: dict[int | None, list[Person]] = {}
        for p in people:
            children_map.setdefault(p.manager_id, []).append(p)

        pal = _org_palette(__import__("atlas.ui.theme", fromlist=["is_dark"]).is_dark())
        status_map, info_map = {}, {}
        for p in people:
            status = _org_status(p, p.id in away_ids, at)
            status_map[p.id] = status
            grouped = responsibilities_of(session, p.id)
            resp = [
                [role.capitalize(), ", ".join(pr.name for pr in procs[:3])]
                for role, procs in grouped.items() if procs
            ][:4]
            info_map[p.id] = {
                "name": p.name, "title": p.title,
                "dept": dept_map.get(p.department_id, "Executive"),
                "email": p.email,
                "manager": by_id[p.manager_id].name if p.manager_id else "—",
                "status": status[1], "dotColor": pal[status[0]],
                "leave": {
                    "reason": _LEAVE_REASONS[p.id % len(_LEAVE_REASONS)],
                    "back": clock.fmt(p.ooo_until, with_time=False)
                            if p.ooo_until else "soon",
                } if status[0] == "leave" else None,
                "resp": resp,
            }

        ctx = {"children": children_map, "dept": dept_map,
               "status": status_map, "info": info_map}
        roots = children_map.get(None, [])
        branches = "".join(_org_branch(r, ctx, None) for r in roots)
    components.html(_org_doc(branches), height=620)


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
            marker={"size": 11, "color": PALETTE["green_700"], "line": {"width": 1.5, "color": _ring()}},
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
            marker={"size": 15, "color": PALETTE["gold_500"], "line": {"width": 1.5, "color": _ring()}},
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
            font={"size": 11, "color": _chart_ui()["ink"],
                  "family": "Instrument Sans, sans-serif"},
            bgcolor="rgba(18,34,26,0.92)" if theme.is_dark() else "rgba(255,253,246,0.92)",
            bordercolor=_chart_ui()["border"],
            borderwidth=1,
            borderpad=3,
        )

    u = _chart_ui()
    figure.update_layout(
        showlegend=True,
        font={"color": u["ink"], "size": 12,
              "family": "Instrument Sans, sans-serif"},
        legend={"orientation": "h", "y": -0.04,
                "font": {"color": u["muted"], "size": 11,
                         "family": "Instrument Sans, sans-serif"}},
        hoverlabel={"bgcolor": u["surface"], "bordercolor": u["border"],
                    "font": {"color": u["ink"], "size": 12,
                             "family": "Instrument Sans, sans-serif"}},
        height=620,
        margin={"l": 10, "r": 10, "t": 10, "b": 10},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis={"visible": False, "range": [-1.95, 1.95]},
        yaxis={"visible": False, "range": [-1.18, 1.18]},
    )
    return figure


# --- page -------------------------------------------------------------------


def render(actor_id: int) -> None:
    if st.session_state.get(PERSON_KEY):
        _person_profile(st.session_state[PERSON_KEY])
        return
    if st.session_state.get(PROCESS_KEY):
        _process_profile(st.session_state[PROCESS_KEY])
        return

    page_header("People", "Who owns the work")

    tab_org, tab_people, tab_processes, tab_graph = st.tabs(
        ["Org chart", "People", "Processes", "Responsibility graph"])

    with tab_org:
        _org_chart_tab()

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
            if action.button("Open", icon=":material/arrow_forward:",
                             key=f"person_{row['id']}", width="stretch"):
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
            if action.button("Open", icon=":material/arrow_forward:",
                             key=f"process_{row['id']}", width="stretch"):
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
