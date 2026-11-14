# Hollowshelf: User Requirements Specification

| Field    | Value                                                          |
|----------|----------------------------------------------------------------|
| Doc ID   | HS-URS-001                                                     |
| Version  | 0.3 (draft)                                                    |
| Date     | 2026-11-14                                                     |
| Owner    | Gabriel Geissler                                               |
| Status   | **Draft.** Priorities and milestones are *proposals* awaiting owner review. Section 4 lists the open decisions. |

> This is the single source of truth for **what** Hollowshelf must do.
> [ROADMAP.md](ROADMAP.md) says **when**, [GUIDELINES.md](GUIDELINES.md) says
> **how work gets in**, and [DECISIONS.md](DECISIONS.md) says **why**.
> If a feature isn't here, it doesn't get built. It goes to the Parking Lot first.

---

## 1. Purpose

Hollowshelf is a personal catalog of the books I own (physical books, ebooks and
audiobooks, in German and English) and of the books I want to own (wishlist).
It stores information *about* the items: metadata, where they are, reading
status, reviews and a reading journal. It does **not** store the book files themselves.

## 2. Scope

### 2.1 In scope

- Cataloguing owned items in three formats: physical, ebook and audiobook
- A wishlist of items not yet owned (D-011)
- Metadata lookup from **Open Library, Google Books and ISFDB** (keyless), plus **Hardcover** (opt-in, free personal token). No other sources for now (D-016).
- Adding a book by scanning its ISBN barcode with a webcam
- Full-text search and filtering across the catalog and my own notes
- Markdown reviews and a dated reading journal for each item
- Keeping the data safe: one local database in the per-user data directory, with backups and schema migrations
- Getting my data out in an open format
- Distribution on Linux and Windows (D-012), with an in-app update check
- A licensed codebase, with copyright shown in the repo and in the app

### 2.2 Non-goals (decided; see D-007)

Anything below is **out of scope for v1.0**. Reopening one requires a new entry in DECISIONS.md.

| ID    | Non-goal                                                                       |
|-------|--------------------------------------------------------------------------------|
| NG-01 | Multi-user support, accounts, authentication                                   |
| NG-02 | Hosted/web deployment, server processes, access from other devices (e.g. from Forge) |
| NG-03 | Sync between machines                                                          |
| NG-04 | Storing, opening or playing the ebook/audiobook files themselves               |
| NG-05 | Mobile app                                                                     |
| NG-06 | Social features (sharing, following, public profiles)                          |
| NG-07 | A second database or storage engine (document DB, PostgreSQL); see D-002, D-003 |
| NG-08 | ~~Scraping websites that have no API~~. *Withdrawn in v0.3:* scraper-type sources are now a **maybe** in the Parking Lot (D-016). |
| NG-09 | Automatic self-update (installing new versions); the app only notifies. *Proposed: confirm via OD-12 / D-014* |
| NG-10 | **Paid metadata APIs** (e.g. ISBNdb) and APIs that need an institutional or commercial account (e.g. WorldCat, Amazon Creators API) (D-016) |

## 3. User and operating context

- **User:** exactly one person (the owner), on one machine.
- **Runtime:** a native desktop window (`NiceGUI native=True`), Python ≥ 3.12, managed with `uv`.
  - Linux: pywebview with the Qt6 backend.
  - Windows: pywebview with WebView2.
- **Network:** needed only for metadata lookups and the optional update check. Everything else has to work offline.
- **Data:** one SQLite file with the FTS5 schema, plus a separate disposable API cache. Both live in OS user directories, never in the source tree (DATA-001).

## 4. Open decisions (owner input needed)

These block or shape requirements. Each one should end up in DECISIONS.md.

| ID   | Question | Affects | Needed by |
|------|----------|---------|-----------|
| OD-1 | ~~Linux only or all three?~~ **Linux + Windows decided (D-012).** Still open: macOS — in or out for v1.0? | NFR-004, REL-001 | M4 |
| OD-2 | Same title in several formats, **and now the wishlist**: keep the flat model and add an `ownership` column (`owned` / `wishlist`), or split into `work` + `copy`, where a wishlist entry is simply a work with no copy? A split is cleaner for wishlist→owned and for duplicates, but it costs more to migrate, and that cost grows with every row entered. | CAT-*, WISH-*, DATA-002 | **M1 start** |
| OD-3 | `book.review` and journal entries with `entry_type='review'` overlap. Keep both? If so, what is each one for? | REV-001, REV-002 | M1 |
| OD-4 | German search quality: the `porter` tokenizer is English-only. Drop it, keep it, or run per-language indexes? | SRCH-004 | M3 |
| OD-5 | Covers: hot-link the URL (breaks offline, see NFR-001), or cache images locally? | CAT-008, NFR-001 | M3 |
| OD-6 | Distribution for v1.0: `uv tool install git+…`, a frozen binary (`nicegui-pack`/PyInstaller), or both? This decides what the release pipeline builds (REL-004). | REL-001, REL-004 | M4 |
| OD-7 | Performance targets (proposed, NFR-003 and LKP-007): confirm or adjust the numbers. | NFR-003, LKP-007 | M1 |
| OD-8 | **License:** MIT / Apache-2.0 (permissive, Apache adds a patent grant) vs. GPL-3.0 (copyleft). Note: on Linux the app depends on **PyQt6, which is GPL-3.0** (or commercial). Permissive licensing of your own code is compatible with that, but a *bundled binary* that ships PyQt6 has to be distributed under GPL terms as a whole. | LIC-001…003, OD-6 | **M0** |
| OD-9 | *Source set decided (D-016).* Still open: the default **priority order** for merging (e.g. Open Library > Google Books > ISFDB > Hardcover), and whether ISFDB should rank higher for speculative fiction. | LKP-001, LKP-008 | M2 |
| OD-10 | API key storage: plaintext in the DB `settings` table (current state for Google; simple, but every backup then contains the key) vs. the OS keyring (`keyring`: Windows Credential Manager / Secret Service; needs a running secret service on Linux). | LKP-009 | M2 |
| OD-11 | Scanner architecture: **(a)** Python-side capture (OpenCV + `zxing-cpp` decoder, preview streamed into NiceGUI; works whatever the webview does about camera permissions, but adds roughly 50–90 MB of wheels) vs. **(b)** in-webview `getUserMedia` + a bundled JS decoder (light, but depends on how QtWebEngine/WebView2 under pywebview handle camera permission prompts). Proposal: a time-boxed spike on (b), falling back to (a). | SCAN-* | M2 start |
| OD-12 | Update check: on or off by default? Notify-only (NG-09), or also offer to download the release artifact? | UPD-001 | M4 |

## 5. Conventions

- **ID:** `<AREA>-<nnn>`. IDs are never reused; a retired requirement is marked *Withdrawn*.
- **Priority (MoSCoW):** **M**ust · **S**hould · **C**ould · **W**on't (this version)
- **Milestone:** M0–M5, as defined in ROADMAP.md
- **Status:**
  - `Open`: not started
  - `Partial`: some acceptance criteria met
  - `Impl.`: code exists, nothing has verified it
  - `Verified`: every acceptance criterion passes by the stated method
  - `Blocked`: an external constraint prevents it
  - `Withdrawn`: no longer required
- **Verify:** `T` = automated test · `M` = manual check, recorded in the PR
- *Status as of 2026-11-14, taken from branch `de-translation` @ `7c2a910`. No test suite exists yet, so nothing is `Verified`.*

---

## 6. Functional requirements

### 6.1 CAT: Catalog management

**CAT-001: Add an item**
*As the owner, I want to add an item I own so the catalog matches my shelves and devices.*
Pri **M** · M1 · Status `Impl.` · Verify T
- The item can be saved with only a title; every other field is optional.
- Saving without a title is rejected with a visible message, and nothing is written.
- After saving, the item shows up in the library grid and in search results.

**CAT-002: Edit and delete an item**
*As the owner, I want to correct or remove an item.*
Pri **M** · M1 · Status `Impl.` · Verify T
- Edits persist after the app restarts.
- Delete asks for confirmation, and it removes the item's journal entries and author/genre links (cascade).
- After a delete the item no longer appears in search results (FTS index in sync).

**CAT-003: Three formats with format-specific fields**
*As the owner, I want to record whether an item is physical, ebook or audiobook, along with the fields that matter for each.*
Pri **M** · M1 · Status `Impl.` · Verify T
- Format is one of `physical | ebook | audiobook`; the database rejects anything else.
- Page count (physical/ebook), duration in minutes (audiobook) and file format (ebook/audio) can all be stored.

**CAT-004: Contributors with roles**
*As the owner, I want several authors in cover order, plus narrators for audiobooks.*
Pri **M** · M1 · Status `Impl.` · Verify T
- An item can have N authors and N narrators, stored with role and order.
- An author is stored once and reused across items (no duplicate author rows for the same name).

**CAT-005: Series**
*As the owner, I want to record a series and an item's position in it (including 1.5 for novellas).*
Pri **S** · M1 · Status `Impl.` · Verify T

**CAT-006: Location**
*As the owner, I want to know where an item lives: a shelf, a device, or a service.*
Pri **M** · M1 · Status `Impl.` · Verify M

**CAT-007: Personal metadata**
*As the owner, I want to track reading status, rating and acquisition date.*
Pri **M** · M1 · Status `Impl.` · Verify T
- Status is one of `unread | reading | read | dnf | reference`.
- Rating is 1–5 or empty; the database rejects other values.

**CAT-008: Cover image**
*As the owner, I want to see an item's cover.*
Pri **C** · M3 · Status `Partial` (URL hot-link only) · Verify M · *Depends on OD-5*

**CAT-009: Input validation**
*As the owner, I want obviously wrong input caught before it reaches the database.*
Pri **S** · M1 · Status `Open` · Verify T
- An ISBN-13 checksum failure triggers a warning (non-blocking).
- Dates must match `YYYY`, `YYYY-MM` or `YYYY-MM-DD`; anything else is rejected with a message.

**CAT-010: Duplicate warning**
*As the owner, I want a warning before I add something I already own or already have on my wishlist.*
Pri **S** · M2 · Status `Open` · Verify T · *Depends on OD-2*
- Saving warns when an existing item (owned or wishlist) has the same ISBN-13, or the same title + format. The user can still save.
- A scan (SCAN-001) of an ISBN that's already in the catalog shows the existing item instead of an empty form.

### 6.2 WISH: Wishlist *(new in v0.2)*

**WISH-001: Add to wishlist**
*As the owner, I want to note books I'd like to own, using the same lookup/scan flow as for owned items.*
Pri **S** · M2 · Status `Open` · Verify T · *Depends on OD-2*
- A wishlist entry can be created by hand, from a lookup result, or from a scan.
- Location and acquired date aren't required for wishlist entries.

**WISH-002: Wishlist view**
*As the owner, I want my wishlist kept separate from my library.*
Pri **S** · M2 · Status `Open` · Verify T
- The wishlist has its own page/grid. Wishlist entries don't appear in the library grid or its counts.
- Full-text search can be scoped to the library, the wishlist, or both.

**WISH-003: "Got it": move to library**
*As the owner, when I buy a wishlist book I want to move it into my library without re-entering anything.*
Pri **S** · M2 · Status `Open` · Verify T
- One action turns a wishlist entry into an owned item. All metadata and notes are kept, I'm asked for format and location, and the acquired date defaults to today.

**WISH-004: Remove from wishlist**
Pri **S** · M2 · Status `Open` · Verify T
- Deleting a wishlist entry works like CAT-002, including the confirmation.

### 6.3 LKP: Metadata lookup

**LKP-001: Look up by ISBN or title/author**
*As the owner, I want metadata filled in from an ISBN or a title so I don't have to type it.*
Pri **M** · M1 · Status `Impl.` · Verify T (parsers, with recorded fixtures) + M (live)
- Enabled providers are ranked by priority: the highest-priority hit wins, and lower-priority hits fill in missing fields.
- A result is shown for review and is only applied to the form when I confirm it.

**LKP-002: Non-blocking lookup**
*As the owner, I want the window to stay responsive during a lookup.*
Pri **M** · M1 · Status `Impl.` · Verify M
- All HTTP runs off the UI event loop (D-005).

**LKP-003: Graceful failure**
*As the owner, I want a lookup that fails (offline, 429 quota, timeout) to tell me what happened and leave the form usable.*
Pri **M** · M1 · Status `Partial` · Verify T
- The message distinguishes "no match" from "a source failed" and says which one. No traceback; the form data is preserved.

**LKP-004: Response cache**
*As the owner, I want repeat lookups to be instant and to spare the API quotas.*
Pri **S** · M1 · Status `Impl.` · Verify T
- Successful responses are cached with a 30-day TTL, and "not found" for 1 day (proposed). Errors (429/5xx) are never cached.
- The cache lives in the user cache directory (DATA-001) and can be deleted without any data loss.

**LKP-005: Media type is a hint**
*As the owner, I want the format guessed from metadata, while I keep the final say.*
Pri **S** · M1 · Status `Impl.` · Verify M
- The detected format pre-selects the dropdown and can always be changed (D-006).

**LKP-006: API identification**
*As the owner, I want lookups to send a proper User-Agent, as Open Library asks.*
Pri **M** · M1 · Status `Impl.` · Verify M

**LKP-007: Lookup speed** *(new; see [notes/lookup-performance.md](notes/lookup-performance.md))*
*As the owner, I want a lookup to feel quick, even with several sources enabled.*
Pri **M** · M1 · Status `Open` · Verify T (benchmark script) + M
- Enabled providers are queried **concurrently**; total latency is bounded by the slowest provider, not their sum.
- Each provider has its own timeout, and one slow or failing provider never blocks the others' results.
- Results appear progressively as each provider responds.
- Result cards use small cover thumbnails.
- *Target (proposed, OD-7):* a cold ISBN lookup shows its first result in ≤ 3 s at the median on the dev machine and network. A warm (cached) lookup takes ≤ 200 ms.

**LKP-008: Source registry and settings** *(new)*
*As the owner, I want to see every available source and choose which ones are used.*
Pri **M** · M2 · Status `Partial` (provider abstraction exists; no UI) · Verify T + M
- The Settings page lists every provider with its name, whether it needs a key, an enabled toggle, and priority order.
- Providers that need a key are **disabled by default** and can't be enabled until a key is entered.
- Changes take effect without restarting the app.
- Keyless providers (Open Library, Google Books, ISFDB) are enabled by default. Hardcover stays disabled until a token is set. The priority order is set by OD-9.

**LKP-009: API key handling** *(new)*
*As the owner, I want API keys handled carefully.*
Pri **M** · M2 · Status `Partial` (Google key stored in plaintext in the DB) · Verify T · *Depends on OD-10*
- Keys are never logged (already true for request params), never included in CSV export, and are masked in the UI.

**LKP-010: Apple Books / iTunes** · Status `Withdrawn` (v0.3). Removed from scope for now; see [notes/metadata-sources.md](notes/metadata-sources.md).

**LKP-011: Hardcover (opt-in, personal API token)** *(new)*
*As the owner, I want to optionally use Hardcover's catalog, which is strong on series and editions.*
Pri **S** · M2 · Status `Open` · Verify T (fixtures) + M
- GraphQL API with a personal access token. It stays disabled until a token is entered (LKP-008).
- Free-tier limits are about 5,000 requests/day and 60/min; the client stays under them.

**LKP-012: Amazon** · Status `Withdrawn` (v0.3). Moved to the Parking Lot as a *maybe* (scraper-type source).

**LKP-013: Goodreads** · Status `Withdrawn` (v0.3). Moved to the Parking Lot as a *maybe*. Goodreads data can come in via PORT-002 (CSV import).

**LKP-014: Kobo** · Status `Withdrawn` (v0.3). Moved to the Parking Lot as a *maybe* (scraper-type source).

**LKP-015: ISFDB (keyless)** *(new in v0.3)*
*As the owner, I want rich metadata for speculative fiction (series, editions, cover artists) from the Internet Speculative Fiction Database.*
Pri **S** · M2 · Status `Open` · Verify T (recorded XML fixtures) + M
- Uses the read-only Web API: `https://www.isfdb.org/cgi-bin/rest/getpub.cgi?<ISBN>`, which takes ISBN-10 or ISBN-13 and needs no key.
- The XML response (encoded as ISO-8859-1) is mapped into `BookResult`. A response of "0 records" counts as not found (LKP-004 negative cache).
- No rate limit is published, so the client stays polite: cache first, and never more than one request in flight to ISFDB.
- *Before release:* confirm ISFDB's data licence and attribution terms (LIC-003).

### 6.4 SCAN: Barcode scanning *(new in v0.2)*

**SCAN-001: Scan ISBN with webcam**
*As the owner, I want to hold a book up to my webcam and have it looked up without typing.*
Pri **S** · M2 · Status `Open` · Verify M (+ T for the decode→lookup path with recorded frames) · *Depends on OD-11*
- "Scan" is available from Add item and from the Wishlist, and opens a live camera preview.
- Only EAN-13 codes with a 978/979 prefix and a valid checksum are accepted. Other barcodes (prices, EAN-5 add-ons) are ignored.
- A successful decode triggers the ISBN lookup (LKP-001) **automatically**, and the result is shown for confirmation.
- Manual ISBN entry is still available as a fallback.

**SCAN-002: Camera handling**
Pri **S** · M2 · Status `Open` · Verify M
- If there are several cameras, I can pick one, and the choice is remembered.
- A missing camera or denied access shows a clear message.
- The camera is released as soon as the scanner closes.

**SCAN-003: Optional dependency**
Pri **S** · M2 · Status `Open` · Verify T
- The scanning dependencies are an optional extra (e.g. `hollowshelf[scan]`). Without it the app runs normally, and the Scan button explains how to enable it.

**SCAN-004: Cross-platform**
Pri **S** · M2 · Status `Open` · Verify M
- Scanning works on Linux and Windows with a standard USB/built-in webcam.

### 6.5 SRCH: Search and browse

**SRCH-001: Library grid**
Pri **M** · M1 · Status `Impl.` · Verify M
- Columns: title, authors, series, format, status, rating, year. Double-clicking a row opens the item.

**SRCH-002: Full-text search**
*As the owner, I want one search box that finds items by title, subtitle, description, review, or my journal notes.*
Pri **M** · M1 · Status `Impl.` · Verify T
- Prefix matching works ("tolk" finds Tolkien).
- Diacritics are ignored ("Borges" matches "Bórges").
- Catalog hits rank above note-only hits.
- Malformed input never raises an error; it falls back to a LIKE search.

**SRCH-003: Filters (status, format)**
Pri **M** · M1 · Status `Impl.` · Verify T

**SRCH-004: German-language search quality** · Pri **S** · M3 · Status `Open` · Verify T · *Depends on OD-4*

**SRCH-005: Filter by author, series, genre** · Pri **C** · M3 · Status `Open` · Verify T

### 6.6 REV: Reviews and journal

**REV-001: Markdown review**
*As the owner, I want to write a review in markdown with a live preview.*
Pri **M** · M1 · Status `Impl.` · Verify M · *Depends on OD-3*

**REV-002: Reading journal**
*As the owner, I want dated entries per item (note, review, quote, progress) that build up over time.*
Pri **M** · M1 · Status `Impl.` · Verify T

### 6.7 DATA: Data integrity, storage and safety

**DATA-001: Per-user data locations, outside the project** *(amended in v0.2)*
*As the owner, I want my library and settings stored in the proper OS user directories, never inside the source tree, on both Linux and Windows.*
Pri **M** · M1 · Status `Open` (today everything is relative to the repo root) · Verify T (Linux + Windows CI)
- Paths are resolved with `platformdirs`, never hard-coded:

  | What | Linux (XDG) | Windows |
  |------|-------------|---------|
  | `library.db`, backups, NiceGUI storage | `~/.local/share/hollowshelf/` | `%LOCALAPPDATA%\hollowshelf\` |
  | `book_cache.db` | `~/.cache/hollowshelf/` | `%LOCALAPPDATA%\hollowshelf\Cache\` |

- NiceGUI's per-user storage (today `.nicegui/` in the *current working directory*, which holds the UI language) is redirected with `NICEGUI_STORAGE_PATH`. It has to be set before NiceGUI initialises its storage.
- The schema file ships **inside the package** and is loaded with `importlib.resources`. Today `collection_schema.sql` sits at the repo root and is missing from an installed wheel.
- The data directory can be overridden with `HOLLOWSHELF_DATA_DIR` (env var) or `--data-dir` (CLI flag).
- On first start, an existing `<repo>/data/library.db` is detected and offered for one-time migration.
- All path handling uses `pathlib`. It's tested with spaces and non-ASCII characters in the user profile path.
- `git clean -fdx` on the repo cannot delete the library.

**DATA-002: Schema versioning and migrations**
*As the owner, I want schema changes to upgrade my existing database without losing data.*
Pri **M** · M1 · Status `Open` · Verify T
- The database records its schema version (`PRAGMA user_version`).
- On startup, pending migrations run in order inside a transaction, after an automatic backup (DATA-003).
- A failed migration leaves the original file untouched and shows an error.

**DATA-003: Backups**
*As the owner, I want automatic and on-demand backups.*
Pri **M** · M1 · Status `Open` · Verify T
- On startup the app takes a backup with the SQLite backup API, keeping the last N copies (proposed default: 10).
- A "Back up now" action writes to a path I choose.
- A backup opens as a valid Hollowshelf database.

**DATA-004: Restore** · Pri **S** · M3 · Status `Open` · Verify T

**DATA-005: Referential integrity**
Pri **M** · M1 · Status `Impl.` · Verify T
- `PRAGMA foreign_keys = ON` on every connection, and the FTS triggers keep the indexes in sync after insert, update and delete.

### 6.8 PORT: Data portability

**PORT-001: CSV export**
*As the owner, I want to export the full catalog (library and wishlist) to CSV so I'm never locked in.*
Pri **S** · M3 · Status `Open` · Verify T
- UTF-8, opens correctly in Excel and LibreOffice. API keys are never included.

**PORT-002: Goodreads / LibraryThing CSV import** → Parking Lot. *This is the only route for Goodreads data for now.*
**PORT-003: `.xlsx` export** → Parking Lot
**PORT-004: Review/journal export via pandoc** → Parking Lot

### 6.9 UI: Interface

**UI-001: Native desktop window**
Pri **M** · M1 · Status `Impl.` · Verify M
- The app launches as a native window with `uv run hollowshelf`, and no browser tab opens.

**UI-002: German / English UI**
Pri **S** · M3 · Status `Partial` (infrastructure on `de-translation`) · Verify T + M
- Every user-visible string goes through `_()`.
- The `.po` catalog has no untranslated entries.
- The language choice survives restarts.

**UI-003: Dark mode** → Parking Lot (*candidate for inclusion in UI-005*)
**UI-004: Reading statistics** → Parking Lot

**UI-005: UI overhaul** *(new)*
*As the owner, once the features are in place, I want a coherent, polished interface instead of one that grew screen by screen.*
Pri **S** · **M5 (deliberately last)** · Status `Open` · Verify M + regression T
- It starts only after feature freeze (all M1–M4 Musts are `Verified`).
- It begins with a written design pass (navigation, layout grid, theme/colours, typography, component conventions) in `docs/`, which is reviewed before any code changes.
- It covers every page: library, wishlist, item form, scanner, settings, about.
- No functional regressions: the full test suite stays green.

**UI-006: About page** *(new)*
Pri **M** · M4 · Status `Open` · Verify M
- Shows the app name, installed version, copyright (LIC-002), license (LIC-001), repo link, third-party notices (LIC-003), and a "Check for updates" button (UPD-001).

### 6.10 LIC: Licensing and copyright *(new in v0.2)*

**LIC-001: License**
Pri **M** · M0 · Status `Open` · Verify M · *Depends on OD-8*
- There's a `LICENSE` file in the repo root, plus an SPDX `license` field in `pyproject.toml`. The license name is shown in the README and on the About page.

**LIC-002: Copyright notice**
Pri **M** · M0 (repo) / M4 (app) · Status `Open` · Verify M
- The notice reads `© 2026 Gabriel Geissler`, using the year of the first commit (2026-06-16) and the git author name; extend it to a range in later years.
- It appears in the `LICENSE` file, the README footer, and the About page (UI-006).

**LIC-003: Third-party notices and data attribution**
Pri **S** · M4 · Status `Open` · Verify M
- Lists the licenses of runtime dependencies. In particular, PyQt6 (GPL-3.0) is used on Linux.
- Gives attribution for each metadata provider as its terms require.

### 6.11 UPD: Versioning and update check *(new in v0.2)*

**UPD-001: In-app update check**
*As the owner, I want the app to tell me when a newer release is available.*
Pri **S** · M4 · Status `Open` · Verify T (version comparison, mocked API) + M · *Depends on OD-12*
- It queries the GitHub Releases API (`/repos/Stranger-Scripts/Hollowshelf/releases/latest`) in the background, at most once per 24 h at startup, without blocking the UI.
- It compares versions per PEP 440 and ignores pre-releases unless that's opted into.
- When a newer version exists, it shows a non-intrusive notification with the version and a link to the release notes. Nothing is downloaded or installed (NG-09).
- Offline, rate-limited (60 unauthenticated requests/h per IP) and failed checks are silent; they're only logged.
- It can be disabled in Settings, and the About page has a "Check now" button.

**UPD-002: Single-source version**
Pri **M** · M1 · Status `Open` · Verify T
- The version is defined once, in `pyproject.toml`, and read at runtime via `importlib.metadata`. Today it's duplicated in `pyproject.toml` and `__init__.py`.

---

## 7. Non-functional requirements

| ID      | Requirement | Pri | MS | Status | Verify |
|---------|-------------|-----|----|--------|--------|
| NFR-001 | **Offline-first:** every function except lookup and the update check works with no network. Startup doesn't wait on the network. | M | M1 | Partial (covers, OD-5) | M |
| NFR-002 | **Privacy** *(amended)*: the only outbound traffic is (a) lookup queries to **enabled** providers, with the configured User-Agent, and (b) the update check, if enabled. No telemetry. | M | M1 | Impl. (a) | M |
| NFR-003 | **Performance (proposed, OD-7):** with 5,000 items, the grid loads in under 1 s and search returns in under 200 ms on the dev machine. | S | M1 | Open | T (benchmark) |
| NFR-004 | **Platforms** *(amended, D-012)*: Linux and Windows 10/11 are supported; macOS depends on OD-1. CI runs on `ubuntu-latest` and `windows-latest` **from M1**. Each release gets a manual smoke test on Windows (window opens via WebView2, CRUD, lookup, scan, backup). | M | M1 (CI) / M4 (full) | Partial (Linux only) | T + M |
| NFR-005 | **Zero ops:** no server process, no external service that has to be running, no config needed to start. | M | M1 | Impl. | M |
| NFR-006 | **Maintainability:** `ruff check` and `ruff format --check` pass. The DB layer and the API parsers have automated tests. CI is green on `main`. | M | M0 | **Open: CI currently fails** | T |

## 8. Release requirements

| ID      | Requirement | Pri | MS | Status |
|---------|-------------|-----|----|--------|
| REL-001 | Documented install path (OD-6) that works on a clean machine of every supported OS. | M | M4 | Open |
| REL-002 | README covers install, first run, where data lives (per OS), backup/restore, enabling optional sources and scanning, license and ©. | M | M4 | Partial |
| REL-003 | `CHANGELOG.md` and a git tag for each release. | S | M4 | Open |
| REL-004 | **Release pipeline (CD)** *(new)*: pushing a tag `vX.Y.Z` runs the full CI matrix, fails if the tag ≠ package version, builds the artifacts per OD-6, and publishes a GitHub Release with the changelog section. That release is what UPD-001 detects. | M | M4 | Open |

---

## 9. Change history

| Version | Date       | Change |
|---------|------------|--------|
| 0.1     | 2026-11-14 | Initial draft: requirements derived from the existing code, README and design notes. |
| 0.3     | 2026-11-14 | **Source set narrowed (D-016):** added LKP-015 ISFDB; withdrew LKP-010 (Apple/iTunes) and LKP-012…014 (Amazon, Goodreads, Kobo), which moved to the Parking Lot as a *maybe*. Withdrew NG-08 (scraping), added NG-10 (paid/membership APIs), narrowed OD-9. Evaluated sources recorded in notes/metadata-sources.md. |
| 0.2     | 2026-11-14 | Added WISH-001…004, SCAN-001…004, LKP-007…014 (lookup speed, source registry, key handling, Apple/iTunes, Hardcover; Amazon/Goodreads/Kobo recorded as Won't/Blocked), UI-005 (overhaul, last), UI-006, LIC-001…003, UPD-001…002, REL-004. Amended DATA-001 (platformdirs, schema as package resource, NiceGUI storage), NFR-002, NFR-004 (Windows, D-012), CAT-010, LKP-004. Added NG-08, NG-09 and OD-8…12. Milestones restructured to M0–M5. |
