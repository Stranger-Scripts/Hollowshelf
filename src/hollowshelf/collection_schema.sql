-- ============================================================
-- Personal Book Collection — SQLite schema (flat-first draft)
-- With FTS5 full-text search.
-- ============================================================
-- One row in `book` = one item you own.
-- Same title in two formats = two rows for now (the flat approach).
-- When the duplication starts get annoying, split into book (the title)
-- + book_copy (the format/location) — the data should migrate cleanly.
--
-- Enable foreign keys on every connection:
PRAGMA foreign_keys = ON;

-- ---------- Lookup / reference tables ----------

CREATE TABLE language (
    language_id   INTEGER PRIMARY KEY,
    name          TEXT NOT NULL UNIQUE,
    code          TEXT UNIQUE                -- ISO 639-1, e.g. 'en', 'de'
);

CREATE TABLE publisher (
    publisher_id  INTEGER PRIMARY KEY,
    name          TEXT NOT NULL,
    website       TEXT,
    country       TEXT
);

CREATE TABLE series (
    series_id     INTEGER PRIMARY KEY,
    name          TEXT NOT NULL,
    total_planned INTEGER                    -- books planned in the series, if known
);

CREATE TABLE author (
    author_id     INTEGER PRIMARY KEY,
    first_name    TEXT,
    last_name     TEXT,
    sort_name     TEXT,                       -- e.g. 'Le Guin, Ursula K.' for sorting
    biography     TEXT,
    birth_date    TEXT,                        -- ISO8601 'YYYY-MM-DD'
    nationality   TEXT
);

CREATE TABLE genre (
    genre_id      INTEGER PRIMARY KEY,
    name          TEXT NOT NULL UNIQUE
);


-- ---------- Core table: the items you own ----------

CREATE TABLE book (
    book_id          INTEGER PRIMARY KEY,
    title            TEXT NOT NULL,
    subtitle         TEXT,
    isbn13           TEXT,                     -- NOT unique: differs per format, may be null for some ebooks/audio
    format           TEXT NOT NULL
                      CHECK (format IN ('physical','ebook','audiobook')),

    publication_date TEXT,                     -- ISO8601
    publisher_id     INTEGER REFERENCES publisher(publisher_id),
    language_id      INTEGER REFERENCES language(language_id),

    -- format-specific fields (leave the irrelevant ones NULL)
    page_count       INTEGER,                  -- physical / ebook
    duration_minutes INTEGER,                  -- audiobook
    file_format      TEXT,                     -- 'EPUB','PDF','MP3','M4B'... for ebook/audio

    -- series placement
    series_id        INTEGER REFERENCES series(series_id),
    series_position  REAL,                     -- REAL so 1.5 works for novellas

    -- where it physically / digitally lives
    location         TEXT,                     -- 'Shelf B3', 'Kindle', 'Audible', '/media/books/...'

    description      TEXT,                      -- markdown OK; rendered in-app; Maybe change to MEDIUMTEXT lateron
    cover_image_url  TEXT,

    -- personal metadata
    read_status      TEXT NOT NULL DEFAULT 'unread'
                      CHECK (read_status IN ('unread','reading','read','dnf','reference')),
    rating           INTEGER CHECK (rating BETWEEN 1 AND 5),
    acquired_date    TEXT,
    review           TEXT,                      -- markdown OK; rendered in-app; see book_note for journaling;  Maybe change to MEDIUMTEXT lateron

    created_at       TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at       TEXT NOT NULL DEFAULT (datetime('now'))
);


-- ---------- Many-to-many junctions ----------

CREATE TABLE book_author (
    book_id       INTEGER NOT NULL REFERENCES book(book_id)   ON DELETE CASCADE,
    author_id     INTEGER NOT NULL REFERENCES author(author_id) ON DELETE CASCADE,
    role          TEXT NOT NULL DEFAULT 'author'
                  CHECK (role IN ('author','editor','translator','narrator','illustrator')),
    author_order  INTEGER DEFAULT 1,           -- ordering of authors on the cover
    PRIMARY KEY (book_id, author_id, role)
);

CREATE TABLE book_genre (
    book_id       INTEGER NOT NULL REFERENCES book(book_id)  ON DELETE CASCADE,
    genre_id      INTEGER NOT NULL REFERENCES genre(genre_id) ON DELETE CASCADE,
    PRIMARY KEY (book_id, genre_id)
);


-- ---------- Timestamped reading journal ----------
-- Many dated markdown notes per book. This is the home for notes/reviews
-- that accumulate over time (the single book.review field is fine for a
-- one-shot take; use this when you want a log).
CREATE TABLE book_note (
    note_id     INTEGER PRIMARY KEY,
    book_id     INTEGER NOT NULL REFERENCES book(book_id) ON DELETE CASCADE,
    note_date   TEXT NOT NULL DEFAULT (datetime('now')),
    entry_type  TEXT NOT NULL DEFAULT 'note'
                CHECK (entry_type IN ('note','review','quote','progress')),
    content     TEXT NOT NULL                  -- markdown
);


-- ---------- Helpful indexes ----------
CREATE INDEX idx_book_title  ON book(title);
CREATE INDEX idx_book_format ON book(format);
CREATE INDEX idx_book_status ON book(read_status);
CREATE INDEX idx_book_series ON book(series_id);
CREATE INDEX idx_ba_author   ON book_author(author_id);
CREATE INDEX idx_bg_genre    ON book_genre(genre_id);


-- ============================================================
-- FULL-TEXT SEARCH (FTS5)
-- ============================================================
-- External-content tables: the index points back at the real rows and
-- stores no copy of the text. Triggers below keep the index in sync.
--
-- Tokenizer: 'porter unicode61 remove_diacritics 2'
--   - porter            -> English stemming (review ~ reviewing ~ reviews)
--   - unicode61         -> Unicode-aware word splitting
--   - remove_diacritics -> "Borges" matches "Bórges"
-- If notes are mostly NON-English, delete the word `porter` below. #ToDo

-- --- Catalog text (title / subtitle / description / review) ---
CREATE VIRTUAL TABLE book_fts USING fts5(
    title, subtitle, description, review,
    content='book',
    content_rowid='book_id',
    tokenize='porter unicode61 remove_diacritics 2'
);

CREATE TRIGGER book_fts_ai AFTER INSERT ON book BEGIN
    INSERT INTO book_fts(rowid, title, subtitle, description, review)
    VALUES (new.book_id, new.title, new.subtitle, new.description, new.review);
END;

CREATE TRIGGER book_fts_ad AFTER DELETE ON book BEGIN
    INSERT INTO book_fts(book_fts, rowid, title, subtitle, description, review)
    VALUES ('delete', old.book_id, old.title, old.subtitle, old.description, old.review);
END;

CREATE TRIGGER book_fts_au AFTER UPDATE ON book BEGIN
    INSERT INTO book_fts(book_fts, rowid, title, subtitle, description, review)
    VALUES ('delete', old.book_id, old.title, old.subtitle, old.description, old.review);
    INSERT INTO book_fts(rowid, title, subtitle, description, review)
    VALUES (new.book_id, new.title, new.subtitle, new.description, new.review);
END;

-- --- Reading-journal notes ---
CREATE VIRTUAL TABLE note_fts USING fts5(
    content,
    content='book_note',
    content_rowid='note_id',
    tokenize='porter unicode61 remove_diacritics 2'
);

CREATE TRIGGER note_fts_ai AFTER INSERT ON book_note BEGIN
    INSERT INTO note_fts(rowid, content) VALUES (new.note_id, new.content);
END;

CREATE TRIGGER note_fts_ad AFTER DELETE ON book_note BEGIN
    INSERT INTO note_fts(note_fts, rowid, content) VALUES ('delete', old.note_id, old.content);
END;

CREATE TRIGGER note_fts_au AFTER UPDATE ON book_note BEGIN
    INSERT INTO note_fts(note_fts, rowid, content) VALUES ('delete', old.note_id, old.content);
    INSERT INTO note_fts(rowid, content) VALUES (new.note_id, new.content);
END;

-- --- Maintenance ---
-- Rebuild an index from its source table (run after a bulk import, or to
-- repair drift). Safe to run anytime:
--     INSERT INTO book_fts(book_fts) VALUES('rebuild');
--     INSERT INTO note_fts(note_fts) VALUES('rebuild');


-- ============================================================
-- Example queries | Note to myself 
-- ============================================================

-- FTS5 query syntax cheatsheet (goes in the MATCH string):
--   dragon            -> word
--   "unreliable narrator"   -> exact phrase
--   narr*             -> prefix match
--   ghost AND ship    -> boolean (also OR, NOT)
--   title:dune        -> restrict to one column

-- Search the catalog, best matches first, title weighted highest:
--   SELECT b.book_id, b.title
--   FROM book_fts
--   JOIN book b ON b.book_id = book_fts.rowid
--   WHERE book_fts MATCH 'dragon'
--   ORDER BY bm25(book_fts, 10.0, 4.0, 1.0, 6.0);   -- title, subtitle, description, review

-- Search notes, returning a highlighted snippet of context:
--   SELECT n.book_id,
--          snippet(note_fts, 0, '[', ']', ' … ', 12) AS excerpt
--   FROM note_fts
--   JOIN book_note n ON n.note_id = note_fts.rowid
--   WHERE note_fts MATCH 'unreliable narrator'
--   ORDER BY rank;

-- One search across BOTH catalog and notes:
--   SELECT 'book' AS source, b.book_id, b.title
--   FROM book_fts JOIN book b ON b.book_id = book_fts.rowid
--   WHERE book_fts MATCH :q
--   UNION ALL
--   SELECT 'note' AS source, b.book_id, b.title
--   FROM note_fts
--   JOIN book_note n ON n.note_id = note_fts.rowid
--   JOIN book b      ON b.book_id = n.book_id
--   WHERE note_fts MATCH :q;
--   -- (relevance scores aren't directly comparable across the two indexes,
--   --  but for a personal tool a simple combined list is usually fine.)

-- All unread sci-fi with their author(s) — plain relational, no FTS:
--   SELECT b.title, a.sort_name
--   FROM book b
--   JOIN book_genre  bg ON bg.book_id = b.book_id
--   JOIN genre       g  ON g.genre_id = bg.genre_id
--   JOIN book_author ba ON ba.book_id = b.book_id
--   JOIN author      a  ON a.author_id = ba.author_id
--   WHERE g.name = 'Science Fiction' AND b.read_status = 'unread';
