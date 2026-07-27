#!/usr/bin/env python3
"""Convert DjVu to Markdown by parsing the structured text layer via djvused."""

import argparse
import subprocess
import sys
from pathlib import Path


def get_page_count(djvu_path: str) -> int:
    result = subprocess.run(
        ["djvused", djvu_path, "-e", "n"],
        capture_output=True, text=True, check=True
    )
    return int(result.stdout.strip())


def get_page_sexp(djvu_path: str, page: int) -> str:
    result = subprocess.run(
        ["djvused", djvu_path, "-e", f"select {page}; print-txt"],
        capture_output=True, text=True, check=True
    )
    return result.stdout


# --- S-expression parser ---

def tokenize(s: str) -> list[str]:
    tokens = []
    i = 0
    while i < len(s):
        c = s[i]
        if c in " \t\n\r":
            i += 1
        elif c in "()":
            tokens.append(c)
            i += 1
        elif c == '"':
            j = i + 1
            buf = []
            while j < len(s) and s[j] != '"':
                if s[j] == '\\' and j + 1 < len(s):
                    j += 1
                    buf.append(s[j])
                else:
                    buf.append(s[j])
                j += 1
            tokens.append("".join(buf))
            i = j + 1
        else:
            j = i
            while j < len(s) and s[j] not in ' \t\n\r()"':
                j += 1
            tokens.append(s[i:j])
            i = j
    return tokens


def parse_sexp(tokens: list[str], pos: list[int]):
    if pos[0] >= len(tokens):
        return None
    tok = tokens[pos[0]]
    if tok == "(":
        pos[0] += 1
        lst = []
        while pos[0] < len(tokens) and tokens[pos[0]] != ")":
            lst.append(parse_sexp(tokens, pos))
        pos[0] += 1  # consume ')'
        return lst
    else:
        pos[0] += 1
        return tok


# --- Text extraction ---
# djvused zone format: (zone-type x1 y1 x2 y2 child ...)
# word nodes:          (word x1 y1 x2 y2 "text")
# Hierarchy:           page > column > region > para > line > word

def collect_words(node) -> list[str]:
    if not isinstance(node, list) or not node:
        return []
    zone_type = node[0]
    if zone_type == "word":
        text = node[5] if len(node) > 5 else None
        return [text] if isinstance(text, str) else []
    return [w for child in node[5:] if isinstance(child, list)
            for w in collect_words(child)]


def extract_paragraphs(node) -> list[str]:
    if not isinstance(node, list) or not node:
        return []
    zone_type = node[0]
    children = [c for c in node[5:] if isinstance(c, list)]

    if zone_type == "word":
        text = node[5] if len(node) > 5 else None
        return [text] if isinstance(text, str) else []

    if zone_type == "para":
        words = collect_words(node)
        text = " ".join(words).strip()
        return [text] if text else []

    if zone_type == "line":
        # Line without a para parent — treat as its own paragraph.
        words = collect_words(node)
        text = " ".join(words).strip()
        return [text] if text else []

    # page, column, region: recurse and collect paragraphs from children
    paras = []
    for child in children:
        paras.extend(extract_paragraphs(child))
    return paras


def page_to_markdown(djvu_path: str, page: int) -> str:
    raw = get_page_sexp(djvu_path, page)
    if not raw.strip():
        return ""
    tokens = tokenize(raw)
    tree = parse_sexp(tokens, [0])
    if not tree:
        return ""
    paragraphs = extract_paragraphs(tree)
    return "\n\n".join(p for p in paragraphs if p)


def convert(djvu_path: str, output_path: str) -> None:
    page_count = get_page_count(djvu_path)
    print(f"Found {page_count} pages in {djvu_path}", file=sys.stderr)

    with open(output_path, "w", encoding="utf-8") as out:
        for page in range(1, page_count + 1):
            print(f"\rProcessing page {page}/{page_count}...", end="", flush=True, file=sys.stderr)
            md = page_to_markdown(djvu_path, page)
            if md:
                out.write(md)
                out.write("\n\n")

    print(f"\nWrote {output_path}", file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert DjVu to Markdown using the structured text layer."
    )
    parser.add_argument("input", help="Input .djvu file")
    parser.add_argument(
        "output", nargs="?",
        help="Output .md file (default: same name as input with .md extension)",
    )
    args = parser.parse_args()

    output_path = args.output or str(Path(args.input).with_suffix(".md"))
    convert(args.input, output_path)


if __name__ == "__main__":
    main()
