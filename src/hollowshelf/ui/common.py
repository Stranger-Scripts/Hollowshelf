"""Shared UI pieces: the header/nav, option maps, and the first-run prompt."""

from __future__ import annotations

from nicegui import ui

from .. import state
from ..i18n import LANGUAGES, _, get_lang, set_lang

# Ratings are language-neutral (stars / an em dash for "no rating").
RATINGS = {0: "—", 1: "★", 2: "★★", 3: "★★★", 4: "★★★★", 5: "★★★★★"}


# The option maps mirror the CHECK constraints in the schema. Keys are the
# stored codes (never translated); the labels are built per render so they
# follow the active language.
def read_statuses() -> dict[str, str]:
    return {
        "unread": _("Unread"),
        "reading": _("Reading"),
        "read": _("Read"),
        "dnf": _("Did not finish"),
        "reference": _("Reference"),
    }


def formats() -> dict[str, str]:
    return {
        "physical": _("Physical"),
        "ebook": _("eBook"),
        "audiobook": _("Audiobook"),
    }


def entry_types() -> dict[str, str]:
    return {
        "note": _("Note"),
        "review": _("Review"),
        "quote": _("Quote"),
        "progress": _("Progress"),
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
            _nav(_("Library"), "/", active == "library")
            _nav(_("Add book"), "/book/new", active == "add")
            _nav(_("Settings"), "/settings", active == "settings")
            _language_toggle()


def _language_toggle() -> None:
    """A DE/EN switch. Flipping it persists the choice and re-renders the page."""
    def switch(e) -> None:
        set_lang(e.value)
        ui.navigate.reload()

    ui.toggle(LANGUAGES, value=get_lang(), on_change=switch) \
        .props("dense no-caps color=white").classes("ml-2")


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
        ui.label(_("Welcome to Hollowshelf")).classes("text-lg font-semibold")
        ui.label(_(
            "Enter your name and email. They identify the app to the free book "
            "APIs (Open Library asks apps to do this) and are stored locally — "
            "no account, nothing is sent anywhere else."
        )).classes("text-sm opacity-80")
        name = ui.input(_("Name")).classes("w-full")
        email = ui.input(_("Email")).classes("w-full")

        def save() -> None:
            if not name.value.strip() or not email.value.strip():
                ui.notify(_("Both fields are required"), type="warning")
                return
            if "@" not in email.value:
                ui.notify(_("That doesn't look like an email"), type="warning")
                return
            state.db.set_profile(name.value, email.value)
            dialog.close()
            ui.navigate.to("/")

        with ui.row().classes("w-full justify-end"):
            ui.button(_("Save"), on_click=save)

    dialog.open()
    return False
