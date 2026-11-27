"""Admin Elite switch (Nov 27, 2026): 'Elite (admin)' checkbox gives the Elite look without changing tier fees.
Run: python3 tests/test_elite.py
"""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import sync_listings as s
s.save_image = lambda *a, **k: ""
base = {"Status": "Active", "Primary Organization": "aeaonms", "Payment Status": "Charter (free)", "Last Name": "Test"}
def L(rid, **f): return s.to_listing({"id": rid, "fields": {**base, **f}}, set())
m_elite = L("recA", **{"First Name": "MemberElite", "Listing Tier": "Member Listing ($25/yr)", "Elite (admin)": True,
                       "Business Name": "SHOULD NOT SHOW", "Business Phone": "555", "Has Business": False})
m_plain = L("recB", **{"First Name": "MemberPlain", "Listing Tier": "Member Listing ($25/yr)"})
b_elite = L("recC", **{"First Name": "BizElite", "Listing Tier": "Business Listing ($50/yr founding rate)", "Has Business": True,
                       "Business Name": "Biz", "Elite (admin)": True})
b_plain = L("recD", **{"First Name": "BizPlain", "Listing Tier": "Business Listing ($50/yr founding rate)", "Has Business": True, "Business Name": "Biz2"})
s.check_listings([m_elite, m_plain, b_elite, b_plain])
checks = {
    "member + Elite: elite look, still Member tier": m_elite["elite"] and m_elite["tier"] == "Member",
    "member + Elite: no business contact published": not any(m_elite.get(k) for k in s.BUSINESS_ONLY_KEYS),
    "plain member: not elite": not m_plain["elite"],
    "business + Elite: Business Elite": b_elite["elite"] and b_elite["tier"] == "Featured",
    "plain business: not elite": not b_plain["elite"] and b_plain["tier"] == "Business",
}
order = sorted([b_plain, m_plain, m_elite, b_elite], key=lambda l: (not l["elite"], l["tier"] == "Member", l["last"].lower(), l["first"]))
checks["elite listed first"] = [l["first"] for l in order][:2] == ["BizElite", "MemberElite"] or {l["first"] for l in order[:2]} == {"BizElite", "MemberElite"}
for k, v in checks.items(): print(("ok  " if v else "FAIL") + " " + k)
sys.exit(0 if all(checks.values()) else 1)
