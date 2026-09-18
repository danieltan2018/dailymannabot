"""Through the Psalms: one psalm passage, a title, a key verse and a devotion."""

from renderers import bible_link, escape

FIELDS = {"psalm", "title", "verse", "text"}


def render(key: str, entry: dict) -> str:
    return "\n".join(
        [
            f"<u>{escape(key)}</u>",
            "",
            f"<b>{bible_link(entry['psalm'])}</b>",
            f"<b>{escape(entry['title'])}</b>",
            "",
            f"<i>{escape(entry['verse'])}</i>",
            "",
            escape(entry["text"]),
        ]
    )
