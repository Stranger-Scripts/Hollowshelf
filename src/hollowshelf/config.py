"""Filesystem paths and app-wide constants.

User data lives in the OS per-user directories (DATA-001), resolved with
``platformdirs``, so the library can never be lost to a `git clean -fdx`:

| What                             | Linux (XDG)                   | Windows                            |
|----------------------------------|-------------------------------|------------------------------------|
| library.db, backups, UI storage  | ``~/.local/share/hollowshelf``| ``%LOCALAPPDATA%\\hollowshelf``    |
| book_cache.db                    | ``~/.cache/hollowshelf``      | ``%LOCALAPPDATA%\\hollowshelf\\Cache`` |

The data directory can be overridden with ``HOLLOWSHELF_DATA_DIR`` or the
``--data-dir`` CLI flag (the flag wins by setting the variable; an environment
variable survives the window subprocess that native mode spawns, a module
global would not). With an override active the cache moves under it too, so
tests and portable setups stay self-contained.

The schema ships inside the package and is read with ``importlib.resources``.
Paths are resolved fresh on every call, never cached at import time, so tests
can monkeypatch the environment.
"""

from __future__ import annotations

import os
from importlib import resources
from pathlib import Path

import platformdirs

from . import __version__

APP_NAME = "Hollowshelf"
APP_VERSION = __version__

# Lowercase on purpose: XDG directory names are conventionally lowercase.
_DIR_NAME = "hollowshelf"

DATA_DIR_ENV = "HOLLOWSHELF_DATA_DIR"


def data_dir() -> Path:
    """Directory holding the library, backups and the UI storage."""
    override = os.environ.get(DATA_DIR_ENV)
    if override:
        return Path(override).expanduser()
    return platformdirs.user_data_path(_DIR_NAME, appauthor=False)


def cache_dir() -> Path:
    """Directory for the disposable API cache."""
    if os.environ.get(DATA_DIR_ENV):
        return data_dir() / "cache"
    return platformdirs.user_cache_path(_DIR_NAME, appauthor=False)


def db_path() -> Path:
    return data_dir() / "library.db"


def cache_path() -> Path:
    return cache_dir() / "book_cache.db"


def storage_dir() -> Path:
    """NiceGUI's per-user storage (holds e.g. the UI language choice)."""
    return data_dir() / "storage"


def schema_sql() -> str:
    """The SQLite + FTS5 schema, shipped as package data."""
    return (resources.files("hollowshelf") / "collection_schema.sql").read_text(
        encoding="utf-8"
    )


def legacy_db_path() -> Path | None:
    """A pre-DATA-001 ``<repo>/data/library.db``, when running from a checkout.

    Installed wheels have no project root around the package, so the
    ``pyproject.toml`` probe keeps this from pointing into ``site-packages``.
    """
    root = Path(__file__).resolve().parents[2]
    if (root / "pyproject.toml").is_file():
        legacy = root / "data" / "library.db"
        if legacy.is_file():
            return legacy
    return None


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
