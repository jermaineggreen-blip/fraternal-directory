"""Spec B6-T6: sample listings show only while there are fewer than 5 Active members.
Runs the real publish main() offline with 4, then 5 fake Active members.
Run: python3 tests/test_samples.py
"""
import json, os, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import sync_listings as s

tmp = tempfile.mkdtemp()
s.IMG = os.path.join(tmp, "img"); s.OUT = os.path.join(tmp, "listings.json")
os.makedirs(s.IMG)
def fake(n):
    return lambda: [{"id": "recFAKEMEMBER%05d" % i, "fields": {"First Name": "T%d" % i, "Last Name": "Test", "Status": "Active",
            "Primary Organization": "aeaonms", "Listing Tier": "Member Listing ($25/yr)", "Payment Status": "Charter (free)"}} for i in range(n)]
ok = True
for n, want_samples in ((4, True), (5, False), (11, False)):
    s.fetch_active = fake(n)
    if os.path.exists(s.OUT): os.remove(s.OUT)
    s.main()
    d = json.load(open(s.OUT))
    samples = sum(1 for l in d["listings"] if l.get("sample"))
    good = (samples > 0) == want_samples and d["demo"] == want_samples and d["real"] == n
    ok &= good
    print(("ok  " if good else "FAIL") + f" {n} Active: demo={d['demo']}, samples shown={samples}")
live = json.load(open(os.path.join(ROOT, "listings.json")))
lg = live["real"] >= 5 and not live["demo"] and not any(l.get("sample") for l in live["listings"])
ok &= lg
print(("ok  " if lg else "FAIL") + f" live listings.json: {live['real']} real, demo={live['demo']}, samples={sum(1 for l in live['listings'] if l.get('sample'))}")
sys.exit(0 if ok else 1)
