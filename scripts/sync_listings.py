#!/usr/bin/env python3
"""Publish approved FVD members to listings.json.

Reads the Airtable Members table and writes every record whose Status is
"Active" to listings.json for the public directory. Photos are copied into
img/ because Airtable attachment links expire after a few hours.

Never publishes personal email, personal phone, member numbers or addresses.
Needs env AIRTABLE_TOKEN (read-only personal access token for the FVD base).
"""
import json, os, re, sys, urllib.request, urllib.parse, urllib.error, datetime, hashlib

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
    "oes": "Order of the Eastern Star (Prince Hall)",
    "doi": "Daughters of AEAONMS of North and South America and Its Jurisdictions, Inc.",
    "other": "Other Fraternal Organization",
    # Divine Nine: published BY NAME ONLY (text). No emblems anywhere until each approves
    # emblem use in writing or becomes a partner.
    "apa": "Alpha Phi Alpha Fraternity, Inc.", "aka": "Alpha Kappa Alpha Sorority, Inc.",
    "kap": "Kappa Alpha Psi Fraternity, Inc.", "opp": "Omega Psi Phi Fraternity, Inc.",
    "dst": "Delta Sigma Theta Sorority, Inc.", "pbs": "Phi Beta Sigma Fraternity, Inc.",
    "zpb": "Zeta Phi Beta Sorority, Inc.", "sgr": "Sigma Gamma Rho Sorority, Inc.",
    "ipt": "Iota Phi Theta Fraternity, Inc.",
}
# Airtable field IDs (stable even if a column is renamed).
F = {
    "First Name": "fldiUgs2ExnPGS2xG", "Last Name": "fld6JtXIhdTuTvCRL",
    "Status": "fldMyEAIigFjCZSLm", "Primary Organization": "fldLmSC9ojsM6hjsF",
    "Chapter": "fldvaRF8yEuRCkwrw", "Additional Organizations": "flda5RjPfT4d1VYnR",
    "City": "fldnGD4m5tQKLUGdh", "State": "fldO2kLS9anDkecc8",
    "Occupation Category": "fldM0CzMwmWJkgi0W", "Occupation Title": "fldX4XFdYbR8rL8QC",
    "Years in Field": "fldwGdb44DYlE1B5c", "Professional Bio": "fldG0Vq2C3rl5KWnd",
    "Has Business": "fldoRATSNpxyAkiRz", "Is Mobile Business": "fldcpIrukntho9BPY",
    "Business Name": "flddCeIU5jDHgCsEJ", "Business Phone": "fld4oG8uermmFBlbP",
    "Business Email": "fld1KsSB2IiiOxooR", "Business City": "fldAo69YHXo9H1wO0",
    "Business State": "fldr4Chpn4DAlhLGE", "Website": "fld1goJEotOelD7Q1",
    "Member Photo": "fldQpsc4aSS0w80CW", "Business Logo": "fldKJcz2zbCnbBrZ9",
    "Business Photo": "fld7Of5kfSTqytpPk", "Available For": "fldXzR0M9qHZ8LKZE",
    "Listing Tier": "fldTWlHv31fX4zh16", "Payment Status": "fldkbDxdCWAgZqGCE",
    "Verification Method": "fld1cRo2FN3oMEkfP",
    "Secretary Answer": "fldxAtHn4XZnzl9Tq",
}
ID2NAME = {v: k for k, v in F.items()}

# Spec B1-T4: privacy label for EVERY Members field (updated Nov 26, 2026).
#   Public   = may appear on the public directory.
#   Logic    = read only to decide what to show (never copied into listings.json).
#   Reviewer = Jermaine/reviewers only (Airtable, review emails). Never published.
#   Never    = must never leave Airtable/Drive (IDs, keys, numbers, dues cards).
# Business Phone/Email/Website publish ONLY for Business and Business Elite listings (paid perk, F6).
FIELD_PRIVACY = {
    "First Name": "Public", "Last Name": "Public", "Primary Organization": "Public",
    "Chapter / Temple / Lodge / Court": "Public", "Additional Organizations": "Public",
    "City": "Public", "State": "Public", "Occupation Category": "Public", "Occupation Title": "Public",
    "Years in Field": "Public", "Professional Bio": "Public", "Available For": "Public",
    "Member Photo": "Public", "Business Name": "Public", "Business Phone": "Public",
    "Business Email": "Public", "Business City": "Public", "Business State": "Public",
    "Website": "Public", "Business Logo": "Public", "Business Photo": "Public",
    "Is Mobile Business": "Public",
    "Status": "Logic", "Listing Tier": "Logic", "Has Business": "Logic",
    "Payment Status": "Logic", "Verification Method": "Logic", "Secretary Answer": "Logic",
    "Secretary Reason": "Reviewer",
    "Personal Email": "Reviewer", "Personal Phone": "Reviewer", "Notes": "Reviewer",
    "Assignee": "Reviewer", "Urgent Availability": "Reviewer", "Last Verified Date": "Reviewer",
    "Business Street Address": "Reviewer", "Business ZIP": "Reviewer", "Divide Contribution": "Reviewer",
    "Submission Date": "Reviewer", "Member # (Last 4)": "Reviewer", "Annual Fee": "Reviewer",
    "Renewal Date": "Reviewer", "Verified By": "Reviewer", "Paid Date": "Reviewer",
    "Org Contribution (15%)": "Reviewer", "Contribution Period (half-year)": "Reviewer",
    "Contribution Paid Out": "Reviewer", "Two-Way Reviews": "Reviewer", "Marks Attestation": "Reviewer",
    "Dues Card": "Reviewer", "Dues Card Deleted On": "Reviewer", "Vouch Status": "Reviewer",
    "Vouched By (name)": "Reviewer", "Vouch Requested On": "Reviewer", "Vouch Answered On": "Reviewer",
    "Vouching Revoked": "Reviewer", "Vouch Reminder Sent": "Reviewer", "Status Reason": "Reviewer",
    "Status Changed": "Reviewer", "FVD-ID": "Reviewer", "FVD Seq": "Reviewer",
    "Years in Field (old number)": "Reviewer",
    "Member Number": "Never", "Review Key": "Never", "Vouch Key": "Never",
    "Vouched By (record ID)": "Never", "Dues Card File ID": "Never",
    "Attachments": "Never", "Attachment Summary": "Never",
}
# Script field names that differ from the Airtable column name.
F_ALIASES = {"Chapter": "Chapter / Temple / Lodge / Court"}
# The only keys allowed in a published listing.
ALLOWED_KEYS = {"id", "first", "last", "org", "orgs", "chapter", "category", "title", "years", "city", "state",
                "tier", "bio", "available", "photo", "verified", "referral", "officer", "charter",
                "business", "phone", "email", "website", "mobile", "logo", "bizPhoto"}
BUSINESS_ONLY_KEYS = ("business", "phone", "email", "website", "logo", "bizPhoto")


def check_field_list():
    """Fail if the script ever reads a field that is not Public or Logic."""
    bad = [n for n in F if FIELD_PRIVACY.get(F_ALIASES.get(n, n)) not in ("Public", "Logic")]
    if bad:
        sys.exit("PRIVACY STOP: publish script reads non-public fields: " + ", ".join(bad))


def check_listings(listings):
    """Fail the publish if any listing carries a key outside the allowlist, or business contact on a Member listing."""
    for l in listings:
        if l.get("sample"):
            continue
        extra = set(l) - ALLOWED_KEYS
        if extra:
            sys.exit(f"PRIVACY STOP: listing {l.get('id')} has unexpected keys: {sorted(extra)}")
        if l.get("tier") == "Member" and any(l.get(k) for k in BUSINESS_ONLY_KEYS):
            sys.exit(f"PRIVACY STOP: member listing {l.get('id')} carries business contact data")
HIDDEN_ORGS = set()  # add a code here to hide an organization again


def api(url):
    token = os.environ.get("AIRTABLE_TOKEN", "").strip().strip('"').strip("'")
    if token.lower().startswith("bearer "):
        token = token[7:].strip()
    if not token.startswith("pat"):
        sys.exit("AIRTABLE_TOKEN is missing or not an Airtable personal access token (should start with 'pat').")
    req = urllib.request.Request(url, headers={"Authorization": "Bearer " + token})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        hint = {401: "token rejected - recreate it and paste the full value",
                403: "token lacks access - give it data.records:read and add the FVD base",
                404: "base or table not found for this token - add the FVD base to the token"}.get(e.code, "")
        sys.exit(f"Airtable said {e.code}: {hint}")


def fetch_active():
    rows, offset = [], None
    while True:
        q = [("pageSize", "100"), ("returnFieldsByFieldId", "true")]
        q += [("fields[]", fid) for fid in F.values()]
        if offset:
            q.append(("offset", offset))
        data = api(f"https://api.airtable.com/v0/{BASE}/{TABLE}?" + urllib.parse.urlencode(q))
        for r in data.get("records", []):
            r["fields"] = {ID2NAME.get(k, k): v for k, v in r["fields"].items()}
            if r["fields"].get("Status") == "Active":
                rows.append(r)
        offset = data.get("offset")
        if not offset:
            return rows


def split(v):
    if not v:
        return []
    if isinstance(v, list):
        return [str(x).strip() for x in v if str(x).strip()]
    # Never split inside an official name such as "Alpha Phi Alpha Fraternity, Inc." (fixed Nov 27, 2026).
    return [p.strip() for p in re.split(r"[\n;]+|,(?!\s*Inc\.)", str(v)) if p.strip()]


HIDDEN_WORDS = ()


def org_label(code):
    code = (code or "").strip()
    if code.lower() in HIDDEN_ORGS or any(w in code.lower() for w in HIDDEN_WORDS):
        return None
    if code.lower().startswith("daughters of aeaonms"):
        return ORGS["doi"]
    for full in ORGS.values():
        if code.lower() == full.lower() or (full.endswith(" (Prince Hall)") and code.lower() == "eastern star (prince hall)"):
            return full
    return ORGS.get(code.lower(), code or None)


# Standard chapter format (Jermaine, Nov 27, 2026): "<Name> <Unit> No. <number>", e.g. "Al-Karim Temple No. 242".
UNIT_BY_ORG = {ORGS["aeaonms"]: "Temple", ORGS["pha"]: "Lodge", ORGS["oes"]: "Chapter", ORGS["doi"]: "Court"}
UNIT_WORDS = r"(temple|lodge|court|chapter|assembly|consistory|council|commandery)"
ACRONYMS = {"AEAONMS", "PHA", "OES", "USA", "II", "III", "IV"}


def _word(w):
    if w.upper() in ACRONYMS:
        return w.upper()
    if w.isupper() or w.islower():
        return w[:1].upper() + w[1:].lower()
    return w  # mixed case is kept as typed (AKHi, McDonald)


def chapter_label(raw, org):
    s = re.sub(r"\s*-\s*", "-", (raw or "").strip())
    if not s:
        return ""
    m = re.search(r"(?:#|\bno\.?|\bnumber)?\s*(\d+)\s*$", s, re.I)
    num = m.group(1) if m else ""
    name = re.sub(r"[#,]|\bno\.?$", "", s[:m.start()] if m else s, flags=re.I).strip()
    unit = ""
    um = re.search(r"\b" + UNIT_WORDS + r"$", name, re.I)
    if um:
        unit, name = um.group(1).title(), name[:um.start()].strip()
    unit = unit or UNIT_BY_ORG.get(org, "Chapter" if (org or "").endswith(", Inc.") else "")
    small = {"of", "the", "and", "de", "du", "la"}
    name = "-".join(" ".join(w.lower() if (i or j) and w.lower() in small else _word(w) for i, w in enumerate(part.split()))
                    for j, part in enumerate(name.split("-")))
    return (name + (" " + unit if unit else "") + (" No. " + num if num else "")).strip()


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
    primary = org_label(f.get("Primary Organization")) or "Other Fraternal Organization"
    orgs = [o for o in (org_label(c) for c in split(f.get("Additional Organizations"))) if o and o != primary]
    city = (f.get("Business City") if has_biz and f.get("Business City") else f.get("City")) or ""
    state = (f.get("Business State") if has_biz and f.get("Business State") else f.get("State")) or ""
    listing = {
        "id": rec["id"],
        "first": (f.get("First Name") or "").strip(),
        "last": (f.get("Last Name") or "").strip(),
        "org": primary,
        "orgs": orgs,
        "chapter": chapter_label(f.get("Chapter"), primary),
        "category": f.get("Occupation Category") or "",
        "title": f.get("Occupation Title") or "",
        "years": years,
        "city": city,
        "state": state,
        "tier": ("Featured" if featured else "Business") if has_biz else "Member",
        "bio": f.get("Professional Bio") or "",
        "available": split(f.get("Available For")),
        "photo": save_image(f.get("Member Photo"), rec["id"], "photo", keep),
        "verified": True,
        # Member vouch (Nov 22, 2026): public badge only; the voucher's identity is never published.
        "referral": f.get("Verification Method") == "Member vouch",
        # Chapter secretary confirmed membership (Nov 27, 2026). Secretary identity is never published.
        "officer": f.get("Secretary Answer") in ("In good standing", "Not current, never expelled"),
        "charter": f.get("Payment Status") == "Charter (free)",
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
    check_field_list()
    os.makedirs(IMG, exist_ok=True)
    keep = set()
    real = [to_listing(r, keep) for r in fetch_active()]
    real.sort(key=lambda l: (l["tier"] == "Member", l["last"].lower()))
    check_listings(real)
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
