"""B1-T4 privacy test. Runs the publish script on fake records (no Airtable token, no network)
and proves no private field reaches listings.json. Run: python3 tests/test_privacy.py"""
import importlib.util, json, os, sys, tempfile, shutil
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location("sync", os.path.join(ROOT, "scripts", "sync_listings.py"))
sync = importlib.util.module_from_spec(spec); spec.loader.exec_module(sync)

PRIVATE = {"Personal Email": "secret.person@example.com", "Personal Phone": "4045550199",
           "Member Number": "MBR-778899", "Business Street Address": "123 Hidden St",
           "Review Key": "KEYKEYKEYKEYKEYKEY", "Vouched By (name)": "Hidden Voucher", "Notes": "private note"}
def rec(i, tier, biz):
    f = {"First Name": "Fake", "Last Name": f"Person{i}", "Status": "Active", "Primary Organization": "AEAONMS",
         "City": "Covington", "State": "GA", "Occupation Title": "Electrician", "Listing Tier": tier,
         "Has Business": biz, "Business Name": "Fake Biz" if biz else "", "Business Phone": "4045550100",
         "Business Email": "biz@example.com", "Payment Status": "Charter (free)"}
    f.update(PRIVATE)  # pretend Airtable sent private fields too
    return {"id": f"recFAKE00000000{i:02d}"[:17], "fields": f}

tmp = tempfile.mkdtemp()
sync.OUT = os.path.join(tmp, "listings.json"); sync.IMG = os.path.join(tmp, "img"); sync.SAMPLES = "/nonexistent"
sync.fetch_active = lambda: [rec(1, "Member Listing ($25/yr)", False), rec(2, "Business Listing ($75/yr)", True),
                             rec(3, "Featured Business Listing ($99/yr)", True)]
sync.main()
out = open(sync.OUT).read()
leaks = [k for k, v in PRIVATE.items() if v in out]
data = json.load(open(sync.OUT))
member = [l for l in data["listings"] if l["tier"] == "Member"][0]
ok = not leaks and not member["phone"] and not member["email"]
print("private values found in output:", leaks or "none")
print("member listing business phone/email empty:", not member["phone"] and not member["email"])
print("keys:", sorted(data["listings"][0].keys()))
# Guard test: an extra key must stop the publish.
try:
    sync.check_listings([{"id": "recX", "tier": "Member", "memberNumber": "1"}]); guard = False
except SystemExit as e:
    guard = "PRIVACY STOP" in str(e)
print("guard stops unexpected key:", guard)
shutil.rmtree(tmp)
sys.exit(0 if ok and guard else 1)
