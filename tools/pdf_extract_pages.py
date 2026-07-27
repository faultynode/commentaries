#!/usr/bin/env python3
"""
pdf_extract_pages.py — Extract a range of pages from a PDF into a new file.

Usage:
    python pdf_extract_pages.py input.pdf 1-30
    python pdf_extract_pages.py input.pdf 3,5,7
    python pdf_extract_pages.py input.pdf 1-5,8,10-15
    python pdf_extract_pages.py input.pdf 1-30 -o chapter1.pdf
"""

import argparse
import sys
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    sys.exit("Missing dependency — install with:  pip install pymupdf")


def parse_page_range(spec: str, total: int) -> list[int]:
    """Parse '1-10', '3,5,7', or '1-5,8,10-15' into sorted 0-indexed page list."""
    pages: set[int] = set()
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-", 1)
            pages.update(range(int(a) - 1, min(int(b), total)))
        else:
            n = int(part) - 1
            if 0 <= n < total:
                pages.add(n)
    return sorted(pages)


def extract_pages(input_path: str, page_spec: str, output_path: str | None) -> None:
    in_file = Path(input_path)
    if not in_file.exists():
        sys.exit(f"File not found: {in_file}")

    doc   = fitz.open(str(in_file))
    total = len(doc)

    indices = parse_page_range(page_spec, total)
    if not indices:
        sys.exit(f"No valid pages in range '{page_spec}' (document has {total} pages).")

    out_file = Path(output_path) if output_path else in_file.with_stem(
        f"{in_file.stem}_pages_{page_spec.replace(',', '_').replace('-', '-')}"
    )

    out_doc = fitz.open()
    for idx in indices:
        out_doc.insert_pdf(doc, from_page=idx, to_page=idx)

    out_doc.save(str(out_file), garbage=4, deflate=True)
    out_doc.close()
    doc.close()

    print(f"Extracted {len(indices)} page(s) → {out_file}")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="pdf_extract_pages",
        description="Extract a page range from a PDF into a new file.",
    )
    parser.add_argument("pdf", help="Input PDF file path.")
    parser.add_argument("pages",
        help="1-indexed page range: '1-30', '3,5,7', or '1-5,8,10-15'.")
    parser.add_argument("-o", "--output",
        help="Output PDF path (default: <input>_pages_<range>.pdf).")

    args = parser.parse_args()
    extract_pages(args.pdf, args.pages, args.output)


if __name__ == "__main__":
    main()
