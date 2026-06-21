"""Filesystem paths and app-wide constants.

Everything lives under the project root so a personal copy stays self-contained.
The SQLite databases are kept in a ``data/`` folder (git-ignored); the schema
file is the one you already authored at the project root.
"""

from __future__ import annotations

import os
from pathlib import Path

from . import __version__

# config.py -> hollowshelf -> src -> <project root>
PROJECT_ROOT = Path(__file__).resolve().parents[2]

SCHEMA_PATH = PROJECT_ROOT / "collection_schema.sql"

DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "library.db"
CACHE_PATH = DATA_DIR / "book_cache.db"

APP_NAME = "Hollowshelf"
APP_VERSION = __version__

# Optional Google Books settings. Keyless access shares a small daily quota and
# returns HTTP 429 once it's spent; set HOLLOWSHELF_GOOGLE_BOOKS_API_KEY to use
# your own key. HOLLOWSHELF_GOOGLE_BOOKS_COUNTRY (e.g. "DE", "US") helps in
# regions where Google Books otherwise returns no items.
GOOGLE_BOOKS_API_KEY = os.environ.get("HOLLOWSHELF_GOOGLE_BOOKS_API_KEY") or None
GOOGLE_BOOKS_COUNTRY = os.environ.get("HOLLOWSHELF_GOOGLE_BOOKS_COUNTRY") or None


def book_client_options() -> dict:
    """Provider options forwarded to ``BookClient`` (drops unset values)."""
    opts = {
        "google_api_key": GOOGLE_BOOKS_API_KEY,
        "google_country": GOOGLE_BOOKS_COUNTRY,
    }
    return {k: v for k, v in opts.items() if v}
