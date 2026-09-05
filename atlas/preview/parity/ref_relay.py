import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent))
from atlas.matching import split_relay, matchable_text

SENTENCES = [
 "Can you send an email to whoever is reposible for Data and ask them to to give me access to it if possible",
 "Can you send an email to whoever is responsible for Data and ask them to give me access to it if possible",
 "Email whoever owns the data room and ask them for access",
 "Ask whoever approves expenses to sign off my claim",
 "ask whoever is accountible for expenses to approve my claim",
 "email the person responsible for travel and ask them to book my flights",
 "email whoever handels travel and ask them to book my flights",
 "ask Layla for data room access",
 "send a message to whoever is in charge of purchase orders asking them to approve mine",
 "please chase whoever handles valuations and ask them to sign off Q3",
 "contact whoever owns IT and ask them to reset my password",
 "I need access to the data room for Project Falcon",
 "who is responsible for invoice approval?",
 "tell me about Layla Mansour",
 "can you get me access to the data room",
 "help",
]
out = []
for s in SENTENCES:
    subject, ask = split_relay(s)
    out.append({"s": s, "subject": subject, "ask": ask, "query": matchable_text(s)})
print(json.dumps(out, ensure_ascii=False))
