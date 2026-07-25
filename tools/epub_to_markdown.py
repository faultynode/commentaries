#!/usr/bin/env python3
"""Extract the text of an EPUB file to a single Markdown file.

Usage:
    python3 tools/epub_to_markdown.py path/to/book.epub [-o output.md]

Requires: ebooklib, beautifulsoup4, markdownify
    pip install ebooklib beautifulsoup4 markdownify
"""

import argparse
import os
import re

from bs4 import BeautifulSoup
from ebooklib import epub
from markdownify import markdownify

XML_DECLARATION_RE = re.compile(rb"^\s*<\?xml[^>]*\?>\s*")


def get_metadata(book, namespace, name):
    values = book.get_metadata(namespace, name)
    return values[0][0] if values else None


def build_frontmatter(book):
    title = get_metadata(book, "DC", "title")
    author = get_metadata(book, "DC", "creator")
    lines = ["---"]
    if title:
        lines.append(f"title: {title}")
    if author:
        lines.append(f"author: {author}")
    lines.append("---\n")
    return "\n".join(lines) if len(lines) > 2 else ""


def spine_documents(book):
    for idref, _linear in book.spine:
        item = book.get_item_with_id(idref)
        if item is not None and item.is_chapter():
            yield item


def convert(epub_path):
    book = epub.read_epub(epub_path)

    sections = []
    for item in spine_documents(book):
        content = XML_DECLARATION_RE.sub(b"", item.get_content())
        soup = BeautifulSoup(content, "html.parser")
        for tag in soup.find_all(["script", "style"]):
            tag.decompose()
        md = markdownify(str(soup), heading_style="ATX").strip()
        if md:
            sections.append(md)

    return build_frontmatter(book) + "\n\n".join(sections) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("epub_path", help="Path to the input .epub file")
    parser.add_argument("-o", "--output", help="Path to the output .md file")
    args = parser.parse_args()

    if not os.path.isfile(args.epub_path):
        parser.error(f"no such file: {args.epub_path}")

    output_path = args.output or os.path.splitext(args.epub_path)[0] + ".md"
    markdown_text = convert(args.epub_path)

    with open(output_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(markdown_text)

    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
