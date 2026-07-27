#!/usr/bin/env python3
"""Extract the text of an AZW3 file to a single Markdown file.

Usage:
    python3 tools/azw3_to_markdown.py path/to/book.azw3 [-o output.md]

Requires: mobi, ebooklib, beautifulsoup4, markdownify
    pip install mobi ebooklib beautifulsoup4 markdownify
"""

import argparse
import os
import shutil

import mobi

from epub_to_markdown import convert as convert_epub


def convert(azw3_path):
    tempdir, extracted_path = mobi.extract(azw3_path)
    try:
        if not extracted_path.endswith(".epub"):
            raise ValueError(f"could not find an unpacked epub for {azw3_path}")
        return convert_epub(extracted_path)
    finally:
        shutil.rmtree(tempdir, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("azw3_path", help="Path to the input .azw3 file")
    parser.add_argument("-o", "--output", help="Path to the output .md file")
    args = parser.parse_args()

    if not os.path.isfile(args.azw3_path):
        parser.error(f"no such file: {args.azw3_path}")

    output_path = args.output or os.path.splitext(args.azw3_path)[0] + ".md"
    markdown_text = convert(args.azw3_path)

    with open(output_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(markdown_text)

    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
