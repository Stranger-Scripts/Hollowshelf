"""The normalized result shape every provider returns.

This is the only object the rest of the app needs to know about — each provider
maps its own JSON into a ``BookResult`` so the UI never sees provider-specific
shapes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


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
    source: str = ""                        # provider name, e.g. "openlibrary"
