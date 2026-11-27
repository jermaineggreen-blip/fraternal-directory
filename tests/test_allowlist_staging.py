"""Spec B5-T2: field allowlist diff test on STAGING data.

Two fake staging records (tests/fixtures/staging_canary.json) have every private field
filled with a marker value. They run through the real publish code twice:
  1. as the real fetch delivers them (only the fields the script asks for), and
  2. worst case: Airtable returns EVERY field.
Pass = no marker or private value in the output, only allowlisted keys, and the
Member listing carries no business contact. Also checks the live listings.json keys.
Run: python3 tests/test_allowlist_staging.py
"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import sync_listings as s

fx = json.load(open(os.path.join(ROOT, "tests", "fixtures", "staging_canary.json")))
REV = {v: k for k, v in s.F_ALIASES.items()}  # Airtable name -> script name

def as_script(fields, only_requested):
    out = {}
    for name, v in fields.items():
        key = REV.get(name, name)
        if only_requested and key not in s.F:
            continue
        out[key] = v
    return out

private = []
for r in fx["records"]:
    for name, v in r["fields"].items():
        if s.FIELD_PRIVACY.get(name) in ("Reviewer", "Never") and isinstance(v, str) and v and not v.startswith("FVD-"):
            private.append(v)
private += ["CANARY"]
ok = True
for mode in (True, False):
    keep = set()
    listings = [s.to_listing({"id": r["id"], "fields": as_script(r["fields"], mode)}, keep) for r in fx["records"]]
    s.check_listings(listings)  # exits on any key outside the allowlist
    blob = json.dumps(listings)
    leaks = [p for p in private if p in blob]
    biz_on_member = [k for l in listings if l["tier"] == "Member" for k in s.BUSINESS_ONLY_KEYS if l.get(k)]
    extra = set().union(*map(set, listings)) - s.ALLOWED_KEYS
    label = "real fetch" if mode else "worst case (all fields)"
    print(f"{label}: {len(listings)} listings, leaks={leaks}, extra keys={sorted(extra)}, business data on Member={biz_on_member}")
    ok &= not leaks and not extra and not biz_on_member
    print("  tiers:", [(l["first"], l["tier"], l["chapter"], l["referral"], l["officer"]) for l in listings])

live = json.load(open(os.path.join(ROOT, "listings.json")))
real = [l for l in live["listings"] if not l.get("sample")]
live_extra = set().union(*map(set, real)) - s.ALLOWED_KEYS if real else set()
print(f"live listings.json: {len(real)} real listings, keys outside allowlist={sorted(live_extra)}")
ok &= not live_extra
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
