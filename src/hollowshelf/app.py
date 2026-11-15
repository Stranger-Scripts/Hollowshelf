"""Application wiring: build the database, register pages, run a native window."""

from __future__ import annotations

from nicegui import app, ui

from . import config, state
from .db import Database
from .ui import book_form, browse, settings


def _register_pages() -> None:
    @ui.page("/")
    def _index() -> None:
        browse.render()

    @ui.page("/book/new")
    def _new_book() -> None:
        book_form.render(None)

    @ui.page("/book/{book_id}")
    def _edit_book(book_id: int) -> None:
        book_form.render(book_id)

    @ui.page("/settings")
    def _settings() -> None:
        settings.render()


def main() -> None:
    # The legacy-import offer (DATA-001) only makes sense on a first start:
    # the check has to run before Database() creates the new file.
    if not config.db_path().exists():
        state.pending_legacy_import = config.legacy_db_path()
    state.db = Database(config.db_path(), config.schema_sql())
    # Late-bound on purpose: the legacy import (browse.py) swaps state.db.
    app.on_shutdown(lambda: state.db.close())
    _register_pages()
    ui.run(
        native=True,
        reload=False,
        title=config.APP_NAME,
        port=8003,
        storage_secret="hollowshelf-local",
    )


if __name__ in {"__main__", "__mp_main__"}:
    main()
