# Hollowshelf

A personal book library — a native desktop app built with [NiceGUI](https://nicegui.io).

Browse and full-text-search your collection, add books by looking them up on
Open Library / Google Books (or by hand), write markdown reviews and a dated
reading journal. Data lives in a local SQLite database using the FTS5 schema in
`collection_schema.sql`.

## Run it

```bash
# 1. install dependencies (a virtualenv is recommended)
pip install -e .

# 2. launch the native window
hollowshelf
#   …or, without installing:
python run.py
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
