"""The registry of devotion channels.

To add a channel: drop its data file in data/, write (or reuse) a renderer,
add an entry here, and add a matching schedule in template.yaml.
"""

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from types import ModuleType

from renderers import psalms

DATA_DIR = Path(__file__).with_name("data")


@dataclass(frozen=True)
class Channel:
    name: str
    chat_id: str          # Telegram channel username or numeric chat id
    data_file: str        # relative to data/
    renderer: ModuleType  # module exposing FIELDS and render(key, entry)
    timezone: str = "Asia/Singapore"

    def load_data(self) -> dict:
        with (DATA_DIR / self.data_file).open(encoding="utf-8") as f:
            return json.load(f)

    def render(self, key: str, entry: dict) -> str:
        return self.renderer.render(key, entry)


CHANNELS = {
    "psalms": Channel(
        name="psalms",
        chat_id="@thruthepsalms",
        data_file="psalms.json",
        renderer=psalms,
    ),
}


def date_key(day: date) -> str:
    """'2 MAY' — the key format used in every data file (no zero-padding)."""
    return f"{day.day} {day:%B}".upper()
