"""Filesystem paths and app-wide constants.

Everything lives under the project root so a personal copy stays self-contained.
The SQLite databases are kept in a ``data/`` folder (git-ignored); the schema
file is the one you already authored at the project root.
"""

from __future__ import annotations

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
