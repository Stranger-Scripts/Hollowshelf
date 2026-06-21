"""The orchestrating client that fans queries out across providers.

``BookClient`` owns the shared HTTP client (and its User-Agent) and the SQLite
cache, then drives an ordered list of providers. Every provider is queried and
the results are merged: duplicates of the same book are collapsed into one
(filling missing fields from lower-priority sources), and unique hits from each
source are kept. Order = priority — a higher-priority provider's values win when
two sources describe the same book.

Swap or extend the sources via ``providers``; per-source settings (API keys,
etc.) flow through ``options`` to every provider.
"""

from __future__ import annotations

from itertools import zip_longest
from typing import Optional

import httpx

from .base import MetadataProvider
from .cache import Cache
from .google_books import GoogleBooksClient
from .models import BookResult
from .openlibrary import OpenLibraryClient

# Order = priority. Open Library first (good DE/EN + audiobook flags), Google
# Books second (richer descriptions, broader fallback).
DEFAULT_PROVIDERS: tuple[type[MetadataProvider], ...] = (
    OpenLibraryClient,
    GoogleBooksClient,
)

# Fields copied from a lower-priority duplicate into the kept result when the
# kept result is missing them.
_ENRICH_FIELDS = (
    "authors", "isbn_13", "isbn_10", "year", "publisher",
    "language", "cover_url", "description", "page_count",
)


class BookClient:
    """Metadata client combining one or more providers.

    The ``app_name``/``app_version``/``contact`` arguments build the User-Agent
    Open Library asks for, e.g. ``"Hollowshelf/0.1.0 (contact: me@example.com)"``.
    Hollowshelf passes the email the user entered on first run as ``contact``.

    ``providers`` (a list of ``MetadataProvider`` subclasses) changes the sources
    or their priority; defaults to Open Library then Google Books.

    ``options`` is a free-form dict forwarded to every provider. Recognized keys:
      - ``google_api_key``  raise the Google Books quota above the keyless limit
      - ``google_country``  ISO country code some regions need for Google Books
    """

    def __init__(
        self,
        cache_path: str = "book_cache.db",
        cache_ttl_days: int = 30,
        app_name: str = "Hollowshelf",
        app_version: str = "0.1.0",
        contact: Optional[str] = None,
        providers: Optional[list[type[MetadataProvider]]] = None,
        options: Optional[dict] = None,
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
        self._cache = Cache(cache_path, cache_ttl_days)
        self._options = options or {}
        self.providers: list[MetadataProvider] = [
            cls(self._http, self._cache, self._options)
            for cls in (providers or DEFAULT_PROVIDERS)
        ]

    def close(self) -> None:
        self._http.close()

    # ----------------------------------------------------------------------- #
    #  Public API
    # ----------------------------------------------------------------------- #

    def search_by_isbn(self, isbn: str) -> Optional[BookResult]:
        """Look up a single edition by ISBN-10 or ISBN-13.

        Every provider is queried; the highest-priority hit becomes the result
        and lower-priority hits fill in any fields it's missing (description,
        page count, cover, …).
        """
        isbn = isbn.replace("-", "").replace(" ", "").strip()
        primary: Optional[BookResult] = None
        for provider in self.providers:
            res = provider.by_isbn(isbn)
            if res is None:
                continue
            if primary is None:
                primary = res
            else:
                _enrich(primary, res)
        return primary

    def search_by_title(
        self,
        title: str,
        author: Optional[str] = None,
        language: Optional[str] = None,   # "de" / "en"
        limit: int = 10,
    ) -> list[BookResult]:
        """Search every provider and return a merged, de-duplicated candidate list.

        Results are interleaved across sources (round-robin) so each provider is
        represented within the ``limit``, and duplicates of the same book are
        collapsed onto the highest-priority copy.
        """
        per_provider = [
            provider.search(title, author, language, limit)
            for provider in self.providers
        ]
        return _merge(per_provider, limit)


# --------------------------------------------------------------------------- #
#  Merge / de-duplication across sources
# --------------------------------------------------------------------------- #

def _merge(result_lists: list[list[BookResult]], limit: int) -> list[BookResult]:
    merged: list[BookResult] = []
    seen: dict[tuple, int] = {}
    for group in zip_longest(*result_lists):  # one result per source, per rank
        for res in group:
            if res is None:
                continue
            key = _dedupe_key(res)
            if key in seen:
                _enrich(merged[seen[key]], res)
                continue
            seen[key] = len(merged)
            merged.append(res)
            if len(merged) >= limit:
                return merged
    return merged


def _dedupe_key(res: BookResult) -> tuple:
    title = (res.title or "").strip().lower()
    if res.authors:
        return (title, res.authors[0].strip().lower())
    # No author to disambiguate — fall back to the year so two different books
    # that merely share a title aren't collapsed together.
    return (title, res.year)


def _enrich(keep: BookResult, other: BookResult) -> None:
    for fld in _ENRICH_FIELDS:
        if not getattr(keep, fld):
            setattr(keep, fld, getattr(other, fld))
    if keep.media == "unknown" and other.media != "unknown":
        keep.media = other.media
