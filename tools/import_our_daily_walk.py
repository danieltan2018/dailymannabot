"""Convert the Lifers app's Our Daily Walk data into this repo's channel format.

    python3 tools/import_our_daily_walk.py ~/Downloads/lifers-app/src/data/devotion/ourDailyWalk.json

The source is F.B. Meyer's *Our Daily Walk*, transcribed from Life BPC's PDFs
(lifebpc.com/images/bookstracts/Meyr0107.pdf … Meyr0407.pdf) by the parser in
the Lifers repo (tools/devotions/). Text is public domain and is kept verbatim:
curly quotes, closed-up em-dashes, ALL CAPS titles, scripture already quoted.
The only change here is shape: the list of {month, day, ...} becomes a dict
keyed "D MONTH", and the scripture/paragraph lists become newline-joined strings.
"""

import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from channels import date_key  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "src" / "data" / "our_daily_walk.json"


def main(source):
    entries = json.load(open(source, encoding="utf-8"))
    out = {}
    for e in entries:
        key = date_key(date(2024, e["month"], e["day"]))   # 2024 is a leap year, so 29 Feb is valid
        assert key not in out, f"duplicate {key}"
        out[key] = {
            "title": e["title"],
            "reference": e["reference"],
            "scripture": "\n".join(e["scripture"]),
            "text": "\n\n".join(e["paragraphs"]),
        }
    with OUT.open("w", encoding="utf-8") as f:
        json.dump(out, f, indent=4, ensure_ascii=False)
        f.write("\n")
    print(f"wrote {len(out)} entries to {OUT}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
