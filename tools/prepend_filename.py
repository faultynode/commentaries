#!/usr/bin/env python3
"""Prepend a string to the filenames of selected files."""

import argparse
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Prepend a string to the filenames of selected files."
    )
    parser.add_argument("prefix", help="String to prepend to each filename")
    parser.add_argument("files", nargs="+", help="Files to rename")
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show what would be renamed without doing it"
    )
    args = parser.parse_args()

    errors = 0
    for src in (Path(f) for f in args.files):
        if not src.exists():
            print(f"Skipping {src}: file not found", file=sys.stderr)
            errors += 1
            continue

        dst = src.with_name(args.prefix + src.name)

        if dst.exists():
            print(f"Skipping {src}: destination {dst.name} already exists", file=sys.stderr)
            errors += 1
            continue

        if args.dry_run:
            print(f"{src.name}  ->  {dst.name}")
        else:
            src.rename(dst)
            print(f"{src.name}  ->  {dst.name}")

    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
