"""Settings: edit the name/email used for the API User-Agent."""

from __future__ import annotations

from nicegui import ui

from .. import config, state
from . import common


def render() -> None:
    common.header("settings")
    profile = state.db.get_profile()

    with ui.column().classes("w-full max-w-screen-md mx-auto p-4 gap-4"):
        ui.label("Settings").classes("text-2xl font-bold")

        with ui.card().classes("w-full gap-3"):
            ui.label("Identity").classes("text-lg font-semibold")
            ui.label(
                "Sent as the User-Agent when looking up books, so the free APIs "
                "can identify the app (Open Library asks for this). Stored locally "
                "in your library database — never shared anywhere else."
            ).classes("text-sm opacity-80")
            name = ui.input("Name", value=profile["name"]).classes("w-full")
            email = ui.input("Email", value=profile["email"]).classes("w-full")

            preview = ui.label().classes("text-xs font-mono opacity-70")

            def update_preview() -> None:
                ua = f"{config.APP_NAME}/{config.APP_VERSION}"
                if email.value.strip():
                    ua += f" (contact: {email.value.strip()})"
                preview.text = f"User-Agent: {ua}"

            email.on("update:model-value", lambda: update_preview())
            update_preview()

            def save() -> None:
                if not name.value.strip() or not email.value.strip():
                    ui.notify("Both fields are required", type="warning")
                    return
                if "@" not in email.value:
                    ui.notify("That doesn't look like an email", type="warning")
                    return
                state.db.set_profile(name.value, email.value)
                ui.notify("Saved", type="positive")

            with ui.row().classes("w-full justify-end"):
                ui.button("Save", icon="save", on_click=save)

        with ui.card().classes("w-full gap-3"):
            ui.label("Google Books").classes("text-lg font-semibold")
            ui.label(
                "Optional. Without a key, Google Books shares a small daily quota "
                "that runs out (lookups then quietly return nothing). Add your own "
                "free key — enable the Books API in the Google Cloud console — to "
                "raise it. Stored locally in your library database."
            ).classes("text-sm opacity-80")
            api_key = ui.input(
                "API key",
                value=state.db.get_setting("google_books_api_key", "") or "",
                password=True,
                password_toggle_button=True,
            ).classes("w-full")

            def save_key() -> None:
                state.db.set_setting(
                    "google_books_api_key", (api_key.value or "").strip()
                )
                ui.notify("Saved", type="positive")

            with ui.row().classes("w-full justify-end"):
                ui.button("Save", icon="save", on_click=save_key)

        with ui.card().classes("w-full gap-1"):
            ui.label("Storage").classes("text-lg font-semibold")
            ui.label(f"Library database: {config.DB_PATH}") \
                .classes("text-xs font-mono opacity-70")
            ui.label(f"API cache: {config.CACHE_PATH}") \
                .classes("text-xs font-mono opacity-70")
