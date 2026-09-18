"""AWS Lambda entry point.

Each EventBridge schedule invokes this with {"channel": "<name>"}. For manual
testing you can also pass "date" (ISO, e.g. "2024-05-02") and "chat_id" (to
post somewhere other than the channel's real chat).

Any failure — unknown channel, missing date entry, Telegram error — raises,
so the invocation is recorded as failed in CloudWatch and nothing reaches
subscribers.
"""

from datetime import date, datetime
from zoneinfo import ZoneInfo

import telegram
from channels import CHANNELS, date_key


def lambda_handler(event, context):
    event = event or {}
    try:
        channel = CHANNELS[event["channel"]]
    except KeyError:
        raise ValueError(f"event must name a channel from {sorted(CHANNELS)}; got {event!r}") from None

    if event.get("date"):
        day = date.fromisoformat(event["date"])
    else:
        day = datetime.now(ZoneInfo(channel.timezone)).date()
    key = date_key(day)

    text = channel.render(key, channel.load_data()[key])
    result = telegram.send_message(event.get("chat_id") or channel.chat_id, text)
    return {
        "channel": channel.name,
        "date": key,
        "chat_id": result["result"]["chat"].get("username") or result["result"]["chat"]["id"],
        "message_id": result["result"]["message_id"],
    }
