# Lookup performance: findings (2026-11-14)

Context: lookups "seem slow". Ref. **URS LKP-007**.

**Limitation:** I couldn't take live timings. Neither the analysis sandbox nor
the local VM could reach Open Library or Google Books. The findings below come
from reading `book_client/`. To get real numbers, run on your machine:

```bash
uv run python scripts/bench_lookup.py            # default ISBNs + 2 title searches
uv run python scripts/bench_lookup.py 978…       # your own ISBNs
```

It prints every HTTP round trip with its duration, using a cold, throw-away cache.

## Request chain today

Every step runs **sequentially** in one `run.io_bound` worker thread.

**ISBN lookup** (`BookClient.search_by_isbn`):

1. `GET openlibrary.org/isbn/{isbn}.json` → 302 → `GET /books/OL…M.json` *(2 round trips, `follow_redirects=True`)*
2. `GET /authors/OL…A.json` **once per author**, one after another (`_resolve_authors`)
3. `GET googleapis.com/books/v1/volumes?q=isbn:…` *(always runs, even when the Open Library record is complete)*

→ Latency is the **sum** of all of them: 4 round trips for a single-author book, 6 for three authors.

**Title search:** `openlibrary.org/search.json`, then Google Books (2 sequential).
After that the UI loads up to 8 **large** (`-L.jpg`) covers from
`covers.openlibrary.org` for 64×96 px thumbnails.

## Causes and options

| # | Cause | Effect | Fix options (trade-off) |
|---|-------|--------|-------------------------|
| P1 | Providers queried sequentially | Total = sum of provider latencies | Query concurrently (`ThreadPoolExecutor` or `httpx.AsyncClient` + `gather`). **Prerequisite:** `Cache` shares one SQLite connection across threads (`check_same_thread=False`) with no lock, so add a lock or use a connection per thread. |
| P2 | Author names resolved N+1, sequentially | +1 round trip per author | Parallelise, or fetch names inline (Open Library Books API `api/books?bibkeys=ISBN:…&jscmd=…`). *First verify it still exposes `physical_format`, which D-006 relies on.* Author JSON is already cached per URL, so repeat authors cost nothing. |
| P3 | `/isbn/` endpoint redirects | +1 round trip | Use the endpoint mentioned in P2, which also removes the redirect |
| P4 | Enrichment always queries Google | +1 provider even when nothing is missing | Skip the secondary provider when the primary result is complete (you lose Google's richer descriptions), or enrich in the background after showing the first result |
| P5 | No negative caching (404s and failures aren't cached) | Repeat misses always hit the network | Cache "not found" with a short TTL (e.g. 1 day). Never cache 429/5xx. |
| P6 | 10 s timeout per phase, no overall deadline, results shown only when everything has finished | One slow provider blocks the whole result | Shorter connect timeout, a per-lookup deadline, and **progressive results** (show each provider's hits as they arrive) |
| P7 | Large covers in the result list | The UI *feels* slow even after data has arrived | Use `-S`/`-M` for the result cards and fetch `-L` only for the saved cover |
| P8 | A keyless Google 429 looks identical to "no matches" | Hard to tell slow from failed | Part of LKP-003 (clear failure messages) |

**Expected impact (to confirm with the benchmark):** P1, P2 and P6 cut
wall-clock time, and P7 improves how fast it feels. P1 is also a prerequisite
for adding more sources (LKP-010/011). With sequential queries, every new
provider adds its full latency to every lookup.
