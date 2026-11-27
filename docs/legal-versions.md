# Legal page versions and change log (Spec B8-T1)

Each public legal page shows a version (the date of its last change). The sign-up form records the versions the member agreed to, with the time, in the Airtable field "Marks Attestation", e.g. `Yes – 11/27/2026, 3:50:00 PM ET – agreed to Terms v2026-11-27, Privacy v2026-11-22`.

**Rule:** any change to terms.html or privacy.html needs Jermaine's sign-off, and then three updates in the same commit:
1. the version line on the page;
2. `LEGAL_VERSIONS` in index.html and staging/index.html;
3. a row below.

| Page | Version | What changed |
|---|---|---|
| Terms | 2026-11-27 | Section 3: founding sign-ups (on or before Mar 31, 2027) free for one year from approval. |
| Terms | 2026-11-26 | "Featured" renamed "Business Elite". |
| Terms | 2026-11-23 | Prices removed during the free founding period; 30 days' notice before any fee. |
| Terms | 2026-11-22 | Member vouch; optional dues card; member emblem policy and 48-hour takedown; prices hidden. |
| Terms | 2026-11-21 | Tier perks; Send a Message; official FVD email; Divine Nine by name only. |
| Terms | 2026-11-14 | First version. |
| Privacy | 2026-11-22 | Dues card photos: stored privately, deleted after verification. |
| Privacy | 2026-11-21 | Official FVD email. |
| Privacy | 2026-11-14 | First version. |
| FAQ | 2026-11-27 | Free for one year from approval. |
| FAQ | 2026-11-26 | Member vs Business paths; contact answer. |
| FAQ | 2026-11-23 | Free founding period; no prices. |
| FAQ | 2026-11-22 | Vouch, dues card, emblem policy, takedown. |

Before Nov 27, 2026 the Terms and Privacy pages said "Last updated November 14, 2026" even after later changes. Sign-ups before Nov 27 do not have a recorded version. The page history in git shows which text was live on any date.
