"""Dump the seeded Atlas database to JSON with every timestamp expressed as
hours relative to the seed instant, so the browser preview can rehydrate it
against its own clock and stay in lockstep with the Python app."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from atlas.seed import seed
from atlas.db import session_scope, get_setting
from atlas.models import (Department, Event, Message, Person, Process,
                          Request, Responsibility)
from datetime import datetime

seed()

with session_scope() as s:
    base = datetime.fromisoformat(get_setting(s, "seeded_at"))
    def rel(dt):
        return None if dt is None else round((dt - base).total_seconds() / 3600.0, 4)

    data = {
        "departments": [{"id": d.id, "name": d.name}
                        for d in s.query(Department).order_by(Department.id).all()],
        "people": [{"id": p.id, "name": p.name, "title": p.title,
                    "department_id": p.department_id, "manager_id": p.manager_id,
                    "email": p.email, "is_ooo": p.is_ooo, "ooo_until": rel(p.ooo_until)}
                   for p in s.query(Person).order_by(Person.id).all()],
        "processes": [{"id": p.id, "name": p.name, "description": p.description,
                       "category": p.category, "keywords": p.keywords}
                      for p in s.query(Process).order_by(Process.id).all()],
        "responsibilities": [{"id": r.id, "process_id": r.process_id,
                              "person_id": r.person_id, "role": r.role}
                             for r in s.query(Responsibility).order_by(Responsibility.id).all()],
        "requests": [{"id": r.id, "requester_id": r.requester_id, "process_id": r.process_id,
                      "assignee_id": r.assignee_id, "original_assignee_id": r.original_assignee_id,
                      "title": r.title, "body": r.body, "status": r.status,
                      "created_at": rel(r.created_at), "updated_at": rel(r.updated_at),
                      "last_action_at": rel(r.last_action_at), "chase_count": r.chase_count,
                      "acknowledged_at": rel(r.acknowledged_at), "completed_at": rel(r.completed_at)}
                     for r in s.query(Request).order_by(Request.id).all()],
        "messages": [{"id": m.id, "request_id": m.request_id, "sender_id": m.sender_id,
                      "recipient_id": m.recipient_id, "type": m.type, "body": m.body,
                      "created_at": rel(m.created_at), "read": m.read}
                     for m in s.query(Message).order_by(Message.id).all()],
        "events": [{"id": e.id, "request_id": e.request_id, "type": e.type,
                    "detail": e.detail, "actor": e.actor, "created_at": rel(e.created_at)}
                   for e in s.query(Event).order_by(Event.id).all()],
        "settings": {"chase_after_hours": 48, "chase_interval_hours": 24, "max_chases": 2},
    }

out = Path(__file__).resolve().parent / "seed.json"
out.write_text(json.dumps(data, separators=(",", ":"), ensure_ascii=False))
print("wrote", out, out.stat().st_size, "bytes")
for k, v in data.items():
    print(f"  {k}: {len(v) if isinstance(v, list) else v}")
