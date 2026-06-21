"""Open Library metadata provider.

Primary source: good German/English coverage, covers, and — via the edition
endpoint's ``physical_format`` — the one place an audiobook edition is actually
flagged. Open Library asks that apps identify themselves with a descriptive
User-Agent; that header is set on the shared client by ``BookClient``.
"""

from __future__ import annotations

from typing import Optional

from ._util import parse_year
from .base import MetadataProvider
from .media import detect_media
from .models import BookResult

# Open Library speaks MARC language codes, not ISO-1.
_LANG_OL = {"de": "ger", "en": "eng", "ger": "ger", "eng": "eng"}
_MARC_TO_ISO = {"ger": "de", "eng": "en"}


class OpenLibraryClient(MetadataProvider):
    name = "openlibrary"

    def by_isbn(self, isbn: str) -> Optional[BookResult]:
        # The edition endpoint exposes `physical_format`, which is the one place
        # an audiobook ("Audio CD", "Audible Audio Edition") is actually flagged.
        data = self._get_json(f"https://openlibrary.org/isbn/{isbn}.json")
        if not data:
            return None

        authors = self._resolve_authors(data.get("authors", []))
        langs = data.get("languages", [])
        lang_code = langs[0]["key"].split("/")[-1] if langs else None
        cover = data.get("covers", [None])[0]

        return BookResult(
            title=data.get("title", "Unknown"),
            authors=authors,
            isbn_13=(data.get("isbn_13") or [None])[0],
            isbn_10=(data.get("isbn_10") or [None])[0],
            year=parse_year(data.get("publish_date")),
            publisher=(data.get("publishers") or [None])[0],
            language=_MARC_TO_ISO.get(lang_code, lang_code),
            cover_url=(f"https://covers.openlibrary.org/b/id/{cover}-L.jpg"
                       if cover else None),
            description=_text(data.get("description")),
            page_count=data.get("number_of_pages"),
            media=detect_media(data.get("physical_format"), data.get("title")),
            source=self.name,
        )

    def search(self, title, author, language, limit) -> list[BookResult]:
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
                media=detect_media(fmt_hint, d.get("title")),
                source=self.name,
            ))
        return out

    def _resolve_authors(self, raw: list) -> list[str]:
        names = []
        for a in raw:
            akey = a.get("key") if isinstance(a, dict) else None
            if not akey:
                continue
            adata = self._get_json(f"https://openlibrary.org{akey}.json")
            if adata and adata.get("name"):
                names.append(adata["name"])
        return names


def _text(value) -> Optional[str]:
    # Open Library descriptions are sometimes {"type": ..., "value": "..."}.
    if isinstance(value, dict):
        return value.get("value")
    return value
