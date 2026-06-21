"""Best-effort media-type detection.

Free metadata is unreliable about whether an edition is print, ebook, or
audiobook, so treat the result as a hint only and let users correct it in the
UI. Providers feed in whatever fields they have (format strings, titles,
subtitles) and we sniff for keywords.
"""

from __future__ import annotations

from typing import Optional

_AUDIO_HINTS = ("audio", "hörbuch", "hoerbuch", "audible", "mp3", "spoken", "cd")
_EBOOK_HINTS = ("ebook", "e-book", "kindle", "epub", "electronic")
_PRINT_HINTS = ("paperback", "hardcover", "hardback", "taschenbuch", "gebunden", "print")


def detect_media(*hints: Optional[str]) -> str:
    blob = " ".join(h for h in hints if h).lower()
    if any(k in blob for k in _AUDIO_HINTS):
        return "audiobook"
    if any(k in blob for k in _EBOOK_HINTS):
        return "ebook"
    if any(k in blob for k in _PRINT_HINTS):
        return "print"
    return "unknown"
