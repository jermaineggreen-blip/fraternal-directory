# FVD Publishing Pipeline — Spec (B5-T1)

Written Nov 27, 2026 from the live code at this commit. Labels follow Spec v1.0 A1:
FACT (read from code or checked live today), GAP (spec asks for it, code does not do it yet; owned by a later task), UNKNOWN.

## 1. What it does

Turns Airtable Members with Status = **Active** into `listings.json` + `img/`, which the public directory reads. Nothing else ever reaches the public site.

## 2. Trigger — FACT

File: `.github/workflows/sync-listings.yml` (workflow id 425016638, "Publish approved listings").

| Trigger | Detail |
|---|---|
| Schedule | `*/30 11-22 * * *` UTC = every 30 min, 6:00 AM–5:30 PM Eastern (EST). The file comment says "6 PM"; the last run is 5:30 PM. |
| Manual | `workflow_dispatch` ("Run workflow" button in GitHub Actions, or the API). |
| Concurrency | Group `sync-listings`: two runs never overlap. |

Note: GitHub can delay or skip scheduled runs when it is busy. A delay is not a failure.

## 3. Steps — FACT

1. Check out the repo; set up Python 3.12.
2. Run `scripts/sync_listings.py` with secret `AIRTABLE_TOKEN` (GitHub Actions secret; never in code).
3. If `listings.json` or `img/` changed, commit as "FVD sync" with message "Publish approved listings" and push to `main`.
4. The push triggers GitHub Pages (`pages-build-deployment`), which deploys the site.

## 4. Query — FACT

- Base `appKGbm7nA88YKC7h`, table `tbl96XAeUWUjPotOd`, 100 records per page, all pages.
- Asks Airtable only for the field IDs listed in `F` (28 fields), by field ID, so renaming a column does not break it.
- Keeps only records whose Status is exactly `Active`. Pending, Verified, Hold, Rejected, Expired and Removed never publish.

## 5. Field allowlist (privacy) — FACT

Three guards, any of which stops the publish with "PRIVACY STOP" and leaves the live site unchanged:

1. `check_field_list()`: every field the script reads must be labeled Public or Logic in `FIELD_PRIVACY` (B1-T4).
2. `ALLOWED_KEYS`: a published listing may only carry these keys: id, first, last, org, orgs, chapter, category, title, years, city, state, tier, bio, available, photo, verified, referral, officer, charter, business, phone, email, website, mobile, logo, bizPhoto.
3. Member-tier listings may not carry business name, phone, email, website, logo or business photo.

Never read, so never published: personal email/phone, member number, dues card, review keys, vouch keys, voucher identity, secretary identity and answer text, Review Log, notes, addresses, ZIP.

Logic-only fields (used to decide, never copied): Status, Listing Tier, Has Business, Payment Status, Verification Method, Secretary Answer.

## 6. How each listing is built — FACT

| Output | Rule |
|---|---|
| tier | Business/Featured only if Has Business is true **and** the tier says Business or Featured; otherwise Member. |
| org / orgs | Codes turned into full official names; Divine Nine by name only. |
| chapter | Standard format "<Name> <Temple/Lodge/Chapter/Court> No. <n>". |
| city / state | Business city/state for business listings when filled; otherwise member city/state. |
| verified | Always true (only approved records publish). |
| referral | Verification Method = Member vouch → "Verified (member referral)". |
| officer | Secretary Answer = In good standing or Not current, never expelled → "Verified (chapter officer)". |
| charter | Payment Status = Charter (free). |
| Business contact | Business listings only; Member listings get empty values. |

Sort: business listings first, then by last name.

## 7. Images — FACT

- Member photo, business logo and business photo are downloaded from Airtable into `img/` (Airtable links expire after a few hours).
- File name: `<recordId>-<photo|logo|biz>-<8-char hash of the attachment id>.jpg|.png`. A new upload gets a new name, so browsers never show a stale photo.
- An existing file is not downloaded again.
- Orphans: every run deletes any `img/rec…` file not used by a current Active listing (removed or held members lose their photos from the site on the next run).
- Dues cards are never touched: they live only in a private Drive folder and the script never reads that field.

## 8. Samples — FACT

Fewer than 5 Active listings → the 10 labeled samples from `scripts/sample_listings.json` are added and `demo` is true. At 5 or more they hide. Today: 11 Active, demo = false.

## 9. Write and commit — FACT

`listings.json` = `{updated, demo, real, listings[]}`. If nothing but the date changed, the file is not rewritten and no commit is made (no empty "publish" commits).

## 10. Evidence (Nov 27, 2026) — FACT

- Last 40 runs: 39 success, 1 failure (manual run Nov 26, 12:04 PM ET; later runs succeeded).
- Last run: manual, Nov 27, 1:12 PM ET, success. `listings.json`: 11 real, demo false.
- `tests/test_privacy.py` passes: Member listing business fields empty; unexpected key stops the publish.

## 11. Gaps owned by later tasks

| Gap | Task |
|---|---|
| Image names use the Airtable record ID, not `FVD-ID-1.jpg` as Spec B5-T3 says. DECISION (Jermaine, Nov 27): keep record-ID names. | B5-T3 |
| ~~No orphan test file yet.~~ Done Nov 27: `tests/test_images.py` (orphan deleted, site art kept, stable names, one download, dues card never published). | B5-T3 |
| "Publish now" is a GitHub button, not one tap from the approval email. Approve → live can take up to 30 min (overnight approvals wait until 6 AM). | B5-T4 |
| No FVD-specific failure email. GitHub's own failure notice may reach the account owner; not verified. | B5-T5 (UNKNOWN until tested) |
| ~~Field allowlist not yet diff-tested on staging.~~ Done Nov 27: `tests/test_allowlist_staging.py` (2 staging canary records, every private field marked; 0 leaks, planted leak caught). | B5-T2 |

## 12. Rollback

Revert the last "Publish approved listings" commit, or set the member's Status to Hold and run the workflow. Script changes: revert the commit that changed `scripts/sync_listings.py`.
