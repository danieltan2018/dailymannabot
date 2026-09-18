"""Minimal Telegram Bot API client — just enough to post a message."""

import json
import os
import urllib.error
import urllib.request

TELEGRAM_MAX_LENGTH = 4096


def send_message(chat_id: str, text: str, token: str = None, **options) -> dict:
    """POST sendMessage. Raises on any HTTP or API-level failure."""
    token = token or os.environ.get("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN environment variable is not set")
    body = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "link_preview_options": {"is_disabled": True},
        **options,
    }
    request = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            result = json.load(response)
    except urllib.error.HTTPError as e:
        # Telegram returns 4xx with a JSON body explaining what was wrong.
        raise RuntimeError(f"Telegram API error {e.code}: {e.read().decode('utf-8', 'replace')}") from e
    if not result.get("ok"):
        raise RuntimeError(f"Telegram API returned failure: {result}")
    return result
