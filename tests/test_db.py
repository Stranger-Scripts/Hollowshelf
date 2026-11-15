"""Smoke test for the SQLite layer (NFR-006).

Covers the path the UI actually walks: a fresh database initialises from
the schema file, a book round-trips through the lookup upserts, FTS5
search reaches both the catalog and the reading journal, and deleting a
book takes its junction rows with it.
"""

from __future__ import annotations

from pathlib import Path

from hollowshelf.config import SCHEMA_PATH
from hollowshelf.db import Database

BOOK = {
    "title": "The Left Hand of Darkness",
    "subtitle": "A Novel",
    "isbn13": "9780441478125",
    "format": "physical",
    "publisher": "Ace Books",
    "language": "en",
    "series": "Hainish Cycle",
    "series_position": 4,
    "page_count": 304,
    "read_status": "read",
    "rating": 5,
    "authors": ["Ursula K. Le Guin"],
    "genres": ["Science Fiction", "Classics"],
    "description": "Winter is a planet without gender.",
}


# ----------------------------------------------------------------- setup
def test_fresh_database_initialises_schema(tmp_path: Path) -> None:
    db = Database(tmp_path / "nested" / "library.db", SCHEMA_PATH)
    try:
        tables = {
            row["name"]
            for row in db.conn.execute(
                "SELECT name FROM sqlite_master WHERE type IN ('table', 'view')"
            )
        }
        assert {"book", "author", "genre", "book_note", "app_settings"} <= tables
        assert db.path.exists()
    finally:
        db.close()


def test_reopening_keeps_existing_data(tmp_path: Path) -> None:
    path = tmp_path / "library.db"
    first = Database(path, SCHEMA_PATH)
    book_id = first.create_book(BOOK)
    first.close()

    second = Database(path, SCHEMA_PATH)
    try:
        assert second.get_book(book_id) is not None
    finally:
        second.close()


# -------------------------------------------------------------- settings
def test_profile_round_trips(db: Database) -> None:
    assert not db.is_configured()

    db.set_profile("  Ada Lovelace  ", " ada@example.com ")

    assert db.get_profile() == {"name": "Ada Lovelace", "email": "ada@example.com"}
    assert db.is_configured()


def test_setting_overwrites_on_conflict(db: Database) -> None:
    db.set_setting("ui_language", "en")
    db.set_setting("ui_language", "de")

    assert db.get_setting("ui_language") == "de"
    assert db.get_setting("missing", "fallback") == "fallback"


# ------------------------------------------------------------- book CRUD
def test_create_and_read_book(db: Database) -> None:
    book_id = db.create_book(BOOK)

    book = db.get_book(book_id)
    assert book is not None
    assert book["title"] == "The Left Hand of Darkness"
    assert book["authors"] == ["Ursula K. Le Guin"]
    assert book["genres"] == ["Classics", "Science Fiction"]  # ORDER BY g.name
    assert book["publisher"] == "Ace Books"
    assert book["language"] == "en"
    assert book["series"] == "Hainish Cycle"
    assert book["series_position"] == 4.0
    assert book["page_count"] == 304


def test_blank_fields_become_null(db: Database) -> None:
    book_id = db.create_book(
        {"title": "   ", "subtitle": "", "page_count": "", "rating": "nonsense"}
    )

    book = db.get_book(book_id)
    assert book is not None
    assert book["title"] == "Untitled"  # the schema requires a title
    assert book["subtitle"] is None
    assert book["page_count"] is None
    assert book["rating"] is None
    assert book["read_status"] == "unread"
    assert book["format"] == "physical"


def test_update_book_replaces_authors_and_genres(db: Database) -> None:
    book_id = db.create_book(BOOK)

    db.update_book(
        book_id,
        {**BOOK, "title": "A Wizard of Earthsea", "genres": ["Fantasy"]},
    )

    book = db.get_book(book_id)
    assert book is not None
    assert book["title"] == "A Wizard of Earthsea"
    assert book["genres"] == ["Fantasy"]
    assert book["authors"] == ["Ursula K. Le Guin"]  # unchanged, not duplicated


def test_authors_are_reused_across_books(db: Database) -> None:
    db.create_book(BOOK)
    db.create_book({**BOOK, "title": "The Dispossessed"})

    authors = db.conn.execute("SELECT COUNT(*) AS n FROM author").fetchone()
    assert authors["n"] == 1


def test_narrators_and_authors_stay_separate(db: Database) -> None:
    book_id = db.create_book(
        {
            **BOOK,
            "format": "audiobook",
            "narrators": ["George Guidall"],
        }
    )

    book = db.get_book(book_id)
    assert book is not None
    assert book["authors"] == ["Ursula K. Le Guin"]
    assert book["narrators"] == ["George Guidall"]


def test_delete_book_cascades(db: Database) -> None:
    book_id = db.create_book(BOOK)
    db.add_note(book_id, "note", "Re-read this one in winter.")

    db.delete_book(book_id)

    assert db.get_book(book_id) is None
    for table in ("book_author", "book_genre", "book_note"):
        row = db.conn.execute(
            f"SELECT COUNT(*) AS n FROM {table} WHERE book_id = ?", (book_id,)
        ).fetchone()
        assert row["n"] == 0, f"{table} kept orphaned rows"


def test_get_missing_book_returns_none(db: Database) -> None:
    assert db.get_book(404) is None


# --------------------------------------------------------- reading journal
def test_notes_round_trip(db: Database) -> None:
    book_id = db.create_book(BOOK)
    db.add_note(book_id, "quote", "Light is the left hand of darkness.")

    notes = db.list_notes(book_id)
    assert len(notes) == 1
    assert notes[0]["entry_type"] == "quote"

    db.delete_note(notes[0]["note_id"])
    assert db.list_notes(book_id) == []


# ---------------------------------------------- listing, filtering, search
def test_list_books_filters(db: Database) -> None:
    db.create_book(BOOK)
    db.create_book(
        {
            **BOOK,
            "title": "Piranesi",
            "format": "ebook",
            "read_status": "unread",
            "authors": ["Susanna Clarke"],
        }
    )

    titles = [b["title"] for b in db.list_books()]
    assert titles == ["Piranesi", "The Left Hand of Darkness"]  # ORDER BY title

    assert [b["title"] for b in db.list_books(status="unread")] == ["Piranesi"]
    assert [b["title"] for b in db.list_books(fmt="physical")] == [
        "The Left Hand of Darkness"
    ]

    row = next(b for b in db.list_books() if b["title"] == "Piranesi")
    assert row["authors"] == "Susanna Clarke"
    assert row["series"] == "Hainish Cycle"


def test_search_matches_title_prefix(db: Database) -> None:
    db.create_book(BOOK)
    db.create_book({**BOOK, "title": "Piranesi", "description": None})

    assert [b["title"] for b in db.list_books(search="dark")] == [
        "The Left Hand of Darkness"
    ]
    assert db.list_books(search="nothing here") == []


def test_search_reaches_notes(db: Database) -> None:
    book_id = db.create_book({**BOOK, "description": None})
    db.add_note(book_id, "note", "A gethenian kemmer explained badly.")

    assert [b["book_id"] for b in db.list_books(search="gethenian")] == [book_id]


def test_search_survives_fts_metacharacters(db: Database) -> None:
    """A stray quote or operator must not raise — see ``_fts_match``."""
    db.create_book(BOOK)

    assert [b["title"] for b in db.list_books(search='"darkness')] == [
        "The Left Hand of Darkness"
    ]
    assert db.list_books(search="   ") == db.list_books()
    assert db.list_books(search="AND OR *") == []
