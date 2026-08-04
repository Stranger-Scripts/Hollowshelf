"""Settings: edit the name/email used for the API User-Agent."""

from __future__ import annotations

from nicegui import ui

from .. import config, state
from ..i18n import _
from . import common


def render() -> None:
    common.header("settings")
    profile = state.db.get_profile()

    with ui.column().classes("w-full max-w-screen-md mx-auto p-4 gap-4"):
        ui.label(_("Settings")).classes("text-2xl font-bold")

        with ui.card().classes("w-full gap-3"):
            ui.label(_("Identity")).classes("text-lg font-semibold")
            ui.label(_(
                "Sent as the User-Agent when looking up books, so the free APIs "
                "can identify the app (Open Library asks for this). Stored locally "
                "in your library database — never shared anywhere else."
            )).classes("text-sm opacity-80")
            name = ui.input(_("Name"), value=profile["name"]).classes("w-full")
            email = ui.input(_("Email"), value=profile["email"]).classes("w-full")

            preview = ui.label().classes("text-xs font-mono opacity-70")

            def update_preview() -> None:
                ua = f"{config.APP_NAME}/{config.APP_VERSION}"
                if email.value.strip():
                    ua += f" (contact: {email.value.strip()})"
                preview.text = _("User-Agent: {ua}").format(ua=ua)

            email.on("update:model-value", lambda: update_preview())
            update_preview()

            def save() -> None:
                if not name.value.strip() or not email.value.strip():
                    ui.notify(_("Both fields are required"), type="warning")
                    return
                if "@" not in email.value:
                    ui.notify(_("That doesn't look like an email"), type="warning")
                    return
                state.db.set_profile(name.value, email.value)
                ui.notify(_("Saved"), type="positive")

            with ui.row().classes("w-full justify-end"):
                ui.button(_("Save"), icon="save", on_click=save)

        with ui.card().classes("w-full gap-3"):
            ui.label(_("Google Books")).classes("text-lg font-semibold")
            ui.label(_(
                "Optional. Without a key, Google Books shares a small daily quota "
                "that runs out (lookups then quietly return nothing). Add your own "
                "free key — enable the Books API in the Google Cloud console — to "
                "raise it. Stored locally in your library database."
            )).classes("text-sm opacity-80")
            api_key = ui.input(
                _("API key"),
                value=state.db.get_setting("google_books_api_key", "") or "",
                password=True,
                password_toggle_button=True,
            ).classes("w-full")

            def save_key() -> None:
                state.db.set_setting(
                    "google_books_api_key", (api_key.value or "").strip()
                )
                ui.notify(_("Saved"), type="positive")

            with ui.row().classes("w-full justify-end"):
                ui.button(_("Save"), icon="save", on_click=save_key)

        with ui.card().classes("w-full gap-1"):
            ui.label(_("Storage")).classes("text-lg font-semibold")
            ui.label(_("Library database: {path}").format(path=config.DB_PATH)) \
                .classes("text-xs font-mono opacity-70")
            ui.label(_("API cache: {path}").format(path=config.CACHE_PATH)) \
                .classes("text-xs font-mono opacity-70")
