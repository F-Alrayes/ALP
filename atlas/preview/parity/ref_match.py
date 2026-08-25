import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent))
from atlas.db import session_scope
from atlas.matching import match_processes

QUERIES = [
 "I need access to the data room for Project Falcon",
 "can someone approve invoice 88412 from Meridian",
 "I am locked out of my account and cannot log in",
 "we need to renew the Bloomberg contract before it expires",
 "need to book flights to London next week",
 "kyc refresh for Northgate",
 "reimburse me for the client dinner receipts",
 "please onboard a new supplier for facilities",
 "I need the quarterly NAV marks signed off",
 "raise a purchase order for new laptops",
 "where is the coffee machine",
 "NDA for the vendor diligence team",
 "board pack for the April committee",
 "grant Sofia read access to the shared drive",
 "my password expired and MFA is broken",
 "expense claim for mileage",
 "policy exception waiver for the trading limit",
 "vendor bank details need verifying",
 "travel visa for the Manama trip",
 "who approves the quarterly valuation",
 "i need a laptop",
 "urgent: data room access for cedarline",
 "renew msa",
 "sanctions screening on a new investor",
]
out = []
with session_scope() as s:
    for q in QUERIES:
        ms = match_processes(s, q, limit=3)
        out.append({"q": q, "top": [{"name": m.process_name, "conf": m.confidence,
                                     "kw": m.matched_keywords,
                                     "sig": m.signals} for m in ms]})
print(json.dumps(out, ensure_ascii=False))
