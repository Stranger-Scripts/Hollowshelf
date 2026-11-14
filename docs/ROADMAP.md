# Hollowshelf: Roadmap

> **When** each requirement in [URS.md](URS.md) gets done. One milestone is
> active at a time. A milestone closes when its exit criteria hold, not on a
> date. Status as of 2026-11-14 (v0.3 of the plan).

```
M0 Stabilise ─► M1 Trustworthy core ─► M2 Capture & sources ─► M3 Daily driver ─► M4 Distribution ─► M5 UI overhaul
   (now)           v0.2.0                 v0.3.0                  v0.4.0              v0.9.0              v1.0.0
```

**Rationale for this order:**
- Data safety comes before data entry (M1). Scanning and the wishlist make data entry faster, so the data has to be safe first.
- Distribution (M4) comes before the UI overhaul (M5), so that real releases exist and the update checker is proven before 1.0.
- The UI overhaul is last, as requested, once the feature set is stable.

M2 and M3 can be swapped if export and restore feel more urgent than scanning.

---

## M0: Stabilise *(active)*

**Goal:** a fresh clone of `main` installs, runs and passes CI. The repo is licensed.

**Why first:** right now the repo can't be trusted as a base.
- On `de-translation`, the committed UI code imports `hollowshelf.i18n`, but `i18n.py`, `locales/` and `babel.cfg` are untracked, so a fresh clone fails.
- CI runs `pytest`, but `pytest` isn't a dependency and there's no `tests/` directory.
- `.gitignore` excludes `*.mo`, while `pyproject.toml` ships `.mo` files as package data.
- The repo is public but has no license, which by default means all rights reserved.

| # | Task | Ref |
|---|------|-----|
| 0.1 | Commit the i18n infrastructure on `de-translation` so the branch is self-consistent. Completing the translations stays in M3. | UI-002 |
| 0.2 | Decide on `.mo` handling (commit them, or compile in a build step). Make `.gitignore` and `pyproject.toml` agree. | UI-002 |
| 0.3 | Add `.nicegui/` to `.gitignore`. Delete the stray root `book_cache.db`. | DATA-001 |
| 0.4 | Add `pytest` to the dev dependencies. Create `tests/` with a DB smoke test. | NFR-006 |
| 0.5 | Get `ruff check` and `ruff format --check` passing. CI green. | NFR-006 |
| 0.6 | **Decide OD-8**, then add `LICENSE` with `© 2026 Gabriel Geissler`, the SPDX field in `pyproject.toml`, and a README footer. | LIC-001, LIC-002 |
| 0.7 | Merge `de-translation` → `main`. Delete the merged remote branches `book-search` and `translation`. | GUIDELINES §3 |
| 0.8 | Replace "Future Ideas" in the README with a link to this roadmap. | GUIDELINES §1 |
| 0.9 | **Decide OD-2 (now including the wishlist model), OD-3 and OD-7.** | URS §4 |

**Exit criteria**
- [ ] A fresh clone of `main` → `uv sync` → `uv run hollowshelf` works
- [ ] CI green on `main`; only `main` exists as a long-lived branch
- [ ] LICENSE in place
- [ ] OD-2, OD-3, OD-7 and OD-8 are recorded as decisions

---

## M1: Trustworthy core → v0.2.0

**Goal:** I can enter my real library on Linux or Windows and trust that it won't be lost, corrupted, or stored in the wrong place. Lookups are fast.

| Scope | Requirements |
|-------|--------------|
| Verify existing (write tests or manual checks) | CAT-001…007, LKP-001…006, SRCH-001…003, REV-001…002, DATA-005, UI-001 |
| Build new | **DATA-001** (platformdirs paths, schema in the package, NiceGUI storage), **DATA-003** (backups), **DATA-002** (migrations), **LKP-007** (concurrent, progressive lookups), UPD-002, CAT-009, LKP-003, LKP-004 (negative cache) |
| Platform | NFR-004: add `windows-latest` to the CI matrix |
| Non-functional | NFR-001, NFR-002, NFR-003, NFR-005 |

**Proposed order:**
1. DATA-001: everything else writes files, so paths come first.
2. Windows CI.
3. DATA-003, then DATA-002, since migrations rely on backups.
4. LKP-007: measure first with `scripts/bench_lookup.py`, then change.
5. Tests for the existing features.
6. The rest.

**Exit criteria**
- [ ] Every M1 **Must** is `Verified`
- [ ] CI green on Linux **and** Windows
- [ ] The library lives in the OS user-data directory, and a backup is written on every start
- [ ] A test migration upgrades a populated DB without data loss
- [ ] The LKP-007 target is met (before/after benchmark recorded in the PR)
- [ ] Tag `v0.2.0`, then start entering the real collection

---

## M2: Capture & sources → v0.3.0

**Goal:** adding books is fast (scan, more sources), and I can keep a wishlist.

| Requirement | Note |
|-------------|------|
| LKP-008 Source registry + settings | build this first; the new sources plug into it |
| LKP-009 Key handling | needs OD-10 |
| LKP-011 Hardcover (opt-in token) | |
| LKP-015 ISFDB (keyless) | check the data licence first |
| WISH-001…004 Wishlist | data model from OD-2 |
| CAT-010 Duplicate warning | needed once scanning makes double entry easy |
| SCAN-001…004 Webcam scanning | **time-boxed spike first** (OD-11) |

**Exit criteria**
- [ ] All M2 **Must/Should** are `Verified`
- [ ] Scanning a book on Linux and on Windows fills the form with no typing
- [ ] Tag `v0.3.0`

---

## M3: Daily driver → v0.4.0

**Goal:** comfortable for everyday use in both languages, with a guaranteed way out.

| Requirement | Note |
|-------------|------|
| UI-002 German/English UI, completed | |
| SRCH-004 German search quality | needs OD-4 |
| PORT-001 CSV export | the "exit insurance" |
| DATA-004 Restore from backup | |
| CAT-008 Covers | needs OD-5 |
| SRCH-005 Author/series/genre filters | *Could*: drop it if M3 drags |

**Exit criteria**
- [ ] All M3 **Must/Should** are `Verified`
- [ ] Two weeks of real use with no data issue
- [ ] Tag `v0.4.0`. **Feature freeze** for v1.0.

---

## M4: Distribution → v0.9.0

**Goal:** installable on Linux and Windows from a GitHub Release, and the app knows when a newer one exists.

| Requirement | Note |
|-------------|------|
| REL-004 Release pipeline (CD) | needs OD-6 |
| REL-001 Install path | needs OD-1 (macOS?) and OD-6 |
| UPD-001 Update check | needs OD-12; test it against the real v0.9.0 → v0.9.1 releases |
| UI-006 About page | |
| LIC-002 © in the app, LIC-003 third-party notices | |
| NFR-004 Full Windows verification | |
| REL-002, REL-003 README, CHANGELOG | |

**Exit criteria**
- [ ] A clean-machine install from a GitHub Release works on Linux and on Windows
- [ ] A running v0.9.0 detects a published v0.9.1
- [ ] Tag `v0.9.0`

---

## M5: UI overhaul → v1.0.0

**Goal:** one coherent interface over the finished feature set.

| Requirement | Note |
|-------------|------|
| UI-005 UI overhaul | design pass doc first, then implementation |
| UI-003 Dark mode | candidate to promote into UI-005 at the M4→M5 review |

**Exit criteria**
- [ ] The design doc is reviewed, and every page follows it
- [ ] The full test suite is green; Windows smoke test passed
- [ ] Tag `v1.0.0` (shipped through the M4 pipeline, and detected by v0.9.x installs)

---

## Parking Lot *(not scheduled)*

Nothing here gets built before v1.0 unless it is promoted through the scope gate ([GUIDELINES.md §1](GUIDELINES.md#1-scope-gate)).

| ID | Idea | Origin |
|----|------|--------|
| PORT-002 | Goodreads / LibraryThing CSV import (the only route for Goodreads data) | README "Future Ideas" |
| PORT-003 | `.xlsx` export | README "Future Ideas" |
| PORT-004 | Review/journal export via pandoc (`.md`/`.docx`) | README "Future Ideas" |
| UI-003 | Dark mode toggle (candidate for UI-005) | README "Future Ideas" |
| UI-004 | Reading statistics dashboard (books/year, top genres, streaks, when a book was added) | README "Future Ideas" |
| — | Other scanner inputs besides the webcam (you said "webcam *for now*") | 2026-11-14 |
| — | **Maybe: scraper-type sources** (Amazon, Goodreads, Kobo, Moly, Biblio, …). Promoting one needs a decision on terms of service, breakage and maintenance cost. | 2026-11-14 (D-016) |
| — | Other sources evaluated and parked (Apple/iTunes, WorldCat, Libris, BnF, DNB, ISBNPlus, paid APIs); see [notes/metadata-sources.md](notes/metadata-sources.md) | 2026-11-14 |
