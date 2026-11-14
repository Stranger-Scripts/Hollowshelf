"""Shared fixtures.

Every test gets its own throwaway database, initialised from the real
``collection_schema.sql`` so the fixture also proves the shipped schema
still applies cleanly.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest

from hollowshelf.config import SCHEMA_PATH
from hollowshelf.db import Database


@pytest.fixture
def db(tmp_path: Path) -> Iterator[Database]:
    database = Database(tmp_path / "library.db", SCHEMA_PATH)
    yield database
    database.close()
