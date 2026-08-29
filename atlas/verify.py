"""Walk the acceptance checklist headlessly.

    python verify.py

Reseeds the database, drives a request through match -> route -> chase ->
escalation -> completion, and checks every claim the brief asks for. Prints a
PASS/FAIL line per check and exits non-zero if anything fails. Leaves the
database freshly seeded, so it is safe to run right before a demo.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from atlas import agent, clock
from atlas.db import session_scope, write_lock
from atlas.matching import match_processes
from atlas.models import Event, Person, Process, Request
from atlas.routing import resolve
from atlas.seed import seed
from atlas.services import (acknowledge, complete, create_request, draft_body,
                            find_similar_open_requests, inbox_for, requests_by, timeline)

FAILS = []
def check(label, cond, extra=""):
    print(("  PASS  " if cond else "  FAIL  ") + label + (f"   {extra}" if extra else ""))
    if not cond:
        FAILS.append(label)

print("\n[1] Fresh setup -> seeded database")
seed()
with session_scope() as s:
    check("40 people seeded", s.query(Person).count() == 40)
    check("8 processes seeded", s.query(Process).count() == 8)
    check("historical requests present", 15 <= s.query(Request).count() <= 20,
          f"count={s.query(Request).count()}")
    check("mixed states", len({r.status for r in s.query(Request).all()}) >= 3)
agent.run_until_settled()

print("\n[2] Data room request -> matches, detects OOO, routes to delegate, explains")
Q = "I need access to the data room for Project Falcon"
with session_scope() as s:
    m = match_processes(s, Q)[0]
    check("matched Data Room Access", m.process_name == "Data Room Access", f"{m.confidence}%")
    check("confidence is high", m.confidence >= 70)
    check("shows matched keywords", bool(m.matched_keywords), str(m.matched_keywords[:3]))
    p = s.get(Process, m.process_id)
    r = resolve(s, p)
    check("owner is OOO and detected", r.rerouted and r.owner_name == "Layla Mansour")
    check("routed to the delegate", r.assignee_role == "delegate" and r.assignee_name == "James Okonkwo")
    check("reasoning is explained", any("out of office" in st.detail for st in r.steps))
    requester = s.query(Person).filter_by(name="Noura Al-Sabah").one()
    rid_holder = create_request(s, requester_id=requester.id, process_id=p.id,
                                assignee_id=r.assignee_id,
                                title="Data room access for Project Falcon",
                                body=draft_body(requester, p, r, Q), resolution=r)
    RID = rid_holder.id
    DELEGATE_ID = r.assignee_id
    REQUESTER_ID = requester.id

print("\n[3] Pending request lands in the delegate's inbox")
with session_scope() as s:
    ids = [x.id for x in inbox_for(s, DELEGATE_ID)]
    check("request in delegate inbox", RID in ids)
    check("status is pending", s.get(Request, RID).status == "pending")

print("\n[3b] Dedup: a near-identical second request is flagged")
with session_scope() as s:
    dupes = find_similar_open_requests(s, process_id=s.get(Request, RID).process_id,
                                       requester_id=REQUESTER_ID,
                                       title="Data room access for Project Falcon")
    check("duplicate detected", any(d.request.id == RID for d in dupes),
          f"{[(d.request.id, d.similarity) for d in dupes]}")

print("\n[4] +48h -> chase; advancing again -> escalation to a manager")
clock.advance(48); agent.run_until_settled()
with session_scope() as s:
    req = s.get(Request, RID)
    evs = [e.type for e in timeline(s, RID)]
    check("chase fired after +48h", req.chase_count == 1 and "chase" in evs)
for _ in range(4):
    clock.advance(24); agent.run_until_settled()
with session_scope() as s:
    req = s.get(Request, RID)
    evs = timeline(s, RID)
    types = [e.type for e in evs]
    check("escalated to a manager", req.status == "escalated" and "escalation" in types)
    mgr = s.get(Person, req.assignee_id)
    check("assignee is now a manager", mgr.name == "Faisal Al-Otaibi", mgr.name)
    agent_actions = [e for e in evs if e.actor == "atlas-agent"]
    check("agent actions on the request timeline", len(agent_actions) >= 3,
          f"{len(agent_actions)} entries")
    log = s.query(Event).filter(Event.actor == "atlas-agent").count()
    check("agent log is populated", log >= 3, f"{log} entries")

print("\n[5] Assignee can acknowledge and complete; requester sees the timeline")
with write_lock, session_scope() as s:
    acknowledge(s, RID, s.get(Request, RID).assignee_id)
with session_scope() as s:
    check("acknowledged", s.get(Request, RID).status == "acknowledged")
with write_lock, session_scope() as s:
    complete(s, RID, s.get(Request, RID).assignee_id, "Access granted to the Falcon room.")
with session_scope() as s:
    req = s.get(Request, RID)
    check("completed", req.status == "completed" and req.completed_at is not None)
    mine = [x.id for x in requests_by(s, REQUESTER_ID)]
    check("visible in the requester's view", RID in mine)
    tl = timeline(s, RID)
    check("full timeline preserved", len(tl) >= 10, f"{len(tl)} events")
    check("timeline ends with completion", tl[-1].type == "completed")

print("\n[6] Dashboard inputs are non-empty")
from atlas import analytics
with session_scope() as s:
    check("status chart has data", sum(r["count"] for r in analytics.by_status(s)) > 0)
    check("department turnaround has data", len(analytics.turnaround_by_department(s)) > 0)
    orph = analytics.orphan_processes(s)
    check("orphan report non-empty", len(orph) == 2, str([o["process"] for o in orph]))
    spof = analytics.single_points_of_failure(s, threshold=2)
    check("SPOF report non-empty", len(spof) > 0, f"top={spof[0].person} owns={spof[0].owns} approves={spof[0].approves}")
    check("someone owns/approves 4+", any(r.owns + r.approves >= 4 for r in spof))
    check("escalation rate > 0", analytics.headline(s)["escalation_rate"] > 0)
    check("bottlenecks computed", len(analytics.bottlenecks(s)) > 0)
    g = analytics.responsibility_graph(s)
    check("graph has nodes and edges", len(g["nodes"]) > 20 and len(g["edges"]) > 20)

print("\n[7] OOO toggle triggers an immediate reroute")
from atlas.services import set_ooo
from datetime import timedelta
seed(); agent.run_until_settled()
with session_scope() as s:
    p = s.query(Process).filter_by(name="Invoice Approval").one()
    r = resolve(s, p)
    requester = s.query(Person).filter_by(name="Anna Sorenson").one()
    req = create_request(s, requester_id=requester.id, process_id=p.id, assignee_id=r.assignee_id,
                         title="Invoice 99001 needs approval", body="Please approve.", resolution=r)
    RID2, OWNER_ID = req.id, r.assignee_id
    owner_name = r.assignee_name
with session_scope() as s:
    until = clock.now(s) + timedelta(days=5)
set_ooo(OWNER_ID, True, until)
n = agent.run_until_settled()
with session_scope() as s:
    req = s.get(Request, RID2)
    new = s.get(Person, req.assignee_id)
    types = [e.type for e in timeline(s, RID2)]
    check("rerouted on OOO toggle", req.assignee_id != OWNER_ID, f"{owner_name} -> {new.name}")
    check("reroute logged with a reason", "reroute_ooo" in types)

print("\n[8] No network access at runtime")
import socket
blocked = []
orig = socket.socket.connect
def guard(self, addr):
    blocked.append(addr)
    raise AssertionError(f"network call attempted to {addr}")
socket.socket.connect = guard
try:
    seed()
    agent.run_until_settled()
    with session_scope() as s:
        match_processes(s, "kyc refresh for a new investor")
        analytics.headline(s)
    check("no outbound sockets opened", not blocked)
finally:
    socket.socket.connect = orig

print("\n" + "=" * 62)
print("FAILED:", FAILS if FAILS else "none — all acceptance checks passed")
sys.exit(1 if FAILS else 0)
