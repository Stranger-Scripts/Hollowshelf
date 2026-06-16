"""
book_client.py — Free book & audiobook metadata lookup for German/English titles.

Sources (all free — no API key, no billing, no signup):
  - Open Library  (primary: good DE/EN coverage, covers + some audiobook editions)
  - Google Books  (fallback / enrichment: strong descriptions and page counts)

Search by ISBN or by title (optionally author + language). Every result is
normalized into a single `BookResult` shape and cached in a local SQLite file so
you never re-fetch the same lookup (this is what keeps you well under any
informal rate limits).

Open Library asks that apps identify themselves via a descriptive User-Agent
that includes a contact address. Hollowshelf builds that header from the name
and email the user enters on first run — see ``BookClient`` below.

Dependency:  pip install httpx
"""

from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import dataclass, field
from typing import Optional

import httpx


# --------------------------------------------------------------------------- #
#  Normalized result shape — the only object the rest of your app needs to know
# --------------------------------------------------------------------------- #

@dataclass
class BookResult:
    title: str
    authors: list[str] = field(default_factory=list)
    isbn_13: Optional[str] = None
    isbn_10: Optional[str] = None
    year: Optional[int] = None
    publisher: Optional[str] = None
    language: Optional[str] = None          # ISO code, e.g. "de" / "en"
    cover_url: Optional[str] = None
    description: Optional[str] = None
    page_count: Optional[int] = None
    media: str = "unknown"                  # print | ebook | audiobook | unknown
    source: str = ""                        # openlibrary | google_books


# --------------------------------------------------------------------------- #
#  Language code mapping (your input uses ISO; the APIs disagree on format)
# --------------------------------------------------------------------------- #

_LANG_OL = {"de": "ger", "en": "eng", "ger": "ger", "eng": "eng"}   # Open Library = MARC
_LANG_GB = {"de": "de", "en": "en", "ger": "de", "eng": "en"}       # Google Books = ISO-1


# --------------------------------------------------------------------------- #
#  Best-effort media detection. Free metadata is unreliable here, so treat this
#  as a hint only and let users correct it in the UI.
# --------------------------------------------------------------------------- #

_AUDIO_HINTS = ("audio", "hörbuch", "hoerbuch", "audible", "mp3", "spoken", "cd")
_EBOOK_HINTS = ("ebook", "e-book", "kindle", "epub", "electronic")
_PRINT_HINTS = ("paperback", "hardcover", "hardback", "taschenbuch", "gebunden", "print")


def _detect_media(*hints: Optional[str]) -> str:
    blob = " ".join(h for h in hints if h).lower()
    if any(k in blob for k in _AUDIO_HINTS):
        return "audiobook"
    if any(k in blob for k in _EBOOK_HINTS):
        return "ebook"
    if any(k in blob for k in _PRINT_HINTS):
        return "print"
    return "unknown"


# --------------------------------------------------------------------------- #
#  Tiny SQLite response cache (TTL in days)
# --------------------------------------------------------------------------- #

class _Cache:
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


# --------------------------------------------------------------------------- #
#  The client
# --------------------------------------------------------------------------- #

class BookClient:
    """Metadata client.

    The ``app_name``/``app_version``/``contact`` arguments build the User-Agent
    Open Library asks for, e.g. ``"Hollowshelf/0.1.0 (contact: me@example.com)"``.
    Hollowshelf passes the email the user entered on first run as ``contact``.
    """

    def __init__(
        self,
        cache_path: str = "book_cache.db",
        cache_ttl_days: int = 30,
        app_name: str = "Hollowshelf",
        app_version: str = "0.1.0",
        contact: Optional[str] = None,
    ):
        user_agent = f"{app_name}/{app_version}"
        if contact:
            user_agent += f" (contact: {contact})"
        self.user_agent = user_agent

        self._http = httpx.Client(
            headers={"User-Agent": user_agent},
            timeout=10.0,
            follow_redirects=True,
        )
        self._cache = _Cache(cache_path, cache_ttl_days)

    def close(self) -> None:
        self._http.close()

    # -- internal: cached GET returning JSON (None on any failure) ----------- #

    def _get_json(self, url: str, params: Optional[dict] = None) -> Optional[dict]:
        key = url + "|" + json.dumps(params or {}, sort_keys=True)
        cached = self._cache.get(key)
        if cached is not None:
            return cached
        try:
            r = self._http.get(url, params=params)
            r.raise_for_status()
            data = r.json()
        except (httpx.HTTPError, ValueError):
            return None
        self._cache.set(key, data)
        return data

    # ----------------------------------------------------------------------- #
    #  Public API
    # ----------------------------------------------------------------------- #

    def search_by_isbn(self, isbn: str) -> Optional[BookResult]:
        """Look up a single edition by ISBN-10 or ISBN-13."""
        isbn = isbn.replace("-", "").replace(" ", "").strip()
        result = self._ol_by_isbn(isbn)
        if result is None:
            result = self._gb_by_isbn(isbn)
        elif not result.description:
            # Enrich a thin Open Library record with a Google Books description.
            gb = self._gb_by_isbn(isbn)
            if gb:
                result.description = gb.description
                result.page_count = result.page_count or gb.page_count
        return result

    def search_by_title(
        self,
        title: str,
        author: Optional[str] = None,
        language: Optional[str] = None,   # "de" / "en"
        limit: int = 10,
    ) -> list[BookResult]:
        """Search by title, returning a ranked list of candidates."""
        results = self._ol_search(title, author, language, limit)
        if results:
            return results
        return self._gb_search(title, author, language, limit)

    # ----------------------------------------------------------------------- #
    #  Open Library
    # ----------------------------------------------------------------------- #

    def _ol_by_isbn(self, isbn: str) -> Optional[BookResult]:
        # The edition endpoint exposes `physical_format`, which is the one place
        # an audiobook ("Audio CD", "Audible Audio Edition") is actually flagged.
        data = self._get_json(f"https://openlibrary.org/isbn/{isbn}.json")
        if not data:
            return None

        authors = self._ol_resolve_authors(data.get("authors", []))
        langs = data.get("languages", [])
        lang_code = langs[0]["key"].split("/")[-1] if langs else None
        cover = data.get("covers", [None])[0]

        return BookResult(
            title=data.get("title", "Unknown"),
            authors=authors,
            isbn_13=(data.get("isbn_13") or [None])[0],
            isbn_10=(data.get("isbn_10") or [None])[0],
            year=_year(data.get("publish_date")),
            publisher=(data.get("publishers") or [None])[0],
            language={"ger": "de", "eng": "en"}.get(lang_code, lang_code),
            cover_url=(f"https://covers.openlibrary.org/b/id/{cover}-L.jpg"
                       if cover else None),
            description=_text(data.get("description")),
            page_count=data.get("number_of_pages"),
            media=_detect_media(data.get("physical_format"), data.get("title")),
            source="openlibrary",
        )

    def _ol_resolve_authors(self, raw: list) -> list[str]:
        names = []
        for a in raw:
            akey = a.get("key") if isinstance(a, dict) else None
            if not akey:
                continue
            adata = self._get_json(f"https://openlibrary.org{akey}.json")
            if adata and adata.get("name"):
                names.append(adata["name"])
        return names

    def _ol_search(self, title, author, language, limit) -> list[BookResult]:
        params = {
            "title": title,
            "limit": limit,
            "fields": ("title,author_name,first_publish_year,isbn,publisher,"
                       "language,cover_i,number_of_pages_median,format"),
        }
        if author:
            params["author"] = author
        if language and language in _LANG_OL:
            params["language"] = _LANG_OL[language]

        data = self._get_json("https://openlibrary.org/search.json", params)
        if not data or not data.get("docs"):
            return []

        out = []
        for d in data["docs"]:
            cover_i = d.get("cover_i")
            fmt = d.get("format")
            fmt_hint = " ".join(fmt) if isinstance(fmt, list) else fmt
            out.append(BookResult(
                title=d.get("title", "Unknown"),
                authors=d.get("author_name", []),
                isbn_13=(d.get("isbn") or [None])[0],
                year=d.get("first_publish_year"),
                publisher=(d.get("publisher") or [None])[0],
                cover_url=(f"https://covers.openlibrary.org/b/id/{cover_i}-L.jpg"
                           if cover_i else None),
                page_count=d.get("number_of_pages_median"),
                media=_detect_media(fmt_hint, d.get("title")),
                source="openlibrary",
            ))
        return out

    # ----------------------------------------------------------------------- #
    #  Google Books
    # ----------------------------------------------------------------------- #

    def _gb_by_isbn(self, isbn: str) -> Optional[BookResult]:
        data = self._get_json(
            "https://www.googleapis.com/books/v1/volumes",
            {"q": f"isbn:{isbn}"},
        )
        items = (data or {}).get("items")
        return self._gb_normalize(items[0]) if items else None

    def _gb_search(self, title, author, language, limit) -> list[BookResult]:
        q = f'intitle:{title}'
        if author:
            q += f'+inauthor:{author}'
        params = {"q": q, "maxResults": min(limit, 40)}
        if language and language in _LANG_GB:
            params["langRestrict"] = _LANG_GB[language]
        data = self._get_json(
            "https://www.googleapis.com/books/v1/volumes", params
        )
        return [self._gb_normalize(it) for it in (data or {}).get("items", [])]

    def _gb_normalize(self, item: dict) -> BookResult:
        info = item.get("volumeInfo", {})
        ids = {x["type"]: x["identifier"]
               for x in info.get("industryIdentifiers", [])}
        images = info.get("imageLinks", {})
        return BookResult(
            title=info.get("title", "Unknown"),
            authors=info.get("authors", []),
            isbn_13=ids.get("ISBN_13"),
            isbn_10=ids.get("ISBN_10"),
            year=_year(info.get("publishedDate")),
            publisher=info.get("publisher"),
            language=info.get("language"),
            cover_url=(images.get("thumbnail") or "").replace("http://", "https://") or None,
            description=info.get("description"),
            page_count=info.get("pageCount"),
            media=_detect_media(info.get("title"), info.get("subtitle")),
            source="google_books",
        )


# --------------------------------------------------------------------------- #
#  Helpers
# --------------------------------------------------------------------------- #

def _year(date_str: Optional[str]) -> Optional[int]:
    if not date_str:
        return None
    for token in str(date_str).replace("-", " ").split():
        if token.isdigit() and len(token) == 4:
            return int(token)
    return None


def _text(value) -> Optional[str]:
    # Open Library descriptions are sometimes {"type": ..., "value": "..."}.
    if isinstance(value, dict):
        return value.get("value")
    return value


# --------------------------------------------------------------------------- #
#  Example usage
# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    client = BookClient(contact="you@example.com")

    book = client.search_by_isbn("9783866470117")   # German edition
    print(book)

    for hit in client.search_by_title("Der Vorleser", language="de", limit=3):
        print(f"{hit.title} — {', '.join(hit.authors)} ({hit.year}) [{hit.media}]")

    client.close()
