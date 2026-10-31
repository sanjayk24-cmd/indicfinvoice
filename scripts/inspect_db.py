import json
import sys

with open("indicfinvoice_indic/mockbank/db.json", "r", encoding="utf-8") as f:
    db = json.load(f)

print(f"Total customers: {len(db)}")
for k, v in db.items():
    prof = v.get("profile", {})
    accts = list(v.get("accounts", {}).keys())
    loans = list(v.get("loans", {}).keys())
    claims = list(v.get("claims", {}).keys())
    txns = len(v.get("transactions", {}))
    print(f"{k}: {prof.get('name')} | scenario: {prof.get('scenario')} | accts: {accts} | loans: {loans} | claims: {claims} | txns: {txns}")
