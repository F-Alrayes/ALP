import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent))
from atlas.seed import seed
from atlas import agent, analytics as A
from atlas.db import session_scope
seed(); agent.run_until_settled()
with session_scope() as s:
    h = A.headline(s)
    print(json.dumps({
      "headline": {k: (round(v,3) if isinstance(v,float) else v) for k,v in h.items()},
      "by_status": A.by_status(s),
      "turnaround": A.turnaround_by_department(s),
      "orphans": A.orphan_processes(s),
      "spof": [{"person": r.person, "owns": r.owns, "approves": r.approves,
                "uncovered": r.uncovered, "open_load": r.open_load} for r in A.single_points_of_failure(s, 2)],
      "bottlenecks": [{k: v for k, v in b.items() if k != "avg_wait_hours"} for b in A.bottlenecks(s)],
    }, ensure_ascii=False))
