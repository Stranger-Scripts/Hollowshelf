"""Google Books metadata provider.

Used as a fallback when Open Library has nothing, and to enrich thin Open
Library records — Google Books tends to carry stronger descriptions and page
counts.
"""

from __future__ import annotations

from typing import Optional

from ._util import parse_year
from .base import MetadataProvider
from .media import detect_media
from .models import BookResult

_VOLUMES_URL = "https://www.googleapis.com/books/v1/volumes"

# Google Books speaks ISO-1 language codes.
_LANG_GB = {"de": "de", "en": "en", "ger": "de", "eng": "en"}


class GoogleBooksClient(MetadataProvider):
    name = "google_books"

    def by_isbn(self, isbn: str) -> Optional[BookResult]:
        data = self._get_json(_VOLUMES_URL, self._params({"q": f"isbn:{isbn}"}))
        items = (data or {}).get("items")
        return self._normalize(items[0]) if items else None

    def search(self, title, author, language, limit) -> list[BookResult]:
        q = f"intitle:{title}"
        if author:
            q += f"+inauthor:{author}"
        params = {"q": q, "maxResults": min(limit, 40)}
        if language and language in _LANG_GB:
            params["langRestrict"] = _LANG_GB[language]
        data = self._get_json(_VOLUMES_URL, self._params(params))
        return [self._normalize(it) for it in (data or {}).get("items", [])]

    def _params(self, params: dict) -> dict:
        # Keyless access shares a small daily quota and 429s easily; supplying
        # ``google_api_key`` gives a real per-project quota. ``google_country``
        # is needed in some regions or the API returns no items.
        out = dict(params)
        if key := self._options.get("google_api_key"):
            out["key"] = key
        if country := self._options.get("google_country"):
            out["country"] = country
        return out

    def _normalize(self, item: dict) -> BookResult:
        info = item.get("volumeInfo", {})
        ids = {x["type"]: x["identifier"]
               for x in info.get("industryIdentifiers", [])}
        images = info.get("imageLinks", {})
        return BookResult(
            title=info.get("title", "Unknown"),
            authors=info.get("authors", []),
            isbn_13=ids.get("ISBN_13"),
            isbn_10=ids.get("ISBN_10"),
            year=parse_year(info.get("publishedDate")),
            publisher=info.get("publisher"),
            language=info.get("language"),
            cover_url=(images.get("thumbnail") or "").replace("http://", "https://") or None,
            description=info.get("description"),
            page_count=info.get("pageCount"),
            media=detect_media(info.get("title"), info.get("subtitle")),
            source=self.name,
        )
