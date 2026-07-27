#!/usr/bin/env python3
"""Extract the text of a DjVu file to a single Markdown file.

Only pages with an embedded text layer (e.g. produced by OCR) yield
text; a scanned DjVu with no text layer produces empty output.

Usage:
    python3 tools/djvu_to_markdown.py path/to/document.djvu [-o output.md]

Requires: djvulibre-bin (djvutxt, djvused)
    apt-get install djvulibre-bin
"""

import argparse
import os
import re
import subprocess

META_LINE_RE = re.compile(r'^(\w+)\t"(.*)"$')


def unescape_djvu_string(value):
    result = bytearray()
    i = 0
    while i < len(value):
        char = value[i]
        if char == "\\" and i + 1 < len(value):
            nxt = value[i + 1]
            if nxt.isdigit():
                result.append(int(value[i + 1:i + 4], 8))
                i += 4
                continue
            result.append(ord(nxt))
            i += 2
            continue
        result.append(ord(char))
        i += 1
    return result.decode("utf-8")


def read_metadata(djvu_path):
    output = subprocess.run(
        ["djvused", "-e", "print-meta", djvu_path],
        capture_output=True, text=True, check=True,
    ).stdout

    metadata = {}
    for line in output.splitlines():
        match = META_LINE_RE.match(line)
        if match:
            key, value = match.groups()
            metadata[key] = unescape_djvu_string(value)
    return metadata


def build_frontmatter(metadata):
    title = metadata.get("Title")
    author = metadata.get("Author")
    lines = ["---"]
    if title:
        lines.append(f"title: {title}")
    if author:
        lines.append(f"author: {author}")
    lines.append("---\n")
    return "\n".join(lines) if len(lines) > 2 else ""


def convert(djvu_path):
    text = subprocess.run(
        ["djvutxt", djvu_path],
        capture_output=True, text=True, check=True,
    ).stdout.strip()

    return build_frontmatter(read_metadata(djvu_path)) + text + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("djvu_path", help="Path to the input .djvu file")
    parser.add_argument("-o", "--output", help="Path to the output .md file")
    args = parser.parse_args()

    if not os.path.isfile(args.djvu_path):
        parser.error(f"no such file: {args.djvu_path}")

    output_path = args.output or os.path.splitext(args.djvu_path)[0] + ".md"
    markdown_text = convert(args.djvu_path)

    with open(output_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(markdown_text)

    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
