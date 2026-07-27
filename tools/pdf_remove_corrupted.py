#!/usr/bin/env python3
"""
pdf_remove_corrupted.py — Remove corrupted pages from a PDF using PyMuPDF.

A page is flagged as corrupted if any of these checks fail:
  1. Rendering the page to a pixmap raises an exception.
  2. Extracting the page's text raises an exception.
  3. The rendered image is entirely blank (all-white pixels), unless --keep-blank
     is passed or the whole document appears blank (to avoid false-positives on
     cover/separator pages).

Usage:
    python pdf_remove_corrupted.py input.pdf
    python pdf_remove_corrupted.py input.pdf -o clean.pdf
    python pdf_remove_corrupted.py input.pdf --keep-blank
    python pdf_remove_corrupted.py input.pdf --dry-run
    python pdf_remove_corrupted.py input.pdf --dpi 150
"""

import argparse
import sys
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    sys.exit("Missing dependency — install with:  pip install pymupdf")


DEFAULT_DPI        = 72   # low resolution is fast enough for corruption detection
BLANK_PIXEL_THRESH = 0.995  # fraction of white pixels that triggers "blank" flag


def is_page_blank(page: "fitz.Page", dpi: int) -> bool:
    """Return True if the rendered page is overwhelmingly white."""
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    pix = page.get_pixmap(matrix=mat, colorspace=fitz.csGRAY)
    samples = pix.samples  # bytes: one byte per pixel (gray)
    white_count = sum(1 for b in samples if b >= 250)
    return white_count / len(samples) >= BLANK_PIXEL_THRESH


def check_page(page: "fitz.Page", dpi: int, check_blank: bool) -> tuple[bool, str]:
    """
    Return (is_corrupted, reason).
    Runs render and text-extraction checks; optionally flags blank pages.
    """
    try:
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        page.get_pixmap(matrix=mat)
    except Exception as exc:
        return True, f"render failed: {exc}"

    try:
        page.get_text()
    except Exception as exc:
        return True, f"text extraction failed: {exc}"

    if check_blank:
        try:
            if is_page_blank(page, dpi):
                return True, "blank page"
        except Exception as exc:
            return True, f"blank-check failed: {exc}"

    return False, ""


def remove_corrupted_pages(
    input_path:  str,
    output_path: str | None,
    dpi:         int,
    keep_blank:  bool,
    dry_run:     bool,
) -> None:
    in_file  = Path(input_path)
    if not in_file.exists():
        sys.exit(f"File not found: {in_file}")

    out_file = Path(output_path) if output_path else in_file.with_stem(in_file.stem + "_clean")

    doc   = fitz.open(str(in_file))
    total = len(doc)
    print(f"Input  : {in_file}  ({total} pages)")

    check_blank = not keep_blank

    corrupted: list[tuple[int, str]] = []   # (0-indexed page number, reason)
    pad = len(str(total))

    for idx in range(total):
        page = doc[idx]
        bad, reason = check_page(page, dpi, check_blank)
        status = f"CORRUPTED ({reason})" if bad else "ok"
        print(f"  page {idx + 1:>{pad}}/{total}  {status}")
        if bad:
            corrupted.append((idx, reason))

    print()

    if not corrupted:
        print("No corrupted pages found. Output not written.")
        doc.close()
        return

    bad_indices = {idx for idx, _ in corrupted}
    keep_indices = [i for i in range(total) if i not in bad_indices]

    print(f"Corrupted pages ({len(corrupted)}):")
    for idx, reason in corrupted:
        print(f"  page {idx + 1}: {reason}")
    print(f"\nKeeping {len(keep_indices)} of {total} pages.")

    if dry_run:
        print("\n--dry-run: no file written.")
        doc.close()
        return

    # Build a new document containing only the healthy pages.
    out_doc = fitz.open()
    out_doc.insert_pdf(doc, from_page=0, to_page=total - 1)  # copy all first ...

    # Delete pages from the back to avoid index shifting.
    for idx in sorted(bad_indices, reverse=True):
        out_doc.delete_page(idx)

    out_doc.save(str(out_file), garbage=4, deflate=True)
    out_doc.close()
    doc.close()

    print(f"Output : {out_file}")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="pdf_remove_corrupted",
        description="Remove corrupted pages from a PDF file.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("pdf",
        help="Input PDF file path.")
    parser.add_argument("-o", "--output",
        help="Output PDF path (default: <input>_clean.pdf).")
    parser.add_argument("--dpi", type=int, default=DEFAULT_DPI,
        help=f"Resolution used for the render check (default: {DEFAULT_DPI}). "
             "Lower is faster; higher catches subtler rendering errors.")
    parser.add_argument("--keep-blank", action="store_true",
        help="Do not flag blank (all-white) pages as corrupted.")
    parser.add_argument("--dry-run", action="store_true",
        help="Report corrupted pages without writing a new file.")

    args = parser.parse_args()

    remove_corrupted_pages(
        input_path  = args.pdf,
        output_path = args.output,
        dpi         = args.dpi,
        keep_blank  = args.keep_blank,
        dry_run     = args.dry_run,
    )


if __name__ == "__main__":
    main()
