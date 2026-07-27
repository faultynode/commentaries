#!/usr/bin/env python3
"""Combine multiple markdown files into one, sorted by filename."""

import argparse
import sys
from pathlib import Path


def combine_markdown(input_dir: str, output_file: str, separator: str = "\n\n---\n\n") -> None:
    source = Path(input_dir)
    if not source.is_dir():
        print(f"Error: '{input_dir}' is not a directory.", file=sys.stderr)
        sys.exit(1)

    md_files = sorted(source.glob("*.md"))
    if not md_files:
        print(f"No .md files found in '{input_dir}'.", file=sys.stderr)
        sys.exit(1)

    parts = []
    for path in md_files:
        content = path.read_text(encoding="utf-8").strip()
        if content:
            parts.append(content)
        print(f"  + {path.name}")

    combined = separator.join(parts) + "\n"
    Path(output_file).write_text(combined, encoding="utf-8")
    print(f"\nWrote {len(parts)} files -> {output_file}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Combine markdown files in filename order.")
    parser.add_argument("input_dir", help="Directory containing .md files")
    parser.add_argument("output_file", help="Output .md file path")
    parser.add_argument(
        "--separator",
        default="\n\n---\n\n",
        help="String inserted between files (default: horizontal rule)",
    )
    args = parser.parse_args()
    combine_markdown(args.input_dir, args.output_file, args.separator)


if __name__ == "__main__":
    main()
