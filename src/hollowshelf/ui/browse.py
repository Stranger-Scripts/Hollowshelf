"""The library page: search, filter, and an AG Grid of the whole collection."""

from __future__ import annotations

from nicegui import ui

from .. import config, state
from ..db import Database, copy_database
from ..i18n import _, ngettext
from . import common


def _to_row(book: dict, fmts: dict, stats: dict) -> dict:
    rating = book.get("rating")
    pub = book.get("publication_date") or ""
    return {
        "id": book["book_id"],
        "title": book["title"],
        "authors": book.get("authors") or "",
        "series": book.get("series") or "",
        "format": fmts.get(book["format"], book["format"]),
        "status": stats.get(book["read_status"], book["read_status"]),
        "rating": "★" * rating if rating else "",
        "year": pub[:4],
    }


def _offer_legacy_import() -> None:
    """One-time offer (DATA-001): import a pre-existing `<repo>/data/library.db`."""
    legacy = state.pending_legacy_import
    if not legacy:
        return

    def _do_import() -> None:
        state.db.close()
        copy_database(legacy, config.db_path())
        state.db = Database(config.db_path(), config.schema_sql())
        state.pending_legacy_import = None
        dialog.close()
        ui.notify(_("Library imported."))
        ui.navigate.reload()

    def _skip() -> None:
        state.pending_legacy_import = None
        dialog.close()

    with ui.dialog() as dialog, ui.card():
        ui.label(_("Existing library found")).classes("text-lg font-bold")
        ui.label(
            _(
                "A library from an earlier version was found at {path}. "
                "Import it into the new data directory ({data_dir})? "
                "The original file is left untouched."
            ).format(path=legacy, data_dir=config.data_dir())
        )
        with ui.row().classes("w-full justify-end"):
            ui.button(_("Start fresh"), on_click=_skip).props("flat")
            ui.button(_("Import"), on_click=_do_import)
    dialog.open()


def render() -> None:
    common.header("library")
    _offer_legacy_import()
    if not common.ensure_profile():
        return

    with ui.column().classes("w-full max-w-screen-xl mx-auto p-4 gap-4"):
        ui.label(_("Library")).classes("text-2xl font-bold")

        with ui.row().classes("w-full items-end gap-3"):
            search = (
                ui.input(
                    _("Search"), placeholder=_("title, author, description, notes…")
                )
                .props("clearable")
                .classes("grow")
            )
            status = ui.select(
                {None: _("Any status"), **common.read_statuses()},
                value=None,
                label=_("Status"),
            ).classes("w-40")
            fmt = ui.select(
                {None: _("Any format"), **common.formats()},
                value=None,
                label=_("Format"),
            ).classes("w-40")
            ui.button(
                _("Add book"), icon="add", on_click=lambda: ui.navigate.to("/book/new")
            )

        count = ui.label().classes("text-sm opacity-70")

        # Kept hand-aligned: one line per grid column reads as a table.
        # fmt: off
        grid = ui.aggrid({
            "columnDefs": [
                {"headerName": _("Title"), "field": "title", "flex": 2,
                 "sortable": True, "filter": True},
                {"headerName": _("Author(s)"), "field": "authors", "flex": 2,
                 "sortable": True, "filter": True},
                {"headerName": _("Series"), "field": "series", "flex": 1,
                 "sortable": True},
                {"headerName": _("Format"), "field": "format", "width": 120,
                 "sortable": True},
                {"headerName": _("Status"), "field": "status", "width": 130,
                 "sortable": True},
                {"headerName": _("Rating"), "field": "rating", "width": 110,
                 "sortable": True},
                {"headerName": _("Year"), "field": "year", "width": 90,
                 "sortable": True},
            ],
            "rowData": [],
            "rowSelection": {"mode": "singleRow"},
        }).classes("w-full").style("height: 65vh")
        # fmt: on

        def refresh() -> None:
            books = state.db.list_books(search.value, status.value, fmt.value)
            fmts, stats = common.formats(), common.read_statuses()
            grid.options["rowData"] = [_to_row(b, fmts, stats) for b in books]
            grid.update()
            n = len(books)
            count.text = ngettext("%d book", "%d books", n) % n

        search.on("update:model-value", lambda: refresh())
        status.on("update:model-value", lambda: refresh())
        fmt.on("update:model-value", lambda: refresh())
        # Only forward the row ``data`` field. Without this, NiceGUI tries to
        # serialise the entire AG Grid event, whose ``context`` is circular,
        # JSON.stringify throws client-side, and the event never reaches here.
        grid.on(
            "rowDoubleClicked",
            lambda e: ui.navigate.to(f"/book/{e.args['data']['id']}"),
            ["data"],
        )

        refresh()
        ui.label(_("Double-click a row to open a book.")).classes("text-xs opacity-60")
