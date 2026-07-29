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

If a run fails partway through, pages completed so far are saved next to the
output file (<output>.progress.json). Re-running with the same -o path picks
up automatically where it left off; a fully completed run removes this file.

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
import json
import os
import re
import sys
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
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
2.  Format headings with Markdown — but ONLY for a heading that genuinely starts
    a new chapter or section AT THIS POINT in the page:
      # Title      → document title or chapter title
      ## Section   → major section headings
      ### Sub      → subsection headings
      #### SubSub  → sub-subsection headings
    Do NOT mark a running header as a heading — see rule 6.
3.  Mark inline footnote calls in the body text as [^N] (e.g. word[^1], phrase[^2]).
4.  Collect footnote definitions at the very end of your response, wrapped exactly as:

FOOTNOTES_BEGIN
[^1]: Full text of footnote 1.
[^2]: Full text of footnote 2.
FOOTNOTES_END

5.  If the page has no footnotes, omit the FOOTNOTES_BEGIN/FOOTNOTES_END block entirely.
6.  A running header/footer is text that repeats near the top or bottom of every page of
    a chapter (e.g. the chapter title, and/or the page number). It is page furniture, not
    content — it must NEVER be formatted as a Markdown heading and must NEVER be left as
    plain body text. Omit it, or wrap it in a single HTML comment: <!-- p. 42 --> or
    <!-- 42 CHAPTER TITLE -->. The same applies to marginal line-numbers printed next to
    the text in critical editions — omit them; never inline them into the sentence.
7.  Output ONLY the extracted text — no commentary, introductions, or summaries.
8.  Separate paragraphs with a blank line. If the page begins mid-paragraph (continuing a
    sentence from the previous page) or ends mid-paragraph (continuing onto the next page),
    do NOT insert a paragraph break — start/end the text exactly as it appears, so the
    surrounding pages can be rejoined into one continuous paragraph.
9.  For tables, use Markdown table syntax where feasible.
10. For mathematical expressions, use LaTeX: inline $...$ or display $$...$$.
11. Title pages, half-title pages, series pages, and copyright/colophon pages (mostly
    large centered or stacked lines — title, author, publisher — rather than flowing
    prose) are front matter, not chapter content. Do not turn every prominent line into
    its own Markdown heading. Use at most one "# " heading for the actual book title if
    this is its title page, and render every other line (subtitle, author, edition,
    imprint) as plain text.
12. German (and other) typeset text sometimes emphasizes a word or phrase by letter-
    spacing it (Sperrdruck), e.g. "g e s p e r r t" instead of italics. Recognize this and
    render it as normal italic Markdown instead: *gesperrt*. Do not transcribe the extra
    spacing literally.
13. Preserve every genuine italic span exactly as *italic* Markdown — single emphasized
    words, names, foreign-language phrases, and titles of works — do not drop italic
    formatting on any of them.
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
_COMMENT_RE = re.compile(r"^<!--.*-->$")
_ARABIC_PAGE_NUM_RE = re.compile(r"^\d+\.?$")
_ROMAN_PAGE_NUM_RE = re.compile(r"^[IVXLCDM]+\.?$")
_SENTENCE_END_CHARS = ".!?”“’’\"'»:;*"
_HYPHEN_BREAK_RE = re.compile(r"(\w)-$")
_DOT_LEADER_RE = re.compile(r"(?:\.\s*){3,}\d+$")  # a table-of-contents entry: "... 76"


def _heading_level(line: str) -> int:
    m = _HEADING_RE.match(line.strip())
    return len(m.group(1)) if m else 0


def _normalize_heading(text: str) -> str:
    """Strip Markdown '#'s and punctuation, casefold, for duplicate-heading comparison."""
    text = re.sub(r"^#{1,4}\s*", "", text.strip())
    text = re.sub(r"\s+", " ", text).strip()
    return text.strip(" .:").casefold()


def _is_page_number_line(line: str) -> bool:
    s = line.strip()
    return bool(s) and bool(_ARABIC_PAGE_NUM_RE.match(s) or _ROMAN_PAGE_NUM_RE.match(s))


def _is_comment_line(line: str) -> bool:
    return bool(_COMMENT_RE.match(line.strip()))


def _ends_sentence(line: str) -> bool:
    """True if this line looks like the end of a paragraph (not a mid-sentence page break)."""
    s = line.rstrip()
    if not s or re.fullmatch(r"[-*]{3,}", s) or _DOT_LEADER_RE.search(s):
        return True
    return s[-1] in _SENTENCE_END_CHARS


def _join_continuation(prev_tail: str, next_line: str) -> str:
    """Join a paragraph's tail (from one page) with its continuation (from the next)."""
    next_line = next_line.lstrip()
    m = _HYPHEN_BREAK_RE.search(prev_tail)
    if m and next_line[:1].islower():
        return prev_tail[:-1] + next_line  # drop the line-break hyphen, no space
    if not prev_tail or prev_tail.endswith(" "):
        return prev_tail + next_line
    return prev_tail + " " + next_line


def _split_blocks(body: str) -> list[list[str]]:
    """Split a page's body into blank-line-delimited blocks of lines."""
    raw = re.split(r"\n\s*\n", body.strip("\n"))
    return [b.splitlines() for b in raw if b.strip()]


def _render_title_page(blocks: list[list[str]], opening_rule: bool = True) -> list[str]:
    """Render a title/cover page's stacked headings as a single set-off block."""
    lines: list[str] = ["---", ""] if opening_rule else []
    for block in blocks:
        first = block[0].strip()
        if _heading_level(first):
            text = re.sub(r"^#{1,4}\s*", "", first).strip()
            if text:
                lines.append(f"**{text}**")
                lines.append("")
            lines.extend(block[1:])
        else:
            lines.extend(block)
        lines.append("")
    while lines and lines[-1] == "":
        lines.pop()
    lines.append("")
    lines.append("---")
    return lines


def _has_adjacent_headings(blocks: list[list[str]]) -> bool:
    """True if two *bare* heading lines (nothing else in their block) appear back-to-back
    with no body text between them — the structural signature of stacked title-page
    typography (Title / Subtitle / Author), not a real chapter break or a table-of-contents
    entry (where a heading-formatted line is immediately followed by its own body text)."""
    was_bare_heading = False
    for block in blocks:
        is_bare_heading = len(block) == 1 and bool(_heading_level(block[0]))
        if is_bare_heading and was_bare_heading:
            return True
        was_bare_heading = is_bare_heading
    return False


def build_sections(pages: list[PageResult]) -> list[Section]:
    """
    Convert the flat page sequence into Section objects.

    Footnotes from each page are attached to the section active at that page's end.
    Running headers/page-numbers that leaked into the body as stray text are dropped,
    paragraphs that continue across a page boundary are rejoined, repeated running
    headers formatted as Markdown headings are collapsed into the enclosing section,
    and pages with stacked title-page typography are set off as their own block.
    """
    sections: list[Section] = []
    current = Section()  # preamble – content before first heading
    current_heading_norm = ""
    pending_comments: list[str] = []

    def _flush_comments() -> None:
        nonlocal pending_comments
        if pending_comments:
            if current.body_lines:
                current.body_lines.append("")
            current.body_lines.extend(pending_comments)
            pending_comments = []

    for page in pages:
        blocks = _split_blocks(page.body)

        if _has_adjacent_headings(blocks):
            _flush_comments()
            last_line = next((l.strip() for l in reversed(current.body_lines) if l.strip()), "")
            rendered = _render_title_page(blocks, opening_rule=last_line != "---")
            if current.body_lines:
                current.body_lines.append("")
            current.body_lines.extend(rendered)
            current.footnotes.extend(page.footnotes)
            continue

        first_content_seen = False  # only the page's *first* content block may
                                     # be merged with the previous page's tail —
                                     # blocks later on the same page are already
                                     # correctly paragraph-separated by the model

        for block in blocks:
            first_line = block[0]

            if len(block) == 1 and _is_comment_line(first_line):
                pending_comments.append(first_line.strip())
                continue

            lvl = _heading_level(first_line)
            if lvl:
                heading_text = first_line.strip()
                if current_heading_norm and _normalize_heading(heading_text) == current_heading_norm:
                    # a running header repeating the current section's own title
                    _flush_comments()
                    if block[1:]:
                        if current.body_lines:
                            current.body_lines.append("")
                        current.body_lines.extend(block[1:])
                    first_content_seen = True
                    continue
                _flush_comments()
                sections.append(current)
                current = Section(heading=heading_text, level=lvl)
                current_heading_norm = _normalize_heading(heading_text)
                current.body_lines.extend(block[1:])
                first_content_seen = True
                continue

            if len(block) == 1:
                line = block[0].strip()
                if _is_page_number_line(line) or (
                    current_heading_norm and _normalize_heading(line) == current_heading_norm
                ):
                    continue  # stray running-header/page-number text, not real content

            if (
                not first_content_seen
                and current.body_lines
                and not _ends_sentence(current.body_lines[-1])
            ):
                prev_tail = current.body_lines.pop()
                merged = _join_continuation(prev_tail, block[0])
                _flush_comments()
                current.body_lines.append(merged)
                current.body_lines.extend(block[1:])
            else:
                _flush_comments()
                if current.body_lines:
                    current.body_lines.append("")
                current.body_lines.extend(block)
            first_content_seen = True

        current.footnotes.extend(page.footnotes)

    _flush_comments()
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


# ─── Sperrdruck (letter-spaced emphasis) cleanup ──────────────────────────────
# Typeset German text often emphasizes a word/phrase by spacing out its letters
# (Sperrdruck) instead of italicizing it. A vision model transcribes that spacing
# literally (e.g. "t r a n s z e n d e n t a l"), so it needs to be collapsed back
# into a word and marked as italic Markdown.

_SPERRDRUCK_RE = re.compile(r"(?<!\w)(?:\w \w \w(?: \w)+)(?!\w)", re.UNICODE)


def _collapse_sperrdruck_run(run: str) -> str:
    """Rejoin a run of single letters into words, splitting before each capital
    letter. Lowercase connector words (e.g. 'und') stay attached to the
    preceding word — a safe compromise, since there's no reliable way to spot
    a lowercase word boundary in already letter-spaced text."""
    tokens = run.split(" ")
    words = [tokens[0]]
    for tok in tokens[1:]:
        if tok.isupper():
            words.append(tok)
        else:
            words[-1] += tok
    return " ".join(words)


def desperrdruck(text: str) -> str:
    """Collapse letter-spaced (Sperrdruck) emphasis runs into italic Markdown."""
    return _SPERRDRUCK_RE.sub(lambda m: f"*{_collapse_sperrdruck_run(m.group(0))}*", text)


# ─── Output assembly helper ───────────────────────────────────────────────────

def _assemble_and_write(page_results: list[PageResult], out_path: Path) -> str:
    sections = build_sections(page_results)
    sections = renumber_footnotes(sections)
    markdown = desperrdruck(sections_to_markdown(sections))
    out_path.write_text(markdown, encoding="utf-8")
    return markdown


# ─── Resume-progress sidecar ───────────────────────────────────────────────────
# The final Markdown loses the per-page structure (footnotes get renumbered,
# headings get regrouped into sections), so it can't itself be resumed from.
# A small JSON sidecar next to the output preserves the raw per-page results
# so a failed run's completed pages aren't re-fetched (and re-billed) on retry.

def _progress_path(out_path: Path) -> Path:
    return out_path.with_suffix(out_path.suffix + ".progress.json")


def load_progress(out_path: Path, total_pages: int) -> list[PageResult]:
    path = _progress_path(out_path)
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    if data.get("pdf_pages_total") != total_pages:
        return []  # stale sidecar from a different document; ignore it
    return [
        PageResult(page_num=item["page_num"], body=item["body"], footnotes=item["footnotes"])
        for item in data.get("page_results", [])
    ]


def save_progress(out_path: Path, total_pages: int, page_results: list[PageResult]) -> None:
    data = {
        "pdf_pages_total": total_pages,
        "page_results": [
            {"page_num": r.page_num, "body": r.body, "footnotes": r.footnotes}
            for r in page_results
        ],
    }
    _progress_path(out_path).write_text(json.dumps(data), encoding="utf-8")


def clear_progress(out_path: Path) -> None:
    path = _progress_path(out_path)
    if path.exists():
        path.unlink()


# ─── Page-range helper ────────────────────────────────────────────────────────

def pages_to_spec(indices: list[int]) -> str:
    """Convert a sorted list of 0-indexed page indices to a 1-indexed --pages spec."""
    if not indices:
        return ""
    parts: list[str] = []
    start = prev = indices[0]
    for idx in indices[1:]:
        if idx == prev + 1:
            prev = idx
            continue
        parts.append(f"{start + 1}-{prev + 1}" if start != prev else f"{start + 1}")
        start = prev = idx
    parts.append(f"{start + 1}-{prev + 1}" if start != prev else f"{start + 1}")
    return ",".join(parts)


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


# ─── Rate-limit retry ──────────────────────────────────────────────────────────

MAX_RATE_LIMIT_RETRIES = 6
FALLBACK_RETRY_DELAY   = 20.0  # seconds, used when the error has no explicit delay

_RETRY_DELAY_RE = re.compile(r"retryDelay['\"]?\s*[:=]\s*['\"]?(\d+(?:\.\d+)?)s")


def _is_retryable_error(exc: Exception) -> bool:
    """True for rate limits and transient server-side errors worth waiting out."""
    msg = str(exc).lower()
    tokens = (
        "429", "resource_exhausted", "rate limit", "too many requests",
        "502", "503", "504", "unavailable", "overloaded", "high demand",
        "server error", "internal error", "try again later",
    )
    return any(tok in msg for tok in tokens)


def _is_daily_quota_error(exc: Exception) -> bool:
    """True for a per-day quota exhaustion, which waiting out a minute can't fix."""
    return re.search(r"per.?day", str(exc), re.IGNORECASE) is not None


def _parse_retry_delay(exc: Exception) -> Optional[float]:
    m = _RETRY_DELAY_RE.search(str(exc))
    return float(m.group(1)) if m else None


# ─── Cross-run daily-quota memory ──────────────────────────────────────────────
# A daily quota, once exhausted, stays exhausted until it resets (UTC midnight for
# Gemini). When a workflow converts many PDFs in one run — one subprocess per file
# — a model that hit its quota on file 1 will immediately hit it again on file 2,
# 3, ... Remembering it in a small state file (scoped to this machine/CI job, not
# the repo) lets later files in the same run skip straight to a working model
# instead of re-discovering the same exhaustion — and paying for the API call and
# retry cycle — every time.

def _quota_state_path() -> Path:
    base = os.environ.get("RUNNER_TEMP") or tempfile.gettempdir()
    return Path(base) / "pdf_extractor_daily_quota.json"


def _today_utc() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _load_quota_exhausted_models() -> set[str]:
    path = _quota_state_path()
    if not path.exists():
        return set()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return set()
    today = _today_utc()
    return {model for model, date in data.items() if date == today}


def _mark_quota_exhausted(model: str) -> None:
    path = _quota_state_path()
    data = {}
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            data = {}
    data[model] = _today_utc()
    try:
        path.write_text(json.dumps(data), encoding="utf-8")
    except OSError:
        pass  # best-effort — losing this memory just means re-discovering it


class QuotaExhaustedError(Exception):
    """Every configured model has hit its daily quota — not fixable by retrying
    today. Quotas reset daily (UTC), so this is expected to clear on its own."""


class ModelCascade:
    """Holds the active extract_fn and can fall back to the next model on a
    daily-quota exhaustion — a fresh model has its own separate quota bucket."""

    def __init__(self, provider: str, models: list[str], api_key: Optional[str], host: str):
        if not models:
            raise ValueError("ModelCascade requires at least one model")
        self.provider = provider
        self.models   = models
        self.api_key  = api_key
        self.host     = host

        exhausted = _load_quota_exhausted_models()
        self.all_exhausted = all(m in exhausted for m in models)
        self.index = next(
            (i for i, m in enumerate(models) if m not in exhausted),
            len(models) - 1,
        )
        if self.index > 0:
            print(f"Skipping {', '.join(models[:self.index])} — already hit today's "
                  f"quota earlier in this run; starting with {models[self.index]}.")
        self.extract_fn = build_extract_fn(provider, models[self.index], api_key, host)

    @property
    def model(self) -> str:
        return self.models[self.index]

    def advance(self) -> bool:
        """Switch to the next fallback model. Returns False if none remain."""
        if self.index + 1 >= len(self.models):
            return False
        self.index += 1
        print(f"\n    daily quota exhausted for {self.models[self.index - 1]} — "
              f"falling back to {self.models[self.index]} …", end=" ", flush=True)
        self.extract_fn = build_extract_fn(self.provider, self.models[self.index], self.api_key, self.host)
        return True


def extract_with_retry(cascade: ModelCascade, image_b64: str) -> str:
    """Call the cascade's active model, pausing and retrying on a per-minute rate
    limit, or falling back to the next model on a per-day quota exhaustion."""
    while True:
        for attempt in range(MAX_RATE_LIMIT_RETRIES):
            try:
                return cascade.extract_fn(image_b64)
            except Exception as exc:
                if _is_daily_quota_error(exc):
                    _mark_quota_exhausted(cascade.model)
                    if cascade.advance():
                        break  # retry immediately on the new model
                    raise QuotaExhaustedError(str(exc)) from exc
                if not _is_retryable_error(exc) or attempt == MAX_RATE_LIMIT_RETRIES - 1:
                    raise
                delay = _parse_retry_delay(exc) or FALLBACK_RETRY_DELAY * (attempt + 1)
                print(f"\n    temporary error — waiting {delay:.0f}s "
                      f"(retry {attempt + 1}/{MAX_RATE_LIMIT_RETRIES - 1}) …", end=" ", flush=True)
                time.sleep(delay)


# ─── Main entry point ─────────────────────────────────────────────────────────

def process_pdf(
    pdf_path:        str,
    output_path:     Optional[str],
    provider:        str,
    model:           Optional[str],
    fallback_models: Optional[list[str]],
    api_key:         Optional[str],
    host:            str,
    dpi:             int,
    pages_spec:      Optional[str],
) -> str:

    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        raise FileNotFoundError(f"File not found: {pdf_file}")

    out_path     = Path(output_path) if output_path else pdf_file.with_suffix(".md")
    active_model = model or DEFAULT_MODELS[provider]
    models       = [active_model, *(fallback_models or [])]
    cascade      = ModelCascade(provider, models, api_key, host)

    doc   = fitz.open(str(pdf_file))
    total = len(doc)

    page_indices = (
        parse_page_range(pages_spec, total) if pages_spec
        else list(range(total))
    )

    page_results: list[PageResult] = load_progress(out_path, total)
    if page_results:
        done = {r.page_num - 1 for r in page_results}
        page_indices = [i for i in page_indices if i not in done]

    print(f"Provider : {provider}  ({active_model})")
    if len(models) > 1:
        print(f"Fallback : {', '.join(models[1:])}  (used if the daily quota is exhausted)")
    print(f"Input    : {pdf_file}  ({total} pages total)")
    print(f"Output   : {out_path}")
    if page_results:
        print(f"Resuming : {len(page_results)} page(s) already done from a previous run")
    print(f"Pages    : {len(page_indices)} page(s) to process  |  DPI {dpi}\n")

    if page_indices and cascade.all_exhausted:
        doc.close()
        print(f"All configured models ({', '.join(models)}) already hit their daily "
              f"quota earlier in this run — skipping this file for now.")
        print("Quotas reset daily (UTC) — re-run with the same -o path to resume automatically.")
        return str(out_path)

    pad = len(str(len(page_indices)))

    for i, idx in enumerate(page_indices):
        print(f"  [{i + 1:>{pad}}/{len(page_indices)}] page {idx + 1} …", end=" ", flush=True)
        try:
            img_b64 = render_page_to_base64(doc[idx], dpi)
            raw     = extract_with_retry(cascade, img_b64)
        except QuotaExhaustedError:
            doc.close()
            print(f"\nAll configured models ({', '.join(models)}) have hit their daily "
                  f"quota ({i} of {len(page_indices)} page(s) completed this run).")
            if page_results:
                _assemble_and_write(page_results, out_path)
                save_progress(out_path, total, page_results)
                print(f"Partial output saved → {out_path}")
            print("Quotas reset daily (UTC) — re-run with the same -o path to resume automatically.")
            return str(out_path)
        except Exception:
            doc.close()
            print(f"\nFAILED on page {idx + 1} "
                  f"({i} of {len(page_indices)} page(s) completed).")
            if page_results:
                _assemble_and_write(page_results, out_path)
                save_progress(out_path, total, page_results)
                print(f"Partial output saved → {out_path}")
                print(f"Progress saved — re-run with the same -o path to resume automatically "
                      f"(or manually with --pages {pages_to_spec(page_indices[i:])}).")
            raise
        result = parse_page_result(raw, idx + 1)
        page_results.append(result)
        fn_n = len(result.footnotes)
        print(f"ok  ({fn_n} footnote{'s' if fn_n != 1 else ''})")

    doc.close()

    print("\nAssembling sections …")
    markdown = _assemble_and_write(page_results, out_path)
    clear_progress(out_path)
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
    gemini-3.5-flash-lite same lightweight tier — good first fallback, its own quota
    gemini-3.5-flash      heavier frontier model — much smaller free-tier daily quota;
                          best used as a last-resort fallback, not a first one

  openai  (OPENAI_API_KEY required)
    gpt-4o                highest quality

  anthropic  (ANTHROPIC_API_KEY required)
    claude-opus-4-5-20251101

examples:
  python pdf_extractor.py paper.pdf
  python pdf_extractor.py paper.pdf --model olmocr2
  python pdf_extractor.py paper.pdf --model qwen2.5vl:7b --dpi 300
  python pdf_extractor.py paper.pdf --provider gemini
  python pdf_extractor.py paper.pdf --provider gemini --fallback-models gemini-3.5-flash-lite,gemini-3.5-flash
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
    parser.add_argument("--fallback-models",
        help=(
            "Comma-separated model names to fall back to, in order, when the "
            "current model's daily quota is exhausted (each model has its own "
            "separate quota). Same provider only. Prefer same-tier fallbacks first "
            "(a heavier model may have a much smaller free-tier daily quota than the "
            "one it's backing up). Example: "
            "gemini-3.1-flash-lite --fallback-models gemini-3.5-flash-lite,gemini-3.5-flash"
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
    fallback_models = (
        [m.strip() for m in args.fallback_models.split(",") if m.strip()]
        if args.fallback_models else None
    )

    process_pdf(
        pdf_path        = args.pdf,
        output_path     = args.output,
        provider        = args.provider,
        model           = args.model,
        fallback_models = fallback_models,
        api_key         = args.api_key,
        host            = args.ollama_host,
        dpi             = args.dpi,
        pages_spec      = args.pages,
    )


if __name__ == "__main__":
    main()
