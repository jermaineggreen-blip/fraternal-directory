"""Spec B5-T3: image handling test (no network, no real data).

Runs the real publish main() in a temp folder with a fake Airtable result:
- a held/removed member's old photo (orphan) must be deleted,
- an Active member's photo is kept and its name is the same on every run,
- non-member files in img/ (e.g. site art) are never touched,
- dues card data never reaches listings.json or img/.
Run: python3 tests/test_images.py
"""
import json, os, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import sync_listings as s

tmp = tempfile.mkdtemp()
s.IMG = os.path.join(tmp, "img"); s.OUT = os.path.join(tmp, "listings.json"); s.SAMPLES = "/nonexistent"
os.makedirs(s.IMG)
orphan = "recHELDMEMBER0001-photo-deadbeef.jpg"
site_art = "seal.png"
for n in (orphan, site_art):
    open(os.path.join(s.IMG, n), "w").write("x")

DUES_ID = "1DuesCardDriveFileIdShouldNeverAppear"
def fake_fetch():
    return [{"id": "recACTIVEMEMBER01", "fields": {
        "First Name": "Img", "Last Name": "Test", "Status": "Active", "Primary Organization": "aeaonms",
        "Listing Tier": "Member Listing ($25/yr)", "Payment Status": "Charter (free)",
        "Member Photo": [{"id": "attPHOTO123", "type": "image/jpeg", "url": "https://example.invalid/p.jpg"}],
        "Dues Card File ID": DUES_ID, "Dues Card": "Uploaded – pending review"}}]
downloads = []
def fake_get(url, path):
    downloads.append(url); open(path, "w").write("img")
s.fetch_active = fake_fetch
s.urllib.request.urlretrieve = fake_get

s.main()
first = sorted(os.listdir(s.IMG))
s.main()  # second run: same names, no new download
second = sorted(os.listdir(s.IMG))
blob = open(s.OUT).read() + " ".join(second)
checks = {
    "orphan deleted": orphan not in second,
    "site art kept": site_art in second,
    "active photo kept": any(n.startswith("recACTIVEMEMBER01-photo-") for n in second),
    "same name every run": first == second,
    "downloaded once": len(downloads) == 1,
    "dues card never published": DUES_ID not in blob and "dues" not in blob.lower(),
}
for k, v in checks.items():
    print(("ok  " if v else "FAIL") + " " + k)
print("files:", second)
sys.exit(0 if all(checks.values()) else 1)
