#!/usr/bin/env python3
"""Convenience launcher so you can run the app without installing the package.

    python run.py

(Equivalent to ``python -m hollowshelf`` once installed with ``pip install -e .``.)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from hollowshelf.app import main  # noqa: E402

if __name__ in {"__main__", "__mp_main__"}:
    main()
