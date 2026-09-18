"""Regenerate src/data/psalms.json from the source PDF.

    python3 -m venv .venv && .venv/bin/pip install pymupdf
    .venv/bin/python tools/extract_psalms.py ~/Downloads/CBPC-Psalm-ver2.pdf

The book is "Thru' the Psalms in one year with Spurgeon's Treasury of David"
(Isaac Ong, Calvary Bible-Presbyterian Church, 2012). One page per day; each
page carries the day number, month, psalm reference, title, key verse and the
devotion body. Everything is read from the PDF's text layer by font, so the
result is deterministic. The PDF itself is not committed.
"""

import json
import re
import sys
from collections import Counter
from pathlib import Path

import fitz  # PyMuPDF

OUT = Path(__file__).resolve().parent.parent / "src" / "data" / "psalms.json"
MONTHS = "JANUARY FEBRUARY MARCH APRIL MAY JUNE JULY AUGUST SEPTEMBER OCTOBER NOVEMBER DECEMBER".split()

# The print has the citation's full stop on the wrong side in two places.
# We keep the sentence's stop before the citation and nothing after it,
# which is what every other day does and what the tests check for.
VERSE_FIXES = {
    "4 JUNE": ("overflow me (Psalm 69:2).", "overflow me. (Psalm 69:2)"),
    "14 NOVEMBER": ("(Psalm 121:1-2).", "(Psalm 121:1-2)"),
}


def font(span):
    return span["font"].replace("MyriadPro-", "")


def span_text(span):
    text = span["text"].replace("\u00ad", "").replace("\u00a0", " ")   # soft hyphens, nbsp
    if "SC700" in span["font"]:                  # small caps: "L" + "ord" -> LORD
        text = text.upper()
    if font(span).startswith("Wingdings"):       # end-of-devotion square
        text = ""
    return text


def tidy(text):
    text = re.sub(r"(?<=\S) ?\. \. \.", "…", text)   # spaced ellipsis
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r" {2,}", " ", text)
    return text.strip()


def is_tab_line(line):
    text = "".join(s["text"] for s in line["spans"])
    return "\t" in text and not text.strip("\t ")


def extract(page):
    lines = [l for b in page.get_text("dict")["blocks"] for l in b.get("lines", [])]
    # Tab-only lines mark the paragraph that follows; nudge them ahead of text
    # on the same row so rounding cannot put them after it.
    lines.sort(key=lambda l: (round(l["bbox"][1] - (3 if is_tab_line(l) else 0)), l["bbox"][0]))

    day = month = psalm = None
    title, verse, body = [], [], []
    for line in lines:
        spans = line["spans"]
        kinds = {(font(s), round(s["size"])) for s in spans}
        # Header pieces are matched per span: on right-hand pages the day
        # number and the psalm reference share a line.
        for s in spans:
            f, size = font(s), round(s["size"])
            if (f, size) == ("Cond", 36):
                day = s["text"].strip()
            elif f == "Carnelian":
                psalm = s["text"].strip()
            elif (f, size) == ("BlackCond", 12) and s["text"].strip().upper() in MONTHS:
                month = s["text"].strip().upper()   # May is typeset "May"
        if kinds & {("Cond", 36), ("Carnelian", 48), ("BlackCond", 12)}:
            continue
        text = "".join(span_text(s) for s in spans)
        if kinds & {("Bold", 16), ("Bold-SC700", 16)}:
            title.append(text.strip())
        elif kinds & {("BoldIt", 12), ("BoldIt-SC700", 12)}:
            verse.append(text.strip())
        elif kinds == {("Regular", 10)}:
            pass                                             # side tab "Jan"
        elif ("Regular", 31) in kinds and len(text.strip()) <= 2:
            body.append(("dropcap", line["bbox"][1], text))  # drop cap, maybe with a quote mark
        elif any(size in (11, 31) for _, size in kinds):
            row_y = min((s["bbox"][1] for s in spans if s["text"].strip()), default=line["bbox"][1])
            body.append((line["bbox"][0], row_y, text))
    if not (day and month and psalm):
        return None

    # Body lines -> items. A paragraph break is a tab line (sometimes glued to
    # the start of the next line), a vertical gap, or a first-line indent.
    # Poems are runs of consecutive indented lines, at the paragraph indent
    # (14pt) or deeper (28pt).
    items = []
    dropcap, after_dropcap, prev_y = "", 0, None
    margin = min(x for x, _, t in body if x != "dropcap" and t.strip() and t != "\t")
    for x, y, text in body:
        if x == "dropcap":
            dropcap, after_dropcap = text.lstrip(), 2         # keep trailing space: "I " + "delight"
            continue
        if dropcap:                                          # "O" + "ne of..." / "I" + " delight..."
            text, dropcap = dropcap + text, ""
        if prev_y is not None and y - prev_y >= 20:
            items.append("tab")
        prev_y = y
        if after_dropcap:
            cls, after_dropcap = "cont", after_dropcap - 1  # lines beside the drop cap
        else:
            cls = "cont" if x - margin < 8 else "indent"
        # A tab marks a paragraph break; it may start the line or sit mid-line.
        for i, part in enumerate(text.split("\t")):
            if i:
                items.append("tab")
            if part.strip():
                items.append((cls, part.strip()))

    paras, cur = [], []
    def flush():
        if cur:
            paras.append(list(cur))
            cur.clear()
    for item in items:
        if item == "tab":
            flush()
            continue
        cls, text = item
        if cls == "indent" and cur and cur[-1][0] == "cont":
            flush()                                          # indented line after prose
        elif cls == "cont" and len(cur) >= 2 and all(c == "indent" for c, _ in cur):
            flush()                                          # prose resuming after a poem
        cur.append((cls, text))
    flush()

    def render(lines):
        if len(lines) >= 2 and all(c == "indent" for c, _ in lines):   # poem
            out = ""
            for _, t in lines:
                if out and not re.search(r"[.,;:!?\"'”’)]$", out) and t[:1].islower():
                    out += " " + t                           # wrapped long poem line
                else:
                    out += ("\n" if out else "") + t
            return out
        out = ""
        for _, t in lines:
            out += t if out.endswith("-") else (" " if out else "") + t
        return out

    return {
        "day": int(day),
        "month": month,
        "psalm": psalm,
        "title": tidy(" ".join(title)),
        "verse": tidy(" ".join(verse)),
        "text": tidy("\n\n".join(render(p) for p in paras)),
    }


def main(pdf_path):
    doc = fitz.open(pdf_path)
    entries = {}
    for page in doc:
        e = extract(page)
        if not e:
            continue
        key = f"{e['day']} {e['month']}"
        if key in entries:
            sys.exit(f"duplicate entry for {key} on page {page.number + 1}")
        entries[key] = {"psalm": e["psalm"], "title": e["title"], "verse": e["verse"], "text": e["text"]}
    for key, (old, new) in VERSE_FIXES.items():
        assert old in entries[key]["verse"], f"{key}: expected {old!r} in verse"
        entries[key]["verse"] = entries[key]["verse"].replace(old, new)

    print(f"{len(entries)} entries:", dict(Counter(k.split()[1] for k in entries)))
    with OUT.open("w", encoding="utf-8") as f:
        json.dump(entries, f, indent=4, ensure_ascii=False)
        f.write("\n")
    print("wrote", OUT)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
