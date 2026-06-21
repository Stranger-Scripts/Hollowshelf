"""Tiny SQLite response cache (TTL in days).

Keying every HTTP lookup here is what keeps the app well under any informal
provider rate limits — the same ISBN or title is never fetched twice within the
TTL window.
"""

from __future__ import annotations

import json
import sqlite3
import time
from typing import Optional


class Cache:
    def __init__(self, path: str = "book_cache.db", ttl_days: int = 30):
        self.ttl = ttl_days * 86_400
        # check_same_thread=False: lookups run in a worker thread (run.io_bound)
        # while the cache is created on the main thread.
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS cache "
            "(key TEXT PRIMARY KEY, ts REAL, body TEXT)"
        )
        self.db.commit()

    def get(self, key: str) -> Optional[dict]:
        row = self.db.execute(
            "SELECT ts, body FROM cache WHERE key = ?", (key,)
        ).fetchone()
        if not row:
            return None
        ts, body = row
        if time.time() - ts > self.ttl:
            return None
        return json.loads(body)

    def set(self, key: str, body: dict) -> None:
        self.db.execute(
            "INSERT OR REPLACE INTO cache VALUES (?, ?, ?)",
            (key, time.time(), json.dumps(body)),
        )
        self.db.commit()
