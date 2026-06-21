"""Manual smoke test:  python -m hollowshelf.book_client"""

from __future__ import annotations

from . import BookClient


def main() -> None:
    client = BookClient(contact="you@example.com")

    book = client.search_by_isbn("9783866470117")   # German edition
    print(book)

    for hit in client.search_by_title("Der Vorleser", language="de", limit=3):
        print(f"{hit.title} — {', '.join(hit.authors)} ({hit.year}) [{hit.media}]")

    client.close()


if __name__ == "__main__":
    main()
