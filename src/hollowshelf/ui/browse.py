"""The library page: search, filter, and an AG Grid of the whole collection."""

from __future__ import annotations

from nicegui import ui

from .. import state
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


def render() -> None:
    common.header("library")
    if not common.ensure_profile():
        return

    with ui.column().classes("w-full max-w-screen-xl mx-auto p-4 gap-4"):
        ui.label(_("Library")).classes("text-2xl font-bold")

        with ui.row().classes("w-full items-end gap-3"):
            search = ui.input(
                _("Search"), placeholder=_("title, author, description, notes…")
            ).props("clearable").classes("grow")
            status = ui.select(
                {None: _("Any status"), **common.read_statuses()},
                value=None, label=_("Status"),
            ).classes("w-40")
            fmt = ui.select(
                {None: _("Any format"), **common.formats()},
                value=None, label=_("Format"),
            ).classes("w-40")
            ui.button(_("Add book"), icon="add",
                      on_click=lambda: ui.navigate.to("/book/new"))

        count = ui.label().classes("text-sm opacity-70")

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
