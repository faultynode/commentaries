#!/usr/bin/env python3
"""Insert or refresh a table of contents in the close-reading files.

Usage:
    python scripts/add_toc.py                 # all outputs/*close-readings.md
    python scripts/add_toc.py FILE [FILE...]  # specific files
    python scripts/add_toc.py --check         # exit 1 if any TOC is stale

The TOC sits directly under the level-1 heading, between the markers
<!-- toc:start --> and <!-- toc:end -->, so re-running replaces it in place.
Anchors follow GitHub's slug rules (also used by Jekyll's GFM parser).
"""
import re
import sys
import unicodedata
from pathlib import Path

START, END = "<!-- toc:start -->", "<!-- toc:end -->"
TITLE = "Contents"
MAX_LEVEL = 3  # include ## and ###
DEFAULT_GLOB = "outputs/*close-readings.md"
HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")


def plain(text):
    text = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"[`*~]+", "", text)
    return re.sub(r"<[^>]+>", "", text).strip()


def slug(text):
    text = unicodedata.normalize("NFC", plain(text)).lower()
    text = re.sub(r"[^\w\- ]", "", text)
    return text.replace(" ", "-")


def split_front_matter(lines):
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                return i + 1
    return 0


def headings(lines, start):
    seen, fence, out = {}, None, []
    for line in lines[start:]:
        m = re.match(r"^\s*(```+|~~~+)", line)
        if m:
            fence = None if fence == m.group(1)[:3] else (fence or m.group(1)[:3])
            continue
        if fence:
            continue
        h = HEADING.match(line)
        if not h:
            continue
        level, text = len(h.group(1)), h.group(2)
        base = slug(text)
        n = seen.get(base, 0)
        seen[base] = n + 1
        out.append((level, plain(text), base if n == 0 else f"{base}-{n}"))
    return out


def build_toc(entries):
    items = [e for e in entries if 2 <= e[0] <= MAX_LEVEL]
    if not items:
        return None
    lines = [START, f"**{TITLE}**", ""]
    for level, text, anchor in items:
        lines.append(f"{'  ' * (level - 2)}- [{text}](#{anchor})")
    lines.append(END)
    return "\n".join(lines)


def process(text):
    lines = text.split("\n")
    body = split_front_matter(lines)
    # drop any existing TOC so it is not listed or duplicated
    s = next((i for i, l in enumerate(lines) if l.strip() == START), None)
    e = next((i for i, l in enumerate(lines) if l.strip() == END), None)
    if s is not None and e is not None and e > s:
        end = e + 1
        if end < len(lines) and lines[end] == "" and s > 0 and lines[s - 1] == "":
            end += 1
        del lines[s:end]
    entries = headings(lines, body)
    toc = build_toc(entries)
    if toc is None:
        return text
    h1 = next((i for i in range(body, len(lines))
               if re.match(r"^#\s+\S", lines[i])), None)
    at = h1 + 1 if h1 is not None else body
    new = lines[:at] + ["", toc] + lines[at:]
    return "\n".join(new)


def main(argv):
    check = "--check" in argv
    files = [Path(a) for a in argv if not a.startswith("--")]
    if not files:
        files = sorted(Path(".").glob(DEFAULT_GLOB))
    stale = 0
    for f in files:
        old = f.read_text(encoding="utf-8")
        new = process(old)
        if new == old:
            print(f"ok       {f}")
        elif check:
            print(f"stale    {f}")
            stale += 1
        else:
            f.write_text(new, encoding="utf-8")
            print(f"updated  {f}")
    return 1 if stale else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
