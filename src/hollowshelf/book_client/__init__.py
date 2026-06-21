"""book_client — free book & audiobook metadata lookup for DE/EN titles.

Sources (free — Google Books optionally takes an API key for a larger quota):
  - Open Library  (good DE/EN coverage, covers + audiobook flags)
  - Google Books  (strong descriptions and page counts)

Search by ISBN or by title (optionally author + language). Every provider is
queried and the results are merged: duplicate books are collapsed onto the
highest-priority copy and unique hits from each source are kept. Every result is
normalized into a single ``BookResult`` and cached in a local SQLite file.

Module map (one concern per file, so a new source is easy to bolt on):
  - models.py        the ``BookResult`` shape every provider returns
  - cache.py         the SQLite TTL response cache
  - base.py          ``MetadataProvider`` — the per-source contract
  - openlibrary.py   the Open Library provider
  - google_books.py  the Google Books provider
  - media.py         shared print/ebook/audiobook detection
  - client.py        ``BookClient`` — queries every provider and merges results

Adding a provider: subclass ``MetadataProvider`` in a new module, then pass it
via ``BookClient(providers=[...])``. Per-source settings (API keys, country, …)
flow through ``BookClient(options={...})`` to every provider.

The public surface (``BookClient`` and ``BookResult``) is unchanged from the
previous single-module version, so existing imports keep working.
"""

from __future__ import annotations

from .base import MetadataProvider
from .client import BookClient
from .google_books import GoogleBooksClient
from .models import BookResult
from .openlibrary import OpenLibraryClient

__all__ = [
    "BookClient",
    "BookResult",
    "MetadataProvider",
    "OpenLibraryClient",
    "GoogleBooksClient",
]
