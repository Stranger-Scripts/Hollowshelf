"""Add / edit a book: API lookup, the full form, markdown editors, journal."""

from __future__ import annotations

from typing import Optional

from nicegui import run, ui

from .. import state
from ..book_client import BookResult
from . import common

_MEDIA_TO_FORMAT = {"print": "physical", "ebook": "ebook", "audiobook": "audiobook"}


def render(book_id: Optional[int]) -> None:
    common.header("add" if book_id is None else "library")
    if not common.ensure_profile():
        return

    book = state.db.get_book(book_id) if book_id is not None else None
    if book_id is not None and book is None:
        with ui.column().classes("w-full max-w-screen-md mx-auto p-6 gap-3"):
            ui.label("That book no longer exists.").classes("text-lg")
            ui.button("Back to library", on_click=lambda: ui.navigate.to("/"))
        return

    f: dict[str, object] = {}

    with ui.column().classes("w-full max-w-screen-lg mx-auto p-4 gap-4"):
        ui.label("Add a book" if book is None else f"Edit · {book['title']}") \
            .classes("text-2xl font-bold")

        if book is None:
            _lookup_card(f)
        _form_card(f, book)
        _action_row(f, book_id)
        if book is not None:
            _journal_card(book_id)


# --------------------------------------------------------------------------- #
#  Metadata lookup (Open Library / Google Books)
# --------------------------------------------------------------------------- #

def _lookup_card(f: dict) -> None:
    with ui.expansion("Look up metadata (Open Library / Google Books)",
                      icon="search", value=True).classes("w-full border rounded"):
        with ui.column().classes("w-full p-2 gap-3"):
            with ui.row().classes("w-full items-end gap-2"):
                isbn = ui.input("ISBN", placeholder="978…").classes("grow")
                isbn_btn = ui.button("Search ISBN", icon="search")
            with ui.row().classes("w-full items-end gap-2"):
                title = ui.input("Title").classes("grow")
                author = ui.input("Author").classes("w-48")
                lang = ui.select(
                    {None: "Any", "en": "English", "de": "German"},
                    value=None, label="Language",
                ).classes("w-32")
                title_btn = ui.button("Search title", icon="search")

            spinner = ui.spinner(size="lg")
            spinner.visible = False
            results = ui.column().classes("w-full gap-2")

            def show(items: list[BookResult]) -> None:
                results.clear()
                if not items:
                    with results:
                        ui.label("No matches (or the API was unreachable).") \
                            .classes("text-sm opacity-70")
                    return
                with results:
                    for res in items:
                        _result_card(res, f)

            async def do_isbn() -> None:
                if not isbn.value.strip():
                    return
                spinner.visible = True
                res = await run.io_bound(
                    state.get_client().search_by_isbn, isbn.value.strip()
                )
                spinner.visible = False
                show([res] if res else [])

            async def do_title() -> None:
                if not title.value.strip():
                    return
                spinner.visible = True
                hits = await run.io_bound(
                    state.get_client().search_by_title,
                    title.value.strip(), author.value.strip() or None,
                    lang.value, 8,
                )
                spinner.visible = False
                show(hits)

            isbn_btn.on_click(do_isbn)
            isbn.on("keydown.enter", do_isbn)
            title_btn.on_click(do_title)
            title.on("keydown.enter", do_title)


def _result_card(res: BookResult, f: dict) -> None:
    with ui.card().classes("w-full"):
        with ui.row().classes("items-start gap-3 no-wrap"):
            if res.cover_url:
                ui.image(res.cover_url).classes("w-16 h-24 object-cover rounded")
            with ui.column().classes("grow gap-0"):
                ui.label(res.title).classes("font-semibold")
                if res.authors:
                    ui.label(", ".join(res.authors)).classes("text-sm")
                meta = " · ".join(
                    str(x) for x in (res.year, res.media, res.source) if x
                )
                ui.label(meta).classes("text-xs opacity-70")
            ui.button("Use", icon="check",
                      on_click=lambda r=res: _apply(r, f)).props("outline")


def _apply(res: BookResult, f: dict) -> None:
    f["title"].value = res.title or ""
    f["authors"].value = "\n".join(res.authors)
    f["isbn13"].value = res.isbn_13 or res.isbn_10 or ""
    f["publication_date"].value = str(res.year) if res.year else ""
    f["publisher"].value = res.publisher or ""
    f["language"].value = res.language or ""
    f["cover_image_url"].value = res.cover_url or ""
    f["description"].value = res.description or ""
    f["page_count"].value = res.page_count
    if res.media in _MEDIA_TO_FORMAT:
        f["format"].value = _MEDIA_TO_FORMAT[res.media]
    ui.notify(f"Filled from “{res.title}”")


# --------------------------------------------------------------------------- #
#  The form
# --------------------------------------------------------------------------- #

def _form_card(f: dict, book: Optional[dict]) -> None:
    b = book or {}
    with ui.card().classes("w-full gap-3"):
        with ui.row().classes("w-full gap-3 no-wrap"):
            with ui.column().classes("grow gap-3"):
                f["title"] = ui.input("Title", value=b.get("title", "")) \
                    .classes("w-full")
                f["subtitle"] = ui.input("Subtitle", value=b.get("subtitle") or "") \
                    .classes("w-full")
                f["authors"] = ui.textarea(
                    "Authors (one per line)",
                    value="\n".join(b.get("authors", [])),
                ).classes("w-full")
                f["narrators"] = ui.textarea(
                    "Narrators (one per line, optional)",
                    value="\n".join(b.get("narrators", [])),
                ).classes("w-full")
                f["genres"] = ui.input(
                    "Genres (comma-separated)",
                    value=", ".join(b.get("genres", [])),
                ).classes("w-full")
            # Cover preview (bound to the URL field once it exists, below).
            with ui.column().classes("items-center gap-1"):
                ui.label("Cover").classes("text-xs opacity-60")
                cover = ui.image().classes(
                    "w-32 h-48 object-cover rounded border"
                )

        with ui.row().classes("w-full gap-3 flex-wrap"):
            f["format"] = ui.select(
                common.FORMATS, value=b.get("format", "physical"), label="Format",
            ).classes("w-40")
            f["read_status"] = ui.select(
                common.READ_STATUS, value=b.get("read_status", "unread"),
                label="Status",
            ).classes("w-40")
            f["rating"] = ui.select(
                common.RATINGS, value=b.get("rating") or 0, label="Rating",
            ).classes("w-32")
            f["language"] = ui.input(
                "Language code", value=b.get("language") or "",
            ).props("placeholder=en, de…").classes("w-32")

        with ui.row().classes("w-full gap-3 flex-wrap"):
            f["isbn13"] = ui.input("ISBN-13", value=b.get("isbn13") or "") \
                .classes("w-48")
            f["publisher"] = ui.input("Publisher", value=b.get("publisher") or "") \
                .classes("w-56")
            f["publication_date"] = ui.input(
                "Published", value=b.get("publication_date") or "",
            ).props("placeholder=YYYY or YYYY-MM-DD").classes("w-40")
            f["acquired_date"] = ui.input(
                "Acquired", value=b.get("acquired_date") or "",
            ).props("placeholder=YYYY-MM-DD").classes("w-40")

        with ui.row().classes("w-full gap-3 flex-wrap"):
            f["page_count"] = ui.number(
                "Pages", value=b.get("page_count"), format="%d",
            ).classes("w-32")
            f["duration_minutes"] = ui.number(
                "Duration (min)", value=b.get("duration_minutes"), format="%d",
            ).classes("w-40")
            f["file_format"] = ui.input(
                "File format", value=b.get("file_format") or "",
            ).props("placeholder=EPUB, MP3…").classes("w-40")
            f["series"] = ui.input("Series", value=b.get("series") or "") \
                .classes("w-56")
            f["series_position"] = ui.number(
                "Series #", value=b.get("series_position"), format="%g",
            ).classes("w-28")

        with ui.row().classes("w-full gap-3 flex-wrap"):
            f["location"] = ui.input(
                "Location", value=b.get("location") or "",
            ).props("placeholder=Shelf B3, Kindle, Audible…").classes("grow")
            f["cover_image_url"] = ui.input(
                "Cover image URL", value=b.get("cover_image_url") or "",
            ).classes("grow")

        # Wire the cover preview to the URL field.
        cover.bind_source_from(f["cover_image_url"], "value")

        f["description"] = _markdown_field(
            "Description", b.get("description") or ""
        )
        f["review"] = _markdown_field("Review", b.get("review") or "")


def _markdown_field(label: str, value: str):
    ui.label(label).classes("text-sm font-medium mt-2")
    with ui.row().classes("w-full gap-3 no-wrap items-stretch"):
        editor = ui.codemirror(
            value=value, language="markdown", line_wrapping=True,
        ).classes("w-1/2 border rounded").style("height: 16rem")
        with ui.scroll_area().classes("w-1/2 border rounded p-2") \
                .style("height: 16rem"):
            preview = ui.markdown(value)
        preview.bind_content_from(editor, "value")
    return editor


# --------------------------------------------------------------------------- #
#  Save / delete
# --------------------------------------------------------------------------- #

def _collect(f: dict) -> dict:
    def lines(key: str) -> list[str]:
        return [s.strip() for s in (f[key].value or "").splitlines() if s.strip()]

    rating = f["rating"].value
    return {
        "title": f["title"].value,
        "subtitle": f["subtitle"].value,
        "authors": lines("authors"),
        "narrators": lines("narrators"),
        "genres": [g.strip() for g in (f["genres"].value or "").split(",")
                   if g.strip()],
        "format": f["format"].value,
        "read_status": f["read_status"].value,
        "rating": rating or None,
        "language": f["language"].value,
        "isbn13": f["isbn13"].value,
        "publisher": f["publisher"].value,
        "publication_date": f["publication_date"].value,
        "acquired_date": f["acquired_date"].value,
        "page_count": f["page_count"].value,
        "duration_minutes": f["duration_minutes"].value,
        "file_format": f["file_format"].value,
        "series": f["series"].value,
        "series_position": f["series_position"].value,
        "location": f["location"].value,
        "cover_image_url": f["cover_image_url"].value,
        "description": f["description"].value,
        "review": f["review"].value,
    }


def _action_row(f: dict, book_id: Optional[int]) -> None:
    with ui.row().classes("w-full justify-between"):
        ui.button("Cancel", on_click=lambda: ui.navigate.to("/")).props("flat")
        with ui.row().classes("gap-2"):
            if book_id is not None:
                ui.button("Delete", icon="delete", color="negative",
                          on_click=lambda: _confirm_delete(book_id)).props("outline")
            ui.button("Save", icon="save", on_click=lambda: _save(f, book_id))


def _save(f: dict, book_id: Optional[int]) -> None:
    data = _collect(f)
    if not (data["title"] or "").strip():
        ui.notify("Title is required", type="warning")
        return
    if book_id is None:
        new_id = state.db.create_book(data)
        ui.notify("Book added", type="positive")
        ui.navigate.to(f"/book/{new_id}")
    else:
        state.db.update_book(book_id, data)
        ui.notify("Saved", type="positive")


def _confirm_delete(book_id: int) -> None:
    with ui.dialog() as dialog, ui.card().classes("gap-3"):
        ui.label("Delete this book and all its notes?")
        with ui.row().classes("w-full justify-end gap-2"):
            ui.button("Cancel", on_click=dialog.close).props("flat")

            def do() -> None:
                state.db.delete_book(book_id)
                dialog.close()
                ui.notify("Deleted")
                ui.navigate.to("/")

            ui.button("Delete", color="negative", on_click=do)
    dialog.open()


# --------------------------------------------------------------------------- #
#  Reading journal (book_note)
# --------------------------------------------------------------------------- #

def _journal_card(book_id: int) -> None:
    with ui.card().classes("w-full gap-3"):
        ui.label("Reading journal").classes("text-lg font-semibold")
        notes_box = ui.column().classes("w-full gap-2")

        def refresh() -> None:
            notes_box.clear()
            notes = state.db.list_notes(book_id)
            with notes_box:
                if not notes:
                    ui.label("No notes yet.").classes("text-sm opacity-70")
                for n in notes:
                    with ui.card().classes("w-full bg-gray-50 dark:bg-gray-800"):
                        with ui.row().classes("w-full justify-between items-center"):
                            ui.label(
                                f"{common.ENTRY_TYPES.get(n['entry_type'], n['entry_type'])}"
                                f" · {n['note_date']}"
                            ).classes("text-xs opacity-70")
                            ui.button(
                                icon="delete", color="negative",
                                on_click=lambda nid=n["note_id"]: _del_note(nid, refresh),
                            ).props("flat dense round")
                        ui.markdown(n["content"])

        with ui.row().classes("w-full items-end gap-2"):
            entry_type = ui.select(
                common.ENTRY_TYPES, value="note", label="Type",
            ).classes("w-40")
        editor = ui.codemirror(
            language="markdown", line_wrapping=True,
        ).classes("w-full border rounded").style("height: 10rem")

        def add() -> None:
            content = (editor.value or "").strip()
            if not content:
                ui.notify("Write something first", type="warning")
                return
            state.db.add_note(book_id, entry_type.value, content)
            editor.value = ""
            refresh()
            ui.notify("Note added", type="positive")

        ui.button("Add note", icon="add", on_click=add)
        refresh()


def _del_note(note_id: int, refresh) -> None:
    state.db.delete_note(note_id)
    refresh()
