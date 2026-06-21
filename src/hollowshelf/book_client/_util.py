"""Small parsing helpers shared across providers."""

from __future__ import annotations

from typing import Optional


def parse_year(date_str) -> Optional[int]:
    """Pull a 4-digit year out of whatever date string an API hands back."""
    if not date_str:
        return None
    for token in str(date_str).replace("-", " ").split():
        if token.isdigit() and len(token) == 4:
            return int(token)
    return None
