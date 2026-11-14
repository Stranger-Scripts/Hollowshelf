"""Time metadata lookups request-by-request (diagnostic for LKP-007).

    uv run python scripts/bench_lookup.py [ISBN ...]

Uses a throw-away cache, so every run is cold. Prints one line per HTTP
request (duration, status, URL without query string) and the total per lookup.
"""

from __future__ import annotations

import sys
import tempfile
import time
from pathlib import Path

from hollowshelf.book_client import BookClient

DEFAULT_ISBNS = ["9780547928227", "9783596170951"]
TITLES = [("Der Schwarm", "Schätzing", "de"), ("Project Hail Mary", None, None)]

_log: list[tuple[float, int, str]] = []


def _req(request):
    request.extensions["t0"] = time.perf_counter()


def _resp(response):
    dt = time.perf_counter() - response.request.extensions["t0"]
    url = str(response.request.url).split("?")[0]
    _log.append((dt, response.status_code, url))


def _run(label, fn):
    _log.clear()
    t0 = time.perf_counter()
    result = fn()
    total = time.perf_counter() - t0
    print(f"\n== {label}: {total:.2f}s total, {len(_log)} HTTP round trips")
    for dt, code, url in _log:
        print(f"   {dt:6.2f}s  {code}  {url}")
    return result


def main() -> None:
    isbns = sys.argv[1:] or DEFAULT_ISBNS
    with tempfile.TemporaryDirectory() as tmp:
        client = BookClient(cache_path=str(Path(tmp) / "bench_cache.db"))
        client._http.event_hooks = {"request": [_req], "response": [_resp]}
        try:
            for isbn in isbns:
                res = _run(f"ISBN {isbn}", lambda: client.search_by_isbn(isbn))
                print("   ->", (res.title, res.authors, res.source) if res else None)
            for title, author, lang in TITLES:
                hits = _run(
                    f"title {title!r}",
                    lambda: client.search_by_title(title, author, lang, 8),
                )
                print(f"   -> {len(hits)} results")
        finally:
            client.close()


if __name__ == "__main__":
    main()
