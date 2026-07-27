#!/usr/bin/env python3
"""
onenote_extractor.py — Export Microsoft OneNote notebooks/sections/pages to Markdown.

Connects to the OneNote desktop application via COM automation (Windows only).
Reads page content as OneNote XML and converts it to clean Markdown, preserving
headings, bullet and numbered lists, nested lists, tables, bold, italic, and
inline code.

Usage:
    python onenote_extractor.py                           # list notebooks
    python onenote_extractor.py --list                    # same
    python onenote_extractor.py --notebook "My Notes"     # export one notebook
    python onenote_extractor.py --all                     # export all notebooks
    python onenote_extractor.py --notebook "Research" --section "Chapter 1"
    python onenote_extractor.py --notebook "Research" -o ./output/

Requirements:
    pip install pywin32

    Microsoft OneNote for Desktop (Microsoft 365 / Office 2016+) must be installed.
    The UWP "OneNote for Windows 10" store app does NOT expose a COM interface;
    use File → Export in that app to save a .docx, then convert with pandoc.
"""

import argparse
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from typing import Optional
from xml.etree import ElementTree as ET


# ---------------------------------------------------------------------------
# Namespace constants
# ---------------------------------------------------------------------------

_NS_2013 = "http://schemas.microsoft.com/office/onenote/2013/onenote"
_NS_2010 = "http://schemas.microsoft.com/office/onenote/2010/onenote"
_ALL_NS  = (_NS_2013, _NS_2010)

# OneNote hierarchy scopes (HierarchyScope enum)
_HS_NOTEBOOKS = 0
_HS_SECTIONS  = 2
_HS_PAGES     = 3

# PageInfo: 0 = basic text content (no binary/image data embedded in XML)
_PAGE_INFO_BASIC = 0


# ---------------------------------------------------------------------------
# Inline HTML → Markdown converter
# ---------------------------------------------------------------------------

class _SpanConverter(HTMLParser):
    """
    Convert the XHTML snippets inside one:T CDATA to Markdown inline marks.
    OneNote encodes bold/italic/code as inline CSS on <span> elements.
    """

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self._stack:  list[str] = []
        self._parts:  list[str] = []
        self._bold   = 0
        self._italic = 0
        self._code   = 0

    def handle_starttag(self, tag: str, attrs):
        style = dict(attrs).get("style", "")
        if tag == "span":
            if "font-weight:bold" in style:
                self._bold += 1
                self._stack.append("bold")
            elif "font-style:italic" in style:
                self._italic += 1
                self._stack.append("italic")
            elif any(f in style for f in ("Consolas", "Courier", "monospace")):
                self._code += 1
                self._stack.append("code")
            else:
                self._stack.append("span")
        elif tag in ("b", "strong"):
            self._bold += 1
            self._stack.append("bold")
        elif tag in ("i", "em"):
            self._italic += 1
            self._stack.append("italic")
        elif tag == "code":
            self._code += 1
            self._stack.append("code")
        elif tag == "br":
            self._parts.append("  \n")
            self._stack.append("br")
        else:
            self._stack.append(tag)

    def handle_endtag(self, _tag: str):
        if not self._stack:
            return
        closed = self._stack.pop()
        if closed == "bold":
            self._bold   = max(0, self._bold   - 1)
        elif closed == "italic":
            self._italic = max(0, self._italic - 1)
        elif closed == "code":
            self._code   = max(0, self._code   - 1)

    def handle_data(self, data: str):
        if not data:
            return
        if self._code:
            self._parts.append(f"`{data}`")
        elif self._bold and self._italic:
            self._parts.append(f"***{data}***")
        elif self._bold:
            self._parts.append(f"**{data}**")
        elif self._italic:
            self._parts.append(f"*{data}*")
        else:
            self._parts.append(data)

    def result(self) -> str:
        return "".join(self._parts)


def _t_to_md(t_elem) -> str:
    """Extract Markdown text from a one:T element (CDATA may contain XHTML)."""
    raw = t_elem.text or ""
    if not raw:
        return ""
    if "<" not in raw:
        return raw
    conv = _SpanConverter()
    try:
        conv.feed(raw)
        return conv.result()
    except Exception:
        return re.sub(r"<[^>]+>", "", raw)


# ---------------------------------------------------------------------------
# XML helpers
# ---------------------------------------------------------------------------

def _tag(elem, local: str) -> Optional[ET.Element]:
    """Find first child with local tag name, trying all known namespaces."""
    for ns in _ALL_NS:
        found = elem.find(f"{{{ns}}}{local}")
        if found is not None:
            return found
    return None


def _tags(elem, local: str):
    """Find all children with local tag name, trying all known namespaces."""
    for ns in _ALL_NS:
        results = elem.findall(f"{{{ns}}}{local}")
        if results:
            return results
    return []


def _iter_tag(elem, local: str):
    """Iterate over all descendants with local tag name."""
    for ns in _ALL_NS:
        for child in elem.iter(f"{{{ns}}}{local}"):
            yield child


# ---------------------------------------------------------------------------
# Quick-style index → name
# ---------------------------------------------------------------------------

_DEFAULT_STYLES: dict[int, str] = {
    0: "p",
    1: "h1",   # Page Title style (large bold)
    2: "h2",   # Heading 1
    3: "h3",   # Heading 2
    4: "h4",   # Heading 3
    5: "h5",   # Heading 4
    6: "h6",   # Heading 5
    7: "h6",   # Heading 6
    10: "cite",
    11: "code",
    12: "p",
    13: "blockquote",
}


def _parse_quick_styles(root) -> dict[int, str]:
    """Read QuickStyleDef elements from the page root; fall back to defaults."""
    styles: dict[int, str] = {}
    for ns in _ALL_NS:
        for qsd in root.findall(f"{{{ns}}}QuickStyleDef"):
            idx = qsd.get("index", "")
            name = qsd.get("name", "p")
            if idx.isdigit():
                styles[int(idx)] = name
    return styles or dict(_DEFAULT_STYLES)


# ---------------------------------------------------------------------------
# Outline element → Markdown lines
# ---------------------------------------------------------------------------

def _oe_text(oe, ns_uri: str) -> str:
    """Concatenate the Markdown text of all one:T elements inside an OE."""
    parts = []
    for t in oe.iter(f"{{{ns_uri}}}T"):
        parts.append(_t_to_md(t))
    return "".join(parts)


def _detect_ns(root) -> str:
    """Return the namespace URI used by the root element."""
    tag = root.tag
    if tag.startswith("{"):
        return tag[1:tag.index("}")]
    return _NS_2013


def _convert_table(table_elem, ns_uri: str) -> list[str]:
    """Convert a one:Table element to a Markdown table."""
    rows_md: list[list[str]] = []

    for row in table_elem.findall(f"{{{ns_uri}}}Row"):
        cell_texts = []
        for cell in row.findall(f"{{{ns_uri}}}Cell"):
            # Flatten all text inside the cell
            parts = []
            for oe in cell.iter(f"{{{ns_uri}}}OE"):
                t = _oe_text(oe, ns_uri).strip()
                if t:
                    parts.append(t)
            cell_texts.append(" ".join(parts).replace("|", "\\|"))
        rows_md.append(cell_texts)

    if not rows_md:
        return []

    col_count = max(len(r) for r in rows_md)
    for r in rows_md:
        while len(r) < col_count:
            r.append("")

    lines = [
        "| " + " | ".join(rows_md[0]) + " |",
        "| " + " | ".join("---" for _ in range(col_count)) + " |",
    ]
    for row in rows_md[1:]:
        lines.append("| " + " | ".join(row) + " |")
    return lines


def _convert_oe(oe, ns_uri: str, quick_styles: dict, depth: int = 0) -> list[str]:
    """
    Recursively convert a one:OE element (and its OEChildren) to Markdown lines.
    depth controls list indentation.
    """
    lines: list[str] = []

    # Embedded table takes precedence
    table = oe.find(f"{{{ns_uri}}}Table")
    if table is not None:
        lines.extend(_convert_table(table, ns_uri))
        lines.append("")
        return lines

    style_name = quick_styles.get(int(oe.get("quickStyleIndex", 0)), "p")
    text = _oe_text(oe, ns_uri).strip()

    # Detect list markers
    list_elem   = oe.find(f"{{{ns_uri}}}List")
    bullet_elem = list_elem.find(f"{{{ns_uri}}}Bullet") if list_elem is not None else None
    number_elem = list_elem.find(f"{{{ns_uri}}}Number") if list_elem is not None else None

    indent = "  " * depth

    if style_name.startswith("h") and len(style_name) == 2 and style_name[1].isdigit():
        if text:
            lines.append("#" * int(style_name[1]) + " " + text)
    elif style_name in ("blockquote", "cite"):
        if text:
            lines.append("> " + text)
    elif style_name == "code":
        if text:
            lines.append(f"`{text}`")
    elif bullet_elem is not None:
        if text:
            lines.append(f"{indent}- {text}")
    elif number_elem is not None:
        start = number_elem.get("startNumber", "1")
        if text:
            lines.append(f"{indent}{start}. {text}")
    else:
        if text:
            lines.append(f"{indent}{text}")
        elif depth == 0:
            lines.append("")

    # Recurse into nested OEChildren
    children = oe.find(f"{{{ns_uri}}}OEChildren")
    if children is not None:
        for child_oe in children.findall(f"{{{ns_uri}}}OE"):
            lines.extend(_convert_oe(child_oe, ns_uri, quick_styles, depth + 1))

    return lines


# ---------------------------------------------------------------------------
# Page XML → Markdown
# ---------------------------------------------------------------------------

def page_xml_to_markdown(page_xml: str) -> tuple[str, str]:
    """
    Convert OneNote page XML (from GetPageContent) to (title, markdown) strings.
    """
    try:
        root = ET.fromstring(page_xml)
    except ET.ParseError as exc:
        return ("Error", f"<!-- XML parse error: {exc} -->\n")

    ns_uri = _detect_ns(root)
    quick_styles = _parse_quick_styles(root)

    # Page title: prefer the one:Title element over the page-level name attribute
    title = root.get("name", "Untitled")
    title_elem = root.find(f"{{{ns_uri}}}Title")
    if title_elem is not None:
        oe = title_elem.find(f"{{{ns_uri}}}OE")
        if oe is not None:
            t = _oe_text(oe, ns_uri).strip()
            if t:
                title = t

    lines: list[str] = [f"# {title}", ""]

    for outline in root.findall(f"{{{ns_uri}}}Outline"):
        oe_children = outline.find(f"{{{ns_uri}}}OEChildren")
        if oe_children is None:
            continue
        for oe in oe_children.findall(f"{{{ns_uri}}}OE"):
            lines.extend(_convert_oe(oe, ns_uri, quick_styles, depth=0))
        lines.append("")

    # Collapse runs of more than one blank line
    out: list[str] = []
    blank = 0
    for ln in lines:
        if ln == "":
            blank += 1
            if blank <= 1:
                out.append(ln)
        else:
            blank = 0
            out.append(ln)

    return title, "\n".join(out).strip() + "\n"


# ---------------------------------------------------------------------------
# COM connection
# ---------------------------------------------------------------------------

def connect_to_onenote():
    """
    Return a win32com handle to the OneNote Application object.
    Starts OneNote if it is not already running.
    """
    try:
        import win32com.client  # type: ignore[import-untyped]
    except ImportError:
        sys.exit(
            "pywin32 is not installed.\n"
            "Install it with:  pip install pywin32\n\n"
            "This script requires Windows with Microsoft OneNote for Desktop."
        )
    try:
        # Try early-binding first (more reliable with out-params)
        app = win32com.client.gencache.EnsureDispatch("OneNote.Application.6")
    except Exception:
        try:
            app = win32com.client.Dispatch("OneNote.Application.6")
        except Exception as exc:
            sys.exit(
                f"Cannot connect to OneNote: {exc}\n\n"
                "Make sure Microsoft OneNote for Desktop (Office 2016 / 365) "
                "is installed.  The 'OneNote for Windows 10' UWP app does not "
                "support COM automation."
            )
    return app


def _hierarchy(app, scope: int) -> ET.Element:
    xml_str = app.GetHierarchy("", scope, "")
    return ET.fromstring(xml_str)


def _page_content(app, page_id: str) -> str:
    return app.GetPageContent(page_id, _PAGE_INFO_BASIC, "")


# ---------------------------------------------------------------------------
# Hierarchy traversal helpers
# ---------------------------------------------------------------------------

def _iter_notebooks(root):
    """Yield (name, elem) for each notebook in a hierarchy root."""
    for ns in _ALL_NS:
        items = root.findall(f"{{{ns}}}Notebook")
        if items:
            for nb in items:
                yield nb.get("name", ""), nb
            return


def _iter_sections(nb_elem):
    """Yield section elements, including those inside SectionGroups."""
    for ns in _ALL_NS:
        for sec in nb_elem.findall(f"{{{ns}}}Section"):
            yield sec
        for sg in nb_elem.findall(f"{{{ns}}}SectionGroup"):
            if sg.get("isRecycleBin") == "true":
                continue
            for sec in sg.findall(f"{{{ns}}}Section"):
                yield sec


def _iter_pages(sec_elem):
    for ns in _ALL_NS:
        pages = sec_elem.findall(f"{{{ns}}}Page")
        if pages:
            for p in pages:
                yield p
            return


def _slugify(name: str) -> str:
    """Filesystem-safe slug from a notebook/section/page name."""
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", name)
    name = re.sub(r"\s+", "_", name.strip())
    return name or "untitled"


# ---------------------------------------------------------------------------
# Export helpers
# ---------------------------------------------------------------------------

def export_page(app, page_elem, out_dir: Path, verbose: bool = True) -> Path:
    page_id   = page_elem.get("ID", "")
    page_name = page_elem.get("name", "Untitled")
    slug      = _slugify(page_name)

    try:
        page_xml = _page_content(app, page_id)
    except Exception as exc:
        print(f"    WARN: could not fetch page '{page_name}': {exc}")
        return out_dir / f"{slug}.md"

    _title, md = page_xml_to_markdown(page_xml)

    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{slug}.md"
    out_file.write_text(md, encoding="utf-8")

    if verbose:
        print(f"    {page_name}  →  {out_file.relative_to(out_file.parents[2])}")

    return out_file


def export_section(app, sec_elem, out_dir: Path, verbose: bool = True) -> list[Path]:
    sec_name = sec_elem.get("name", "Untitled")
    sec_dir  = out_dir / _slugify(sec_name)
    files    = []
    for page_elem in _iter_pages(sec_elem):
        files.append(export_page(app, page_elem, sec_dir, verbose=verbose))
    return files


def export_notebook(
    app,
    nb_elem,
    out_dir: Path,
    section_filter: Optional[str] = None,
    verbose: bool = True,
) -> list[Path]:
    nb_name = nb_elem.get("name", "Untitled")
    nb_dir  = out_dir / _slugify(nb_name)
    files   = []

    if verbose:
        print(f"\nNotebook: {nb_name}")

    for sec_elem in _iter_sections(nb_elem):
        sec_name = sec_elem.get("name", "")
        if section_filter and section_filter.lower() != sec_name.lower():
            continue
        if verbose:
            print(f"  Section: {sec_name}")
        files.extend(export_section(app, sec_elem, nb_dir, verbose=verbose))

    return files


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def cmd_list(app) -> None:
    root = _hierarchy(app, _HS_SECTIONS)
    print("Available notebooks:\n")
    for nb_name, nb_elem in _iter_notebooks(root):
        print(f"  {nb_name}")
        for sec in _iter_sections(nb_elem):
            print(f"    ↳ {sec.get('name', '')}")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="onenote_extractor",
        description=(
            "Export Microsoft OneNote notebooks to Markdown files.\n"
            "Requires Windows with Microsoft OneNote for Desktop installed."
        ),
    )
    parser.add_argument(
        "--list", action="store_true",
        help="List available notebooks and sections, then exit.",
    )
    parser.add_argument(
        "--all", action="store_true",
        help="Export every open notebook.",
    )
    parser.add_argument(
        "--notebook", metavar="NAME",
        help="Name of the notebook to export (case-insensitive).",
    )
    parser.add_argument(
        "--section", metavar="NAME",
        help="Export only this section (requires --notebook).",
    )
    parser.add_argument(
        "-o", "--output", default="./onenote_export",
        help="Root output directory (default: ./onenote_export).",
    )
    parser.add_argument(
        "-q", "--quiet", action="store_true",
        help="Suppress per-page progress output.",
    )

    args = parser.parse_args()
    verbose = not args.quiet

    app     = connect_to_onenote()
    out_dir = Path(args.output)

    if args.list or (not args.notebook and not args.all):
        cmd_list(app)
        return

    root  = _hierarchy(app, _HS_PAGES)
    files = []

    if args.all:
        for _name, nb_elem in _iter_notebooks(root):
            files.extend(export_notebook(app, nb_elem, out_dir, verbose=verbose))

    elif args.notebook:
        target = args.notebook.lower()
        matched = False
        for nb_name, nb_elem in _iter_notebooks(root):
            if nb_name.lower() == target:
                files.extend(
                    export_notebook(
                        app, nb_elem, out_dir,
                        section_filter=args.section,
                        verbose=verbose,
                    )
                )
                matched = True
                break
        if not matched:
            sys.exit(
                f"Notebook not found: {args.notebook!r}\n"
                "Run without arguments to list available notebooks."
            )

    resolved = out_dir.resolve()
    print(f"\nExported {len(files)} page(s) to {resolved}")


if __name__ == "__main__":
    main()
