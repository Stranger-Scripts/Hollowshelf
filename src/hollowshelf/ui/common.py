"""Shared UI pieces: the header/nav, option maps, and the first-run prompt."""

from __future__ import annotations

from nicegui import ui

from .. import state

# Constrained option maps (mirror the CHECK constraints in the schema).
READ_STATUS = {
    "unread": "Unread",
    "reading": "Reading",
    "read": "Read",
    "dnf": "Did not finish",
    "reference": "Reference",
}
FORMATS = {
    "physical": "Physical",
    "ebook": "eBook",
    "audiobook": "Audiobook",
}
RATINGS = {0: "—", 1: "★", 2: "★★", 3: "★★★", 4: "★★★★", 5: "★★★★★"}
ENTRY_TYPES = {
    "note": "Note",
    "review": "Review",
    "quote": "Quote",
    "progress": "Progress",
}


def header(active: str = "") -> None:
    """Render the top navigation bar. ``active`` is one of library/add/settings."""
    with ui.header().classes("items-center justify-between px-4 py-2"):
        with ui.row().classes("items-center gap-2 cursor-pointer").on(
            "click", lambda: ui.navigate.to("/")
        ):
            ui.icon("menu_book").classes("text-2xl")
            ui.label("Hollowshelf").classes("text-xl font-semibold")
        with ui.row().classes("items-center gap-1"):
            _nav("Library", "/", active == "library")
            _nav("Add book", "/book/new", active == "add")
            _nav("Settings", "/settings", active == "settings")


def _nav(label: str, target: str, is_active: bool) -> None:
    btn = ui.button(label, on_click=lambda: ui.navigate.to(target)).props("flat")
    if is_active:
        btn.props("color=white").classes("font-bold")
    else:
        btn.props("flat color=white").classes("opacity-80")


def ensure_profile() -> bool:
    """If name/email aren't set, pop a blocking first-run dialog.

    Returns True when a profile already exists (page can render normally),
    False when the prompt was shown instead.
    """
    if state.db.is_configured():
        return True

    with ui.dialog().props("persistent") as dialog, ui.card().classes("w-96 gap-3"):
        ui.label("Welcome to Hollowshelf").classes("text-lg font-semibold")
        ui.label(
            "Enter your name and email. They identify the app to the free book "
            "APIs (Open Library asks apps to do this) and are stored locally — "
            "no account, nothing is sent anywhere else."
        ).classes("text-sm opacity-80")
        name = ui.input("Name").classes("w-full")
        email = ui.input("Email").classes("w-full")

        def save() -> None:
            if not name.value.strip() or not email.value.strip():
                ui.notify("Both fields are required", type="warning")
                return
            if "@" not in email.value:
                ui.notify("That doesn't look like an email", type="warning")
                return
            state.db.set_profile(name.value, email.value)
            dialog.close()
            ui.navigate.to("/")

        with ui.row().classes("w-full justify-end"):
            ui.button("Save", on_click=save)

    dialog.open()
    return False
