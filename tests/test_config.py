"""Path resolution and data safety (DATA-001).

The library must live in the OS user-data directory, never inside the
source tree; the data directory honours HOLLOWSHELF_DATA_DIR; the schema
ships inside the package; and path handling survives spaces and non-ASCII
characters. The legacy `<repo>/data/library.db` import copies without
touching the original.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from hollowshelf import config
from hollowshelf.db import Database, copy_database

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def no_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(config.DATA_DIR_ENV, raising=False)


def test_default_paths_live_outside_the_source_tree(no_override: None) -> None:
    for path in (config.db_path(), config.cache_path(), config.storage_dir()):
        assert path.is_absolute()
        assert REPO_ROOT not in path.parents, f"{path} is inside the repo"


def test_default_data_dir_is_the_platform_user_dir(no_override: None) -> None:
    # Resolved via platformdirs: ~/.local/share/hollowshelf on Linux (XDG),
    # %LOCALAPPDATA%\hollowshelf on Windows.
    assert config.data_dir().name == "hollowshelf"
    assert config.db_path() == config.data_dir() / "library.db"
    assert config.storage_dir() == config.data_dir() / "storage"


def test_env_override_wins_and_handles_spaces_and_non_ascii(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    override = tmp_path / "Mein Bücher Regal" / "daten"
    monkeypatch.setenv(config.DATA_DIR_ENV, str(override))

    assert config.data_dir() == override
    assert config.db_path() == override / "library.db"
    # With an override active the cache moves under it too, so tests and
    # portable setups stay self-contained.
    assert config.cache_path() == override / "cache" / "book_cache.db"

    # The database actually works at such a path.
    db = Database(config.db_path(), config.schema_sql())
    try:
        book_id = db.create_book({"title": "Winterplanet", "authors": ["Le Guin"]})
        assert db.get_book(book_id)["title"] == "Winterplanet"
    finally:
        db.close()


def test_schema_ships_inside_the_package(no_override: None) -> None:
    sql = config.schema_sql()
    assert "CREATE TABLE" in sql and "book" in sql
    # It really is package data, not a file resolved relative to the repo root.
    assert not (REPO_ROOT / "collection_schema.sql").exists()


def test_legacy_import_copies_without_touching_the_original(tmp_path: Path) -> None:
    legacy = tmp_path / "old" / "library.db"
    source = Database(legacy, config.schema_sql())
    book_id = source.create_book({"title": "The Dispossessed", "authors": ["Le Guin"]})
    source.close()
    before = legacy.read_bytes()

    dest = tmp_path / "new" / "library.db"
    copy_database(legacy, dest)

    imported = Database(dest, config.schema_sql())
    try:
        assert imported.get_book(book_id)["title"] == "The Dispossessed"
    finally:
        imported.close()
    assert legacy.read_bytes() == before
