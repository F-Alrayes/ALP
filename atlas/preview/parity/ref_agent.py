import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent))
from atlas.seed import seed
from atlas import agent, clock
from atlas.db import session_scope
from atlas.models import Person, Process, Request, Event
from atlas.matching import match_processes
from atlas.routing import resolve
from atlas.services import create_request, draft_body, acknowledge, complete, timeline

seed()
steps = []
def snapshot(label, actions, rid):
    with session_scope() as s:
        r = s.get(Request, rid) if rid else None
        ev = [(e.type, e.actor) for e in timeline(s, rid)] if rid else []
        steps.append({"label": label, "actions": actions,
                      "status": r.status if r else None,
                      "assignee": s.get(Person, r.assignee_id).name if r and r.assignee_id else None,
                      "chases": r.chase_count if r else None,
                      "events": ev,
                      "agent_events_total": s.query(Event).filter(Event.actor=="atlas-agent").count()})

snapshot("seed+settle", agent.run_until_settled(), None)

Q = "I need access to the data room for Project Falcon"
with session_scope() as s:
    m = match_processes(s, Q, 3)[0]
    p = s.get(Process, m.process_id)
    r = resolve(s, p)
    requester = s.query(Person).filter_by(name="Noura Al-Sabah").one()
    req = create_request(s, requester_id=requester.id, process_id=p.id, assignee_id=r.assignee_id,
                         title="Data room access for Project Falcon",
                         body=draft_body(requester, p, r, Q), resolution=r)
    RID = req.id
snapshot("created", 0, RID)

for hours in [48, 24, 24, 24, 24]:
    clock.advance(hours)
    snapshot(f"+{hours}h", agent.run_until_settled(), RID)

with session_scope() as s:
    acknowledge(s, RID, s.get(Request, RID).assignee_id)
snapshot("acknowledge", 0, RID)
with session_scope() as s:
    complete(s, RID, s.get(Request, RID).assignee_id, "Access granted.")
snapshot("complete", 0, RID)

print(json.dumps(steps, ensure_ascii=False))
