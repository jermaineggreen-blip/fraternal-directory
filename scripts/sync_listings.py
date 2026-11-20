#!/usr/bin/env python3
"""Publish approved FVD members to listings.json.

Reads the Airtable Members table and writes every record whose Status is
"Active" to listings.json for the public directory. Photos are copied into
img/ because Airtable attachment links expire after a few hours.

Never publishes personal email, personal phone, member numbers or addresses.
Needs env AIRTABLE_TOKEN (read-only personal access token for the FVD base).
"""
import json, os, re, sys, urllib.request, urllib.parse, datetime, hashlib

BASE = "appKGbm7nA88YKC7h"
TABLE = "tbl96XAeUWUjPotOd"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "listings.json")
IMG = os.path.join(ROOT, "img")
SAMPLES = os.path.join(ROOT, "scripts", "sample_listings.json")
MIN_REAL_BEFORE_SAMPLES_HIDE = 5

ORGS = {
    "aeaonms": "AEAONMS",
    "pha": "Prince Hall Masons (F&AM)",
    "oes": "Eastern Star (Prince Hall)",
    "doi": "Daughters of AEAONMS of North and South America and Its Jurisdictions, Inc.",
    "other": "Other Fraternal Organization",
    # Divine Nine stay hidden until each approves; they are never published here.
}
HIDDEN_ORGS = {"apa", "aka", "kap", "opp", "dst", "pbs", "zpb", "sgr", "ipt"}


def api(url):
    req = urllib.request.Request(url, headers={"Authorization": "Bearer " + os.environ["AIRTABLE_TOKEN"]})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def fetch_active():
    rows, offset = [], None
    formula = "{Status}='Active'"
    while True:
        q = {"filterByFormula": formula, "pageSize": "100"}
        if offset:
            q["offset"] = offset
        data = api(f"https://api.airtable.com/v0/{BASE}/{TABLE}?" + urllib.parse.urlencode(q))
        rows += data.get("records", [])
        offset = data.get("offset")
        if not offset:
            return rows


def split(v):
    if not v:
        return []
    if isinstance(v, list):
        return [str(x).strip() for x in v if str(x).strip()]
    return [p.strip() for p in re.split(r"[,\n;]+", str(v)) if p.strip()]


def org_label(code):
    code = (code or "").strip()
    if code.lower() in HIDDEN_ORGS:
        return None
    return ORGS.get(code.lower(), code or None)


def save_image(att, rec_id, kind, keep):
    if not att:
        return ""
    a = att[0]
    ext = ".png" if "png" in (a.get("type") or "") else ".jpg"
    digest = hashlib.sha1((a.get("id", "") + kind).encode()).hexdigest()[:8]
    name = f"{rec_id}-{kind}-{digest}{ext}"
    path = os.path.join(IMG, name)
    keep.add(name)
    if not os.path.exists(path):
        urllib.request.urlretrieve(a["url"], path)
    return "img/" + name


def to_listing(rec, keep):
    f = rec["fields"]
    tier_raw = f.get("Listing Tier") or ""
    has_biz = bool(f.get("Has Business")) and ("Business" in tier_raw or "Featured" in tier_raw)
    featured = "Featured" in tier_raw
    years = re.sub(r"\s*years?\s*$", "", str(f.get("Years in Field") or ""), flags=re.I)
    orgs = [o for o in (org_label(c) for c in split(f.get("Additional Organizations"))) if o]
    city = (f.get("Business City") if has_biz and f.get("Business City") else f.get("City")) or ""
    state = (f.get("Business State") if has_biz and f.get("Business State") else f.get("State")) or ""
    listing = {
        "id": rec["id"],
        "first": (f.get("First Name") or "").strip(),
        "last": (f.get("Last Name") or "").strip(),
        "org": org_label(f.get("Primary Organization")) or "Other Fraternal Organization",
        "orgs": orgs,
        "chapter": f.get("Chapter / Temple / Lodge / Court") or "",
        "category": f.get("Occupation Category") or "",
        "title": f.get("Occupation Title") or "",
        "years": years,
        "city": city,
        "state": state,
        "tier": ("Featured" if featured else "Business") if has_biz else "Member",
        "bio": f.get("Professional Bio") or "",
        "available": split(f.get("Available For")),
        "photo": save_image(f.get("Member Photo"), rec["id"], "photo", keep),
    }
    if has_biz:
        listing.update({
            "business": f.get("Business Name") or "",
            "phone": f.get("Business Phone") or "",
            "email": f.get("Business Email") or "",
            "website": f.get("Website") or "",
            "mobile": bool(f.get("Is Mobile Business")),
            "logo": save_image(f.get("Business Logo"), rec["id"], "logo", keep),
            "bizPhoto": save_image(f.get("Business Photo"), rec["id"], "biz", keep),
        })
    else:
        listing.update({"business": "", "phone": "", "email": "", "website": "", "mobile": False})
    return listing


def main():
    os.makedirs(IMG, exist_ok=True)
    keep = set()
    real = [to_listing(r, keep) for r in fetch_active()]
    real.sort(key=lambda l: (l["tier"] == "Member", l["last"].lower()))
    listings = list(real)
    demo = len(real) < MIN_REAL_BEFORE_SAMPLES_HIDE
    if demo and os.path.exists(SAMPLES):
        for s in json.load(open(SAMPLES))["listings"]:
            s["sample"] = True
            listings.append(s)
    # Remove photos of members who are no longer listed.
    for name in os.listdir(IMG):
        if name.startswith("rec") and name not in keep:
            os.remove(os.path.join(IMG, name))
    new = {"updated": datetime.date.today().isoformat(), "demo": demo, "real": len(real), "listings": listings}
    old = json.load(open(OUT)) if os.path.exists(OUT) else {}
    if {k: v for k, v in old.items() if k != "updated"} == {k: v for k, v in new.items() if k != "updated"}:
        print(f"No change ({len(real)} live members).")
        return
    json.dump(new, open(OUT, "w"), indent=1)
    print(f"Published {len(real)} live members (samples shown: {demo}).")


if __name__ == "__main__":
    main()
