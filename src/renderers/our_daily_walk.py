"""Our Daily Walk (F.B. Meyer): title, one or more scripture quotations with
their reference, the devotion, and a closing prayer."""

from renderers import bible_link, escape

FIELDS = {"title", "reference", "scripture", "text"}


def render(key: str, entry: dict) -> str:
    paragraphs = entry["text"].split("\n\n")
    # The closing prayer (or, on three days, a short poem) reads as a distinct
    # ending; set it in italics.
    paragraphs[-1] = f"<i>{escape(paragraphs[-1])}</i>"
    paragraphs[:-1] = [escape(p) for p in paragraphs[:-1]]
    return "\n".join(
        [
            f"<u>{escape(key)}</u>",
            "",
            f"<b>{escape(entry['title'])}</b>",
            "",
            *(f"<i>{escape(line)}</i>" for line in entry["scripture"].split("\n")),
            f"— {bible_link(entry['reference'])}",
            "",
            "\n\n".join(paragraphs),
        ]
    )
