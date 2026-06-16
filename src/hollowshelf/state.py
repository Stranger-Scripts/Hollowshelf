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
_client_contact: Optional[str] = None


def get_client() -> BookClient:
    """Return a metadata client whose User-Agent uses the saved email."""
    global _client, _client_contact
    contact = db.get_profile().get("email") or None
    if _client is None or contact != _client_contact:
        if _client is not None:
            _client.close()
        _client = BookClient(
            cache_path=str(config.CACHE_PATH),
            app_name=config.APP_NAME,
            app_version=config.APP_VERSION,
            contact=contact,
        )
        _client_contact = contact
    return _client
