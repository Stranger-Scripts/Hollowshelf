"""Shared application state: the database handle and a lazily-built API client.

The metadata client is rebuilt whenever the saved contact email changes, so the
Open Library User-Agent always carries the address the user entered.
"""

from __future__ import annotations

from typing import Optional

from . import config
from .book_client import BookClient
from .db import Database

db: Database  # set by app.main()

_client: Optional[BookClient] = None
_client_signature: Optional[tuple] = None


def _build_options() -> dict:
    """Provider options: env defaults, overridden by anything saved in the UI."""
    opts = config.book_client_options()
    api_key = (db.get_setting("google_books_api_key", "") or "").strip()
    if api_key:
        opts["google_api_key"] = api_key
    return opts


def get_client() -> BookClient:
    """Return a metadata client, rebuilt when the email or provider options change."""
    global _client, _client_signature
    contact = db.get_profile().get("email") or None
    options = _build_options()
    signature = (contact, tuple(sorted(options.items())))
    if _client is None or signature != _client_signature:
        if _client is not None:
            _client.close()
        _client = BookClient(
            cache_path=str(config.CACHE_PATH),
            app_name=config.APP_NAME,
            app_version=config.APP_VERSION,
            contact=contact,
            options=options,
        )
        _client_signature = signature
    return _client
