# Hollowshelf

A personal book library — a native desktop app built with [NiceGUI](https://nicegui.io).

Browse and full-text-search your collection, add books by looking them up on
Open Library / Google Books (or by hand), write markdown reviews and a dated
reading journal. Data lives in a local SQLite database using the FTS5 schema in
`collection_schema.sql`.

## Requirements

- **Python:** `>= 3.12` (Tested up to `3.14`)
- **Platform-specific backends:** Automatically handled via `pyproject.toml` (`pywebview` native on Windows/macOS, `PyQt6` WebEngine on Linux).

## Run it

This project uses `uv` for fast, reproducible dependency management.

```bash
# 1. Pin the Python version and sync dependencies into a virtual environment
uv python pin 3.13
uv sync

# 2. Launch the native window application
uv run hollowshelf
```

On first launch you'll be asked for your name and email. These are stored
locally and used only to build the `User-Agent` the free book APIs ask for
(Open Library requests that apps identify themselves). You can change them later
under **Settings**.

## Layout

```
collection_schema.sql      # the SQLite + FTS5 schema (auto-applied on first run)
run.py                     # convenience launcher
data/                      # library.db + API cache (git-ignored, created on run)
src/hollowshelf/
  app.py                   # builds the DB, registers pages, runs the native window
  config.py                # paths and constants
  db.py                    # schema init, settings, book/note CRUD, FTS search
  book_client.py           # Open Library / Google Books lookup client
  state.py                 # shared DB handle + lazily-built API client
  ui/
    common.py              # header/nav, option maps, first-run prompt
    browse.py              # library grid + search/filter
    book_form.py           # add/edit form, API lookup, markdown editors, journal
    settings.py            # name/email + storage info
```

## Notes

- The book APIs are free and need no key. Lookups are cached in `data/book_cache.db`
  for 30 days, and run off the UI thread (`run.io_bound`) so the window never freezes.
- Audiobook/format detection from the APIs is only a hint — correct it in the form.
- `native=True` uses `pywebview`; on Linux it needs a webview backend
  (e.g. `python3-gi gir1.2-webkit2-4.1`, or install `pywebview[qt]`).

## Future Ideas 
  - [ ] **Data Portability:** Add bulk import/export options from Goodreads or LibraryThing CSV files.
  - [ ] **Data Export:** Add an option to export book tables and collections directly to an Excel sheet (`.xlsx`).
  - [ ] **Document Export:** Allow exporting specific notes, reviews, or journals into clean `.md` or `.docx` formats using Pandoc.
  - [ ] **Appearance:** Implement a native Dark Mode toggle utilizing NiceGUI's theme system.
  - [ ] **Backups:** Add automated database backups to a secondary local directory or user-defined path.
  - [ ] **Reading Stats:** Simple analytics dashboard (books read per year, top genres, reading streaks).
  - [ ] **Translation:** Add multi-language support, starting with a native German translation.