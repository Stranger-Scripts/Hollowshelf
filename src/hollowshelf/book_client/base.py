"""The contract every metadata source implements.

To add a new source (e.g. Deutsche Nationalbibliothek, WorldCat), subclass
``MetadataProvider``, set a ``name``, and implement ``by_isbn`` and ``search``.
The shared ``httpx`` client (carrying the User-Agent) and the SQLite cache are
injected by the orchestrating ``BookClient``, so providers only describe *how*
to query and *how* to map the response into a ``BookResult``.
"""

from __future__ import annotations

import json
import logging
from typing import Optional

import httpx

from .cache import Cache
from .models import BookResult

log = logging.getLogger(__name__)


class MetadataProvider:
    name: str = "provider"

    def __init__(
        self,
        http: httpx.Client,
        cache: Cache,
        options: Optional[dict] = None,
    ):
        self._http = http
        self._cache = cache
        # Free-form per-source config (API keys, country, …). Each provider
        # reads the keys it cares about and ignores the rest, so adding a
        # source that needs its own settings doesn't touch the orchestrator.
        self._options = options or {}

    # -- shared: cached GET returning JSON (None on any failure) ------------- #

    def _get_json(self, url: str, params: Optional[dict] = None) -> Optional[dict]:
        key = url + "|" + json.dumps(params or {}, sort_keys=True)
        cached = self._cache.get(key)
        if cached is not None:
            return cached
        try:
            r = self._http.get(url, params=params)
            r.raise_for_status()
            data = r.json()
        except httpx.HTTPStatusError as exc:
            # 404 just means "this source has no record" — normal during
            # fallback, so keep it quiet. Everything else (429 rate-limit,
            # 5xx, …) is worth surfacing. ``params`` is never logged: it can
            # carry an API key.
            if exc.response.status_code == 404:
                log.debug("%s: not found (%s)", self.name, url)
            else:
                log.warning("%s request failed: HTTP %s (%s)",
                            self.name, exc.response.status_code, url)
            return None
        except (httpx.HTTPError, ValueError) as exc:
            log.warning("%s request failed: %s (%s)", self.name, exc, url)
            return None
        self._cache.set(key, data)
        return data

    # -- to implement in each provider -------------------------------------- #

    def by_isbn(self, isbn: str) -> Optional[BookResult]:
        """Look up a single edition by a normalized ISBN-10/13."""
        raise NotImplementedError

    def search(
        self,
        title: str,
        author: Optional[str],
        language: Optional[str],   # "de" / "en"
        limit: int,
    ) -> list[BookResult]:
        """Search by title, returning a ranked list of candidates."""
        raise NotImplementedError
