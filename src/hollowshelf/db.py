"""SQLite data access for Hollowshelf.

Wraps the schema you authored in ``collection_schema.sql``:
  * auto-initialises the database from that file on first run,
  * adds a small ``app_settings`` table (name/email used for the API
    User-Agent) without touching your schema file,
  * provides book / author / genre / note CRUD,
  * runs FTS5 search across both the catalog and the reading journal.

All writes go through a lock because lookups run in worker threads
(``run.io_bound``) while the UI runs on the main thread.
"""

from __future__ import annotations

import re
import sqlite3
import threading
from pathlib import Path
from typing import Any, Optional

# ISO 639-1 -> display name, for the language lookup table. Extend freely.
_LANG_NAMES = {
    "en": "English", "de": "German", "fr": "French", "es": "Spanish",
    "it": "Italian", "nl": "Dutch", "pt": "Portuguese", "ru": "Russian",
    "ja": "Japanese", "zh": "Chinese", "sv": "Swedish", "da": "Danish",
    "no": "Norwegian", "fi": "Finnish", "pl": "Polish", "la": "Latin",
}

# Author display name expression reused across queries.
_DISPLAY = "TRIM(COALESCE(first_name,'') || ' ' || COALESCE(last_name,''))"


def _int_or_none(value: Any) -> Optional[int]:
    try:
        if value in (None, ""):
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def _float_or_none(value: Any) -> Optional[float]:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _clean(value: Any) -> Optional[str]:
    if value is None:
        return None
    value = str(value).strip()
    return value or None


class Database:
    def __init__(self, db_path: str | Path, schema_path: str | Path):
        self.path = Path(db_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        if not self._has_schema():
            self._init_schema(schema_path)
        self._ensure_settings_table()

    # ----------------------------------------------------------------- setup
    def _has_schema(self) -> bool:
        row = self.conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='book'"
        ).fetchone()
        return row is not None

    def _init_schema(self, schema_path: str | Path) -> None:
        sql = Path(schema_path).read_text(encoding="utf-8")
        with self._lock:
            self.conn.executescript(sql)
            self.conn.commit()

    def _ensure_settings_table(self) -> None:
        with self._lock:
            self.conn.execute(
                "CREATE TABLE IF NOT EXISTS app_settings "
                "(key TEXT PRIMARY KEY, value TEXT)"
            )
            self.conn.commit()

    # -------------------------------------------------------------- settings
    def get_setting(self, key: str, default: Optional[str] = None) -> Optional[str]:
        row = self.conn.execute(
            "SELECT value FROM app_settings WHERE key = ?", (key,)
        ).fetchone()
        return row["value"] if row else default

    def set_setting(self, key: str, value: str) -> None:
        with self._lock:
            self.conn.execute(
                "INSERT INTO app_settings(key, value) VALUES(?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (key, value),
            )
            self.conn.commit()

    def get_profile(self) -> dict[str, str]:
        return {
            "name": self.get_setting("user_name", "") or "",
            "email": self.get_setting("user_email", "") or "",
        }

    def set_profile(self, name: str, email: str) -> None:
        self.set_setting("user_name", name.strip())
        self.set_setting("user_email", email.strip())

    def is_configured(self) -> bool:
        p = self.get_profile()
        return bool(p["name"] and p["email"])

    # ------------------------------------------------------- lookup upserts
    def _get_or_create_author(self, name: str) -> Optional[int]:
        name = (name or "").strip()
        if not name:
            return None
        parts = name.split()
        if len(parts) >= 2:
            first, last = " ".join(parts[:-1]), parts[-1]
            sort = f"{last}, {first}"
        else:
            first, last, sort = "", name, name
        row = self.conn.execute(
            "SELECT author_id FROM author WHERE sort_name = ?", (sort,)
        ).fetchone()
        if row:
            return row["author_id"]
        cur = self.conn.execute(
            "INSERT INTO author(first_name, last_name, sort_name) VALUES(?, ?, ?)",
            (first or None, last, sort),
        )
        return cur.lastrowid

    def _get_or_create_publisher(self, name: Optional[str]) -> Optional[int]:
        name = _clean(name)
        if not name:
            return None
        row = self.conn.execute(
            "SELECT publisher_id FROM publisher WHERE name = ?", (name,)
        ).fetchone()
        if row:
            return row["publisher_id"]
        cur = self.conn.execute(
            "INSERT INTO publisher(name) VALUES(?)", (name,)
        )
        return cur.lastrowid

    def _get_or_create_genre(self, name: Optional[str]) -> Optional[int]:
        name = _clean(name)
        if not name:
            return None
        row = self.conn.execute(
            "SELECT genre_id FROM genre WHERE name = ?", (name,)
        ).fetchone()
        if row:
            return row["genre_id"]
        cur = self.conn.execute("INSERT INTO genre(name) VALUES(?)", (name,))
        return cur.lastrowid

    def _get_or_create_series(self, name: Optional[str]) -> Optional[int]:
        name = _clean(name)
        if not name:
            return None
        row = self.conn.execute(
            "SELECT series_id FROM series WHERE name = ?", (name,)
        ).fetchone()
        if row:
            return row["series_id"]
        cur = self.conn.execute("INSERT INTO series(name) VALUES(?)", (name,))
        return cur.lastrowid

    def _get_or_create_language(self, code: Optional[str]) -> Optional[int]:
        code = _clean(code)
        if not code:
            return None
        code = code.lower()
        row = self.conn.execute(
            "SELECT language_id FROM language WHERE code = ?", (code,)
        ).fetchone()
        if row:
            return row["language_id"]
        name = _LANG_NAMES.get(code, code.upper())
        # name is UNIQUE in the schema; fall back if it already exists.
        existing = self.conn.execute(
            "SELECT language_id FROM language WHERE name = ?", (name,)
        ).fetchone()
        if existing:
            return existing["language_id"]
        cur = self.conn.execute(
            "INSERT INTO language(name, code) VALUES(?, ?)", (name, code)
        )
        return cur.lastrowid

    # -------------------------------------------------------------- book CRUD
    def create_book(self, data: dict) -> int:
        with self._lock:
            book_id = self._upsert_book(None, data)
            self.conn.commit()
        return book_id

    def update_book(self, book_id: int, data: dict) -> None:
        with self._lock:
            self._upsert_book(book_id, data)
            self.conn.commit()

    def delete_book(self, book_id: int) -> None:
        with self._lock:
            self.conn.execute("DELETE FROM book WHERE book_id = ?", (book_id,))
            self.conn.commit()

    def _upsert_book(self, book_id: Optional[int], d: dict) -> int:
        fields = {
            "title": (_clean(d.get("title")) or "Untitled"),
            "subtitle": _clean(d.get("subtitle")),
            "isbn13": _clean(d.get("isbn13")),
            "format": d.get("format") or "physical",
            "publication_date": _clean(d.get("publication_date")),
            "publisher_id": self._get_or_create_publisher(d.get("publisher")),
            "language_id": self._get_or_create_language(d.get("language")),
            "page_count": _int_or_none(d.get("page_count")),
            "duration_minutes": _int_or_none(d.get("duration_minutes")),
            "file_format": _clean(d.get("file_format")),
            "series_id": self._get_or_create_series(d.get("series")),
            "series_position": _float_or_none(d.get("series_position")),
            "location": _clean(d.get("location")),
            "description": _clean(d.get("description")),
            "cover_image_url": _clean(d.get("cover_image_url")),
            "read_status": d.get("read_status") or "unread",
            "rating": _int_or_none(d.get("rating")),
            "acquired_date": _clean(d.get("acquired_date")),
            "review": _clean(d.get("review")),
        }

        if book_id is None:
            cols = ", ".join(fields)
            placeholders = ", ".join("?" for _ in fields)
            cur = self.conn.execute(
                f"INSERT INTO book ({cols}) VALUES ({placeholders})",
                tuple(fields.values()),
            )
            book_id = cur.lastrowid
        else:
            assignments = ", ".join(f"{k} = ?" for k in fields)
            self.conn.execute(
                f"UPDATE book SET {assignments}, updated_at = datetime('now') "
                "WHERE book_id = ?",
                (*fields.values(), book_id),
            )

        # Authors (role 'author') — rebuild the junction rows.
        self.conn.execute(
            "DELETE FROM book_author WHERE book_id = ? AND role = 'author'",
            (book_id,),
        )
        for i, name in enumerate(d.get("authors") or [], start=1):
            aid = self._get_or_create_author(name)
            if aid:
                self.conn.execute(
                    "INSERT OR IGNORE INTO book_author"
                    "(book_id, author_id, role, author_order) VALUES(?, ?, 'author', ?)",
                    (book_id, aid, i),
                )

        # Narrators (role 'narrator') — optional, mostly for audiobooks.
        self.conn.execute(
            "DELETE FROM book_author WHERE book_id = ? AND role = 'narrator'",
            (book_id,),
        )
        for i, name in enumerate(d.get("narrators") or [], start=1):
            aid = self._get_or_create_author(name)
            if aid:
                self.conn.execute(
                    "INSERT OR IGNORE INTO book_author"
                    "(book_id, author_id, role, author_order) VALUES(?, ?, 'narrator', ?)",
                    (book_id, aid, i),
                )

        # Genres.
        self.conn.execute("DELETE FROM book_genre WHERE book_id = ?", (book_id,))
        for name in (d.get("genres") or []):
            gid = self._get_or_create_genre(name)
            if gid:
                self.conn.execute(
                    "INSERT OR IGNORE INTO book_genre(book_id, genre_id) VALUES(?, ?)",
                    (book_id, gid),
                )

        return book_id

    # ------------------------------------------------------------- book reads
    def list_books(
        self,
        search: Optional[str] = None,
        status: Optional[str] = None,
        fmt: Optional[str] = None,
    ) -> list[dict]:
        where, params = [], []
        if search and search.strip():
            ids = self._fts_ids(search.strip())
            if not ids:
                return []
            where.append(f"b.book_id IN ({', '.join('?' * len(ids))})")
            params += ids
        if status:
            where.append("b.read_status = ?")
            params.append(status)
        if fmt:
            where.append("b.format = ?")
            params.append(fmt)

        sql = f"""
            SELECT b.book_id, b.title, b.subtitle, b.format, b.read_status,
                   b.rating, b.publication_date, b.series_position,
                   COALESCE(GROUP_CONCAT(
                       CASE WHEN ba.role = 'author' THEN {_DISPLAY} END, ', '
                   ), '') AS authors,
                   s.name AS series
            FROM book b
            LEFT JOIN book_author ba ON ba.book_id = b.book_id
            LEFT JOIN author a       ON a.author_id = ba.author_id
            LEFT JOIN series s       ON s.series_id = b.series_id
        """
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " GROUP BY b.book_id ORDER BY b.title COLLATE NOCASE"
        return [dict(r) for r in self.conn.execute(sql, params)]

    def get_book(self, book_id: int) -> Optional[dict]:
        row = self.conn.execute(
            """
            SELECT b.*, p.name AS publisher, l.code AS language, s.name AS series
            FROM book b
            LEFT JOIN publisher p ON p.publisher_id = b.publisher_id
            LEFT JOIN language  l ON l.language_id  = b.language_id
            LEFT JOIN series    s ON s.series_id    = b.series_id
            WHERE b.book_id = ?
            """,
            (book_id,),
        ).fetchone()
        if not row:
            return None
        book = dict(row)
        book["authors"] = self._roles(book_id, "author")
        book["narrators"] = self._roles(book_id, "narrator")
        book["genres"] = [
            r["name"] for r in self.conn.execute(
                "SELECT g.name FROM genre g "
                "JOIN book_genre bg ON bg.genre_id = g.genre_id "
                "WHERE bg.book_id = ? ORDER BY g.name",
                (book_id,),
            )
        ]
        return book

    def _roles(self, book_id: int, role: str) -> list[str]:
        return [
            r["display"] for r in self.conn.execute(
                f"SELECT {_DISPLAY} AS display FROM author a "
                "JOIN book_author ba ON ba.author_id = a.author_id "
                "WHERE ba.book_id = ? AND ba.role = ? ORDER BY ba.author_order",
                (book_id, role),
            )
        ]

    # ------------------------------------------------------- reading journal
    def list_notes(self, book_id: int) -> list[dict]:
        return [
            dict(r) for r in self.conn.execute(
                "SELECT * FROM book_note WHERE book_id = ? "
                "ORDER BY note_date DESC, note_id DESC",
                (book_id,),
            )
        ]

    def add_note(self, book_id: int, entry_type: str, content: str) -> None:
        with self._lock:
            self.conn.execute(
                "INSERT INTO book_note(book_id, entry_type, content) VALUES(?, ?, ?)",
                (book_id, entry_type, content),
            )
            self.conn.commit()

    def delete_note(self, note_id: int) -> None:
        with self._lock:
            self.conn.execute(
                "DELETE FROM book_note WHERE note_id = ?", (note_id,)
            )
            self.conn.commit()

    # --------------------------------------------------------------- search
    def _fts_ids(self, query: str) -> list[int]:
        """Book ids matching the query across catalog + notes, best first."""
        match = self._fts_match(query)
        ids: list[int] = []
        seen: set[int] = set()
        try:
            catalog = self.conn.execute(
                "SELECT b.book_id FROM book_fts "
                "JOIN book b ON b.book_id = book_fts.rowid "
                "WHERE book_fts MATCH ? "
                "ORDER BY bm25(book_fts, 10.0, 4.0, 1.0, 6.0)",
                (match,),
            )
            for r in catalog:
                if r["book_id"] not in seen:
                    seen.add(r["book_id"])
                    ids.append(r["book_id"])
            notes = self.conn.execute(
                "SELECT n.book_id FROM note_fts "
                "JOIN book_note n ON n.note_id = note_fts.rowid "
                "WHERE note_fts MATCH ? ORDER BY rank",
                (match,),
            )
            for r in notes:
                if r["book_id"] not in seen:
                    seen.add(r["book_id"])
                    ids.append(r["book_id"])
        except sqlite3.OperationalError:
            # Malformed FTS expression — fall back to a forgiving LIKE scan.
            like = f"%{query}%"
            for r in self.conn.execute(
                "SELECT book_id FROM book "
                "WHERE title LIKE ? OR description LIKE ? OR review LIKE ?",
                (like, like, like),
            ):
                if r["book_id"] not in seen:
                    seen.add(r["book_id"])
                    ids.append(r["book_id"])
        return ids

    @staticmethod
    def _fts_match(query: str) -> str:
        """Turn free text into a safe FTS5 prefix query (implicit AND)."""
        tokens = re.findall(r"\w+", query, flags=re.UNICODE)
        if not tokens:
            return '""'
        return " ".join(f'"{t}"*' for t in tokens)

    def close(self) -> None:
        self.conn.close()
