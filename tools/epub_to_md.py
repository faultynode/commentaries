#!/usr/bin/env python3
"""Convert an EPUB file to Markdown, processing one section at a time."""

import argparse
import sys
import zipfile
from pathlib import Path, PurePosixPath
from xml.etree import ElementTree as ET

import html2text

CONTAINER_PATH = "META-INF/container.xml"
CONTAINER_NS = "urn:oasis:names:tc:opendocument:xmlns:container"
OPF_NS = "http://www.idpf.org/2007/opf"


def find_opf_path(epub: zipfile.ZipFile) -> str:
    with epub.open(CONTAINER_PATH) as f:
        root = ET.parse(f).getroot()
    rootfile = root.find(f".//{{{CONTAINER_NS}}}rootfile")
    if rootfile is None:
        raise ValueError("Could not find rootfile in container.xml")
    return rootfile.attrib["full-path"]


def get_spine_hrefs(epub: zipfile.ZipFile, opf_path: str) -> list[str]:
    opf_dir = PurePosixPath(opf_path).parent

    with epub.open(opf_path) as f:
        root = ET.parse(f).getroot()

    manifest = {}
    for item in root.findall(f".//{{{OPF_NS}}}item"):
        item_id = item.attrib.get("id")
        href = item.attrib.get("href", "")
        media_type = item.attrib.get("media-type", "")
        if item_id and "html" in media_type:
            full = str(opf_dir / href) if str(opf_dir) != "." else href
            manifest[item_id] = full

    hrefs = []
    for itemref in root.findall(f".//{{{OPF_NS}}}itemref"):
        idref = itemref.attrib.get("idref", "")
        if idref in manifest:
            hrefs.append(manifest[idref])

    return hrefs


def make_converter() -> html2text.HTML2Text:
    h = html2text.HTML2Text()
    h.ignore_links = False
    h.ignore_images = True
    h.body_width = 0  # don't wrap lines
    return h


def convert(epub_path: str, output_path: str) -> None:
    converter = make_converter()

    with zipfile.ZipFile(epub_path, "r") as epub, \
         open(output_path, "w", encoding="utf-8") as out:

        opf_path = find_opf_path(epub)
        hrefs = get_spine_hrefs(epub, opf_path)
        total = len(hrefs)
        print(f"Found {total} sections in {epub_path}", file=sys.stderr)

        for i, href in enumerate(hrefs, 1):
            print(f"\rProcessing section {i}/{total}...", end="", flush=True, file=sys.stderr)
            try:
                with epub.open(href) as f:
                    html = f.read().decode("utf-8", errors="replace")
                out.write(converter.handle(html))
                out.write("\n")
            except KeyError:
                print(f"\nWarning: missing file {href!r}, skipping", file=sys.stderr)

    print(f"\nWrote {output_path}", file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert an EPUB file to Markdown.")
    parser.add_argument("input", help="Input .epub file")
    parser.add_argument(
        "output", nargs="?",
        help="Output .md file (default: same name as input with .md extension)",
    )
    args = parser.parse_args()

    output_path = args.output or str(Path(args.input).with_suffix(".md"))
    convert(args.input, output_path)


if __name__ == "__main__":
    main()
