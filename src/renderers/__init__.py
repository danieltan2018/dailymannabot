"""Shared helpers for turning a day's data entry into a Telegram HTML message.

Each renderer module exposes:
    FIELDS  – the set of keys every entry in its data file must have
    render(key, entry) -> str
"""

import html
import urllib.parse


def escape(text: str) -> str:
    """Telegram HTML only requires <, > and & to be escaped."""
    return html.escape(text, quote=False)


def bible_link(ref: str) -> str:
    query = urllib.parse.urlencode({"search": ref, "version": "KJV"})
    return f'<a href="https://www.biblegateway.com/passage/?{query}">{escape(ref)}</a>'
