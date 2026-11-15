"""Console entry point: resolve paths, then hand over to the app.

Deliberately free of ``nicegui`` imports (directly or via ``.app``/``.i18n``):
NiceGUI resolves ``NICEGUI_STORAGE_PATH`` the moment the package is imported,
so the environment has to be final before ``.app`` loads. That is also why the
CLI help text stays outside gettext for now.
"""

from __future__ import annotations

import argparse
import os


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="hollowshelf",
        description="A personal book library.",
    )
    parser.add_argument(
        "--data-dir",
        metavar="PATH",
        help=(
            "directory for the library and UI storage "
            "(default: the OS user-data directory; "
            "equivalent to setting HOLLOWSHELF_DATA_DIR)"
        ),
    )
    return parser.parse_args(argv)


def _configure_environment(args: argparse.Namespace) -> None:
    """Fix paths in the environment so the native-mode subprocess inherits them."""
    from . import config

    if args.data_dir:
        os.environ[config.DATA_DIR_ENV] = str(args.data_dir)
    storage = config.storage_dir()
    storage.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("NICEGUI_STORAGE_PATH", str(storage))


def main() -> None:
    _configure_environment(_parse_args())

    from .app import main as run_app

    run_app()


if __name__ in {"__main__", "__mp_main__"}:
    main()
