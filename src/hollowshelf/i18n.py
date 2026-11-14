"""German/English UI translation.

Runtime translation uses the standard-library ``gettext`` module, so there is no
runtime dependency: the compiled ``.mo`` catalogs under
``locales/<lang>/LC_MESSAGES/`` are produced from ``.po`` sources with Babel,
which is only needed at development time (see ``babel.cfg`` and the README).

The active language is stored per client in ``app.storage.user`` so it survives
page reloads and app restarts, and it is resolved *fresh on every* ``_()`` call.
That is what lets the header toggle flip the language and a plain
``ui.navigate.reload()`` re-render the page in the new language — no restart.
"""

from __future__ import annotations

import gettext as _gettext
from pathlib import Path

from nicegui import app, context

DOMAIN = "hollowshelf"
LOCALE_DIR = Path(__file__).resolve().parent / "locales"

DEFAULT_LANG = "en"
# code -> label shown on the header toggle
LANGUAGES = {"en": "EN", "de": "DE"}

_catalogs: dict[str, _gettext.NullTranslations] = {}


def _catalog(lang: str) -> _gettext.NullTranslations:
    """Load (and cache) the gettext catalog for a language."""
    cat = _catalogs.get(lang)
    if cat is None:
        try:
            cat = _gettext.translation(DOMAIN, LOCALE_DIR, languages=[lang])
        except FileNotFoundError:
            # English, or a not-yet-compiled catalog: identity translation.
            cat = _gettext.NullTranslations()
        _catalogs[lang] = cat
    return cat


def _browser_lang() -> str:
    """Best-effort first-run guess from the client's Accept-Language header."""
    try:
        accept = context.client.request.headers.get("accept-language", "")
    except Exception:
        return DEFAULT_LANG
    # e.g. "de-DE,de;q=0.9,en;q=0.8" -> "de"
    for part in accept.split(","):
        code = part.split(";")[0].strip().lower().split("-")[0]
        if code in LANGUAGES:
            return code
    return DEFAULT_LANG


def get_lang() -> str:
    """The current client's language, detected and persisted on first use."""
    try:
        store = app.storage.user
    except Exception:
        return DEFAULT_LANG
    lang = store.get("lang")
    if lang not in LANGUAGES:
        lang = _browser_lang()
        store["lang"] = lang
    return lang


def set_lang(lang: str) -> None:
    """Persist the client's language choice (the toggle calls this)."""
    if lang in LANGUAGES:
        try:
            app.storage.user["lang"] = lang
        except Exception:
            pass


def _(message: str) -> str:
    """Translate ``message`` into the current client's language."""
    return _catalog(get_lang()).gettext(message)


def ngettext(singular: str, plural: str, n: int) -> str:
    """Plural-aware translation (e.g. '1 book' vs '5 books' / 'Bücher')."""
    return _catalog(get_lang()).ngettext(singular, plural, n)
