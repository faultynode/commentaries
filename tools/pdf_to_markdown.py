#!/usr/bin/env python3
"""Extract the text of a PDF file to a single Markdown file.

Usage:
    python3 tools/pdf_to_markdown.py path/to/document.pdf [-o output.md]

Requires: pypdf, pdfplumber
    pip install pypdf pdfplumber
"""

import argparse
import os

import pdfplumber
from pypdf import PdfReader


def build_frontmatter(pdf_path):
    meta = PdfReader(pdf_path).metadata
    title = meta.title if meta else None
    author = meta.author if meta else None
    lines = ["---"]
    if title:
        lines.append(f"title: {title}")
    if author:
        lines.append(f"author: {author}")
    lines.append("---\n")
    return "\n".join(lines) if len(lines) > 2 else ""


def convert(pdf_path):
    sections = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = (page.extract_text() or "").strip()
            if text:
                sections.append(text)

    return build_frontmatter(pdf_path) + "\n\n".join(sections) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf_path", help="Path to the input .pdf file")
    parser.add_argument("-o", "--output", help="Path to the output .md file")
    args = parser.parse_args()

    if not os.path.isfile(args.pdf_path):
        parser.error(f"no such file: {args.pdf_path}")

    output_path = args.output or os.path.splitext(args.pdf_path)[0] + ".md"
    markdown_text = convert(args.pdf_path)

    with open(output_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(markdown_text)

    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
