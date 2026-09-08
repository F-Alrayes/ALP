import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent))
from atlas.db import session_scope
from atlas.matching import match_departments

QUESTIONS = [
 "who do i need to contact to get my laptop fixed",
 "my screen is broken",
 "who should i speak to about my pension",
 "i need someone to look at a contract",
 "who handles payroll",
 "where do i get a parking permit",
 "i want to book a meeting room",
 "who do i talk to about the data room",
 "my wifi keeps dropping",
 "who can help me with a visa for a work trip",
 "i think i got a phishing email",
 "who approves a new hire",
 "my chair is broken",
 "who do i ask about training courses",
 "i need a second monitor",
 "how do i claim back a taxi",
 "who owns invoice approval",
 "where is the coffee machine",
 "i need to renew an NDA",
 "my printer wont print",
 "who do i contact about a sanctions check",
 "my vpn keeps disconnecting",
 "who sorts out the fire drill",
 "i need a corporate card",
]
out = []
with session_scope() as s:
    for q in QUESTIONS:
        rows = match_departments(s, q, limit=3)
        out.append({"q": q, "top": [{"dept": c.department_name, "conf": c.confidence,
                                     "kw": c.matched_keywords, "who": c.person_name,
                                     "reason": c.reason} for c in rows]})
print(json.dumps(out, ensure_ascii=False))
