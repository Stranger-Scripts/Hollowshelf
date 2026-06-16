"""The library page: search, filter, and an AG Grid of the whole collection."""

from __future__ import annotations

from nicegui import ui

from .. import state
from . import common


def _to_row(book: dict) -> dict:
    rating = book.get("rating")
    pub = book.get("publication_date") or ""
    return {
        "id": book["book_id"],
        "title": book["title"],
        "authors": book.get("authors") or "",
        "series": book.get("series") or "",
        "format": common.FORMATS.get(book["format"], book["format"]),
        "status": common.READ_STATUS.get(book["read_status"], book["read_status"]),
        "rating": "★" * rating if rating else "",
        "year": pub[:4],
    }


def render() -> None:
    common.header("library")
    if not common.ensure_profile():
        return

    with ui.column().classes("w-full max-w-screen-xl mx-auto p-4 gap-4"):
        ui.label("Library").classes("text-2xl font-bold")

        with ui.row().classes("w-full items-end gap-3"):
            search = ui.input(
                "Search", placeholder="title, author, description, notes…"
            ).props("clearable").classes("grow")
            status = ui.select(
                {None: "Any status", **common.READ_STATUS},
                value=None, label="Status",
            ).classes("w-40")
            fmt = ui.select(
                {None: "Any format", **common.FORMATS},
                value=None, label="Format",
            ).classes("w-40")
            ui.button("Add book", icon="add",
                      on_click=lambda: ui.navigate.to("/book/new"))

        count = ui.label().classes("text-sm opacity-70")

        grid = ui.aggrid({
            "columnDefs": [
                {"headerName": "Title", "field": "title", "flex": 2,
                 "sortable": True, "filter": True},
                {"headerName": "Author(s)", "field": "authors", "flex": 2,
                 "sortable": True, "filter": True},
                {"headerName": "Series", "field": "series", "flex": 1,
                 "sortable": True},
                {"headerName": "Format", "field": "format", "width": 120,
                 "sortable": True},
                {"headerName": "Status", "field": "status", "width": 130,
                 "sortable": True},
                {"headerName": "Rating", "field": "rating", "width": 110,
                 "sortable": True},
                {"headerName": "Year", "field": "year", "width": 90,
                 "sortable": True},
            ],
            "rowData": [],
            "rowSelection": {"mode": "singleRow"},
        }).classes("w-full").style("height: 65vh")

        def refresh() -> None:
            books = state.db.list_books(search.value, status.value, fmt.value)
            grid.options["rowData"] = [_to_row(b) for b in books]
            grid.update()
            n = len(books)
            count.text = f"{n} book{'s' if n != 1 else ''}"

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
        ui.label("Double-click a row to open a book.").classes("text-xs opacity-60")
