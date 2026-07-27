#!/usr/bin/env python3
"""
pdf_extractor.py — Extract text from PDF page images via vision LLM → Markdown.

Bypasses poor OCR by rendering each page to a high-resolution image and sending
it to a vision model.  Four provider options:

  --provider gemini    Gemini (requires GEMINI_API_KEY; free tier available)
  --provider openai    GPT-4o (requires OPENAI_API_KEY)
  --provider anthropic Claude  (requires ANTHROPIC_API_KEY)
  --provider ollama    Fully local, no API key needed  ← default

Usage:
    python pdf_extractor.py paper.pdf
    python pdf_extractor.py paper.pdf --provider ollama --model llama3.2-vision:11b
    python pdf_extractor.py paper.pdf --provider gemini --model gemini-3.1-flash-lite
    python pdf_extractor.py paper.pdf --provider openai --model gpt-4o
    python pdf_extractor.py paper.pdf --provider anthropic --model claude-opus-4-5-20251101
    python pdf_extractor.py paper.pdf --pages 1-30 --dpi 300

Recommended local models (no API key, install Ollama first):
    olmocr2          - fine-tuned for document OCR, best quality for academic text
    llama3.2-vision  - strong general vision model
    qwen2.5vl        - excellent at structured document extraction
    minicpm-v        - compact, good on CPU-only machines

Requirements:
    pip install pymupdf ollama           # for local Ollama (default)
    pip install pymupdf google-genai     # for Gemini (free tier available)
    pip install pymupdf openai           # for GPT-4o
    pip install pymupdf anthropic        # for Claude
"""

import argparse
import base64
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional

# ─── Dependency checks ────────────────────────────────────────────────────────

try:
    import fitz  # PyMuPDF
except ImportError:
    sys.exit("Missing dependency — install with:  pip install pymupdf")

ollama_sdk: Any = None
try:
    import ollama as ollama_sdk  # type: ignore[import-untyped]
    HAS_OLLAMA = True
except ImportError:
    HAS_OLLAMA = False

OpenAI: Any = None
try:
    from openai import OpenAI  # type: ignore[import-untyped]
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

anthropic_sdk: Any = None
try:
    import anthropic as anthropic_sdk
    from anthropic.types import TextBlock as _AnthropicTextBlock
    HAS_ANTHROPIC = True
except ImportError:
    _AnthropicTextBlock = None  # type: ignore[assignment,misc]
    HAS_ANTHROPIC = False

gemini_sdk: Any = None
gemini_types: Any = None
try:
    from google import genai as gemini_sdk
    from google.genai import types as gemini_types
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False


# ─── Constants ────────────────────────────────────────────────────────────────

PROVIDER_OLLAMA    = "ollama"
PROVIDER_OPENAI    = "openai"
PROVIDER_ANTHROPIC = "anthropic"
PROVIDER_GEMINI    = "gemini"

DEFAULT_MODELS = {
    PROVIDER_OLLAMA:    "llama3.2-vision:11b",
    PROVIDER_OPENAI:    "gpt-4o",
    PROVIDER_ANTHROPIC: "claude-sonnet-4-6",
    PROVIDER_GEMINI:    "gemini-3.1-flash-lite",
}

DEFAULT_DPI      = 200
DEFAULT_PROVIDER = PROVIDER_OLLAMA

EXTRACTION_PROMPT = """\
You are extracting text from a scanned or typeset academic PDF page image.

Rules:
1.  Extract ALL text faithfully — headings, body paragraphs, captions, footnotes.
2.  Format headings with Markdown:
      # Title      → document title or chapter title
      ## Section   → major section headings
      ### Sub      → subsection headings
      #### SubSub  → sub-subsection headings
3.  Mark inline footnote calls in the body text as [^N] (e.g. word[^1], phrase[^2]).
4.  Collect footnote definitions at the very end of your response, wrapped exactly as:

FOOTNOTES_BEGIN
[^1]: Full text of footnote 1.
[^2]: Full text of footnote 2.
FOOTNOTES_END

5.  If the page has no footnotes, omit the FOOTNOTES_BEGIN/FOOTNOTES_END block entirely.
6.  Page numbers and running headers/footers that are purely navigational should be
    omitted or wrapped in an HTML comment: <!-- p. 42 -->
7.  Output ONLY the extracted text — no commentary, introductions, or summaries.
8.  Separate paragraphs with a blank line.
9.  For tables, use Markdown table syntax where feasible.
10. For mathematical expressions, use LaTeX: inline $...$ or display $$...$$.
"""


# ─── Data structures ──────────────────────────────────────────────────────────

@dataclass
class PageResult:
    page_num:  int
    body:      str          # Markdown body with [^N] inline references
    footnotes: list[str]    # ["[^1]: text ...", "[^2]: text ..."]


@dataclass
class Section:
    heading:    str = ""    # Markdown heading line, e.g. "## Introduction"
    level:      int = 0     # 1–4; 0 = preamble before first heading
    body_lines: list[str] = field(default_factory=list)
    footnotes:  list[str] = field(default_factory=list)


# ─── Page rendering ───────────────────────────────────────────────────────────

def render_page_to_base64(page: "fitz.Page", dpi: int) -> str:
    """Render a single PDF page to a base64-encoded PNG string."""
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
    return base64.b64encode(pix.tobytes("png")).decode("utf-8")


# ─── Vision API calls ─────────────────────────────────────────────────────────

def _call_ollama(model: str, image_b64: str) -> str:
    """Call a local Ollama vision model. No API key required."""
    response = ollama_sdk.chat(
        model=model,
        messages=[{
            "role":    "user",
            "content": EXTRACTION_PROMPT,
            "images":  [image_b64],   # Ollama accepts raw base64 strings
        }],
        options={"num_predict": 4096},
    )
    return response["message"]["content"].strip()


def _call_openai(client: "OpenAI", model: str, image_b64: str) -> str:
    response = client.chat.completions.create(
        model=model,
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": EXTRACTION_PROMPT},
                {"type": "image_url", "image_url": {
                    "url":    f"data:image/png;base64,{image_b64}",
                    "detail": "high",
                }},
            ],
        }],
        max_tokens=4096,
    )
    return response.choices[0].message.content.strip()


def _call_anthropic(client: "anthropic_sdk.Anthropic", model: str, image_b64: str) -> str:
    msg = client.messages.create(
        model=model,
        max_tokens=4096,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {
                    "type":       "base64",
                    "media_type": "image/png",
                    "data":       image_b64,
                }},
                {"type": "text", "text": EXTRACTION_PROMPT},
            ],
        }],
    )
    block = msg.content[0]
    return block.text.strip() if isinstance(block, _AnthropicTextBlock) else ""  # type: ignore[union-attr]


def _call_gemini(client: "gemini_sdk.Client", model: str, image_b64: str) -> str:
    image_bytes = base64.b64decode(image_b64)
    response = client.models.generate_content(
        model=model,
        contents=[
            gemini_types.Part.from_bytes(data=image_bytes, mime_type="image/png"),
            EXTRACTION_PROMPT,
        ],
    )
    return (response.text or "").strip()


# ─── Raw output parsing ───────────────────────────────────────────────────────

def parse_page_result(raw: str, page_num: int) -> PageResult:
    """Split the model's raw output into body text and footnote definitions."""
    footnotes: list[str] = []
    body = raw

    if "FOOTNOTES_BEGIN" in raw:
        pre, rest = raw.split("FOOTNOTES_BEGIN", 1)
        body = pre.strip()
        fn_block = rest.split("FOOTNOTES_END")[0].strip()
        footnotes = [ln.strip() for ln in fn_block.splitlines() if ln.strip()]

    return PageResult(page_num=page_num, body=body, footnotes=footnotes)


# ─── Document assembly ────────────────────────────────────────────────────────

_HEADING_RE = re.compile(r"^(#{1,4})\s+")


def _heading_level(line: str) -> int:
    m = _HEADING_RE.match(line.strip())
    return len(m.group(1)) if m else 0


def build_sections(pages: list[PageResult]) -> list[Section]:
    """
    Convert the flat page sequence into Section objects.
    Footnotes from each page are attached to the section active at that page's end.
    """
    sections: list[Section] = []
    current = Section()  # preamble – content before first heading

    for page in pages:
        for line in page.body.splitlines():
            lvl = _heading_level(line)
            if lvl:
                sections.append(current)
                current = Section(heading=line.strip(), level=lvl)
            else:
                current.body_lines.append(line)
        current.footnotes.extend(page.footnotes)

    sections.append(current)
    return sections


def renumber_footnotes(sections: list[Section]) -> list[Section]:
    """
    Assign globally unique, sequential footnote numbers.
    The model resets to [^1] on every page; this rewrites both definitions
    and inline references so every footnote has a distinct identifier.
    """
    counter = 1

    for section in sections:
        if not section.footnotes:
            continue

        mapping: dict[str, str] = {}

        new_footnotes = []
        for fn in section.footnotes:
            m = re.match(r"^\[\^(\d+)\]:", fn)
            if m:
                old = m.group(1)
                if old not in mapping:
                    mapping[old] = str(counter)
                    counter += 1
                fn = fn.replace(f"[^{old}]:", f"[^{mapping[old]}]:", 1)
            new_footnotes.append(fn)
        section.footnotes = new_footnotes

        new_body = []
        for line in section.body_lines:
            for old, new in mapping.items():
                line = re.sub(
                    rf"\[\^{re.escape(old)}\](?!:)",
                    f"[^{new}]",
                    line,
                )
            new_body.append(line)
        section.body_lines = new_body

    return sections


def sections_to_markdown(sections: list[Section]) -> str:
    parts: list[str] = []

    for section in sections:
        if section.heading:
            parts.append(section.heading)
            parts.append("")

        body = "\n".join(section.body_lines).strip()
        if body:
            parts.append(body)
            parts.append("")

        if section.footnotes:
            parts.append("---")
            parts.append("")
            for fn in section.footnotes:
                parts.append(fn)
            parts.append("")

    return "\n".join(parts).strip() + "\n"


# ─── Page-range helper ────────────────────────────────────────────────────────

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


# ─── Provider setup ───────────────────────────────────────────────────────────

def build_extract_fn(
    provider: str,
    model:    str,
    api_key:  Optional[str],
    host:     str,
) -> Callable[[str], str]:
    """Return a callable (image_b64) -> str for the chosen provider."""

    if provider == PROVIDER_OLLAMA:
        if not HAS_OLLAMA:
            sys.exit(
                "Ollama SDK not installed.\n"
                "Run:  pip install ollama\n"
                "Also ensure the Ollama app is running: https://ollama.com"
            )
        # Optionally point at a non-default Ollama host
        if host != "http://localhost:11434":
            import ollama as _ol  # type: ignore[import-untyped]
            _client = _ol.Client(host=host)
            return lambda img: _client.chat(
                model=model,
                messages=[{"role": "user", "content": EXTRACTION_PROMPT,
                            "images": [img]}],
                options={"num_predict": 4096},
            )["message"]["content"].strip()
        return lambda img, m=model: _call_ollama(m, img)

    if provider == PROVIDER_OPENAI:
        if not HAS_OPENAI:
            sys.exit("OpenAI SDK not installed.  Run:  pip install openai")
        key = api_key or os.environ.get("OPENAI_API_KEY", "")
        if not key:
            sys.exit("Set OPENAI_API_KEY env var or pass --api-key.")
        client = OpenAI(api_key=key)
        return lambda img, c=client, m=model: _call_openai(c, m, img)

    if provider == PROVIDER_ANTHROPIC:
        if not HAS_ANTHROPIC:
            sys.exit("Anthropic SDK not installed.  Run:  pip install anthropic")
        key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        if not key:
            sys.exit("Set ANTHROPIC_API_KEY env var or pass --api-key.")
        client = anthropic_sdk.Anthropic(api_key=key)
        return lambda img, c=client, m=model: _call_anthropic(c, m, img)

    if provider == PROVIDER_GEMINI:
        if not HAS_GEMINI:
            sys.exit("Gemini SDK not installed.  Run:  pip install google-genai")
        key = api_key or os.environ.get("GEMINI_API_KEY", "")
        if not key:
            sys.exit("Set GEMINI_API_KEY env var or pass --api-key.")
        client = gemini_sdk.Client(api_key=key)
        return lambda img, c=client, m=model: _call_gemini(c, m, img)

    sys.exit(f"Unknown provider: {provider!r}. Choose ollama, gemini, openai, or anthropic.")


# ─── Main entry point ─────────────────────────────────────────────────────────

def process_pdf(
    pdf_path:    str,
    output_path: Optional[str],
    provider:    str,
    model:       Optional[str],
    api_key:     Optional[str],
    host:        str,
    dpi:         int,
    pages_spec:  Optional[str],
) -> str:

    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        raise FileNotFoundError(f"File not found: {pdf_file}")

    out_path     = Path(output_path) if output_path else pdf_file.with_suffix(".md")
    active_model = model or DEFAULT_MODELS[provider]
    extract_fn   = build_extract_fn(provider, active_model, api_key, host)

    doc   = fitz.open(str(pdf_file))
    total = len(doc)

    page_indices = (
        parse_page_range(pages_spec, total) if pages_spec
        else list(range(total))
    )

    print(f"Provider : {provider}  ({active_model})")
    print(f"Input    : {pdf_file}  ({total} pages total)")
    print(f"Output   : {out_path}")
    print(f"Pages    : {len(page_indices)} page(s) to process  |  DPI {dpi}\n")

    page_results: list[PageResult] = []
    pad = len(str(len(page_indices)))

    for i, idx in enumerate(page_indices):
        print(f"  [{i + 1:>{pad}}/{len(page_indices)}] page {idx + 1} …", end=" ", flush=True)
        img_b64 = render_page_to_base64(doc[idx], dpi)
        raw     = extract_fn(img_b64)
        result  = parse_page_result(raw, idx + 1)
        page_results.append(result)
        fn_n = len(result.footnotes)
        print(f"ok  ({fn_n} footnote{'s' if fn_n != 1 else ''})")

    doc.close()

    print("\nAssembling sections …")
    sections = build_sections(page_results)
    sections = renumber_footnotes(sections)
    markdown = sections_to_markdown(sections)

    out_path.write_text(markdown, encoding="utf-8")
    print(f"Done → {out_path}  ({len(markdown):,} characters)")
    return str(out_path)


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="pdf_extractor",
        description=(
            "Extract PDF text via a vision LLM and write Markdown with footnotes.\n"
            "Defaults to a fully local Ollama model — no API key required."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
provider / model quick-reference:
  ollama (default, no API key needed)
    llama3.2-vision:11b   good all-rounder, 11B params (~8 GB VRAM)
    olmocr2               fine-tuned for document OCR — best for academic text
    qwen2.5vl:7b          strong at structured/scientific documents
    minicpm-v             compact; usable on CPU-only machines

  gemini  (GEMINI_API_KEY required; free tier available)
    gemini-3.1-flash-lite fast, current free-tier-eligible model

  openai  (OPENAI_API_KEY required)
    gpt-4o                highest quality

  anthropic  (ANTHROPIC_API_KEY required)
    claude-opus-4-5-20251101

examples:
  python pdf_extractor.py paper.pdf
  python pdf_extractor.py paper.pdf --model olmocr2
  python pdf_extractor.py paper.pdf --model qwen2.5vl:7b --dpi 300
  python pdf_extractor.py paper.pdf --provider gemini
  python pdf_extractor.py paper.pdf --provider openai
  python pdf_extractor.py paper.pdf --pages 1-50 -o chapter1.md
        """,
    )
    parser.add_argument("pdf",
        help="Input PDF file path.")
    parser.add_argument("-o", "--output",
        help="Output Markdown path (default: <pdf>.md).")
    parser.add_argument("--provider",
        default=DEFAULT_PROVIDER,
        choices=[PROVIDER_OLLAMA, PROVIDER_GEMINI, PROVIDER_OPENAI, PROVIDER_ANTHROPIC],
        help=f"Vision provider (default: {DEFAULT_PROVIDER}).")
    parser.add_argument("--model", default=None,
        help=(
            "Model name. Defaults per provider: "
            f"ollama={DEFAULT_MODELS[PROVIDER_OLLAMA]}, "
            f"gemini={DEFAULT_MODELS[PROVIDER_GEMINI]}, "
            f"openai={DEFAULT_MODELS[PROVIDER_OPENAI]}, "
            f"anthropic={DEFAULT_MODELS[PROVIDER_ANTHROPIC]}."
        ),
    )
    parser.add_argument("--api-key",
        help="API key for gemini/openai/anthropic (overrides env var).")
    parser.add_argument("--ollama-host",
        default="http://localhost:11434",
        help="Ollama server URL (default: http://localhost:11434).")
    parser.add_argument("--dpi", type=int, default=DEFAULT_DPI,
        help=f"Page rendering resolution (default: {DEFAULT_DPI}). "
             "Use 300 for small or dense text.")
    parser.add_argument("--pages",
        help=(
            "1-indexed page range to process. "
            "Formats: '1-30', '3,5,7', '1-5,8,10-15'."
        ),
    )

    args = parser.parse_args()

    process_pdf(
        pdf_path    = args.pdf,
        output_path = args.output,
        provider    = args.provider,
        model       = args.model,
        api_key     = args.api_key,
        host        = args.ollama_host,
        dpi         = args.dpi,
        pages_spec  = args.pages,
    )


if __name__ == "__main__":
    main()
