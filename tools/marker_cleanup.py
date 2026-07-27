"""
marker_cleanup.py
Rule-based pre-processing pass on marker-pdf markdown output.
Handles the deterministic fixes locally before sending to an LLM for the
context-sensitive pass (character encoding, line numbers, punctuation,
footnote placement).

Usage:
    python marker_cleanup.py file.md [file2.md ...]

Each input file is written to <stem>_cleaned.md alongside the original.
"""

import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Rule #3 — Broken hyphenation
# ---------------------------------------------------------------------------

def fix_broken_hyphenation(text: str) -> str:
    """
    Rejoin words split by typesetting line-wrap (hyphen + newline).
    Only rejoins when the continuation starts with a lowercase letter —
    that signature distinguishes line-wrap artifacts from legitimate
    German hyphenated compounds (which never have a bare newline after them).
    """
    return re.sub(r'(\w)-\n([a-zäöüàèéêëïîôùûüçœß])', r'\1\2', text)


# ---------------------------------------------------------------------------
# Rule #4 — Duplicate paragraphs
# ---------------------------------------------------------------------------

def remove_duplicate_paragraphs(text: str) -> str:
    """
    Remove exact duplicate paragraph blocks (common at page boundaries where
    marker-pdf re-emits the last lines of a page).
    Preserves the first occurrence; comparison is whitespace-normalised.
    """
    _heading = re.compile(r'^#{1,6}\s')
    # Only deduplicate blocks long enough to be prose paragraphs.
    # Short blocks (footnotes, brief phrases) legitimately repeat across sections.
    MIN_DEDUP_CHARS = 150
    blocks = re.split(r'\n{2,}', text)
    seen: set[str] = set()
    kept = []
    for block in blocks:
        key = re.sub(r'\s+', ' ', block.strip())
        if not key:
            continue
        too_short = len(key) < MIN_DEDUP_CHARS
        is_heading = _heading.match(block.strip())
        if too_short or is_heading or key not in seen:
            seen.add(key)
            kept.append(block)
    return '\n\n'.join(kept)


# ---------------------------------------------------------------------------
# Rule #5 — Spurious pipe characters
# ---------------------------------------------------------------------------

_TABLE_ROW = re.compile(r'^\s*\|')          # line starts with |
_TABLE_SEP  = re.compile(r'^\s*\|?[\s\-:]+\|')  # separator row (---|---)

def remove_spurious_pipes(text: str) -> str:
    """
    Remove stray | characters that are OCR/column-detection noise.
    Lines that are part of a genuine markdown table are left untouched.
    """
    lines = text.split('\n')
    cleaned = []
    for line in lines:
        if _TABLE_ROW.match(line) or _TABLE_SEP.match(line):
            cleaned.append(line)
        else:
            cleaned.append(re.sub(r'\s*\|\s*', ' ', line))
    return '\n'.join(cleaned)


# ---------------------------------------------------------------------------
# Rule #7 — Footnote markup normalisation
# ---------------------------------------------------------------------------

# Patterns are ordered from most-specific to least-specific to avoid
# partial rewrites leaving residual artefacts.
_FOOTNOTE_PATTERNS = [
    # <sup>$^{1}$</sup>  (fully wrapped in <sup> but contains LaTeX)
    (re.compile(r'<sup>\$\^\{(\d+)\}\$</sup>'), r'<sup>\1</sup>'),
    # $^{1}$</sup>  (missing opening <sup>)
    (re.compile(r'\$\^\{(\d+)\}\$</sup>'),       r'<sup>\1</sup>'),
    # <sup>$1$  (missing closing </sup> — append it)
    (re.compile(r'<sup>\$(\d+)\$(?!</sup>)'),     r'<sup>\1</sup>'),
    # ^{1}<sup>  (inverted order)
    (re.compile(r'\^\{(\d+)\}<sup>'),             r'<sup>\1</sup>'),
    # \(^{1}\)  (LaTeX inline math remnant)
    (re.compile(r'\\\(\^\{(\d+)\}\\\)'),          r'<sup>\1</sup>'),
    # $^{1}$  (bare LaTeX with no HTML wrapper)
    (re.compile(r'\$\^\{(\d+)\}\$'),              r'<sup>\1</sup>'),
    # ^1^  (simple double-caret notation)
    (re.compile(r'\^(\d+)\^'),                    r'<sup>\1</sup>'),
]

def normalize_footnote_markers(text: str) -> str:
    """Normalise all broken footnote marker variants to <sup>N</sup>."""
    for pattern, replacement in _FOOTNOTE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


# ---------------------------------------------------------------------------
# Rule #8b — Entirely-bold paragraphs
# ---------------------------------------------------------------------------

_HEADING = re.compile(r'^#{1,6}\s')

def _is_entirely_bold(block: str) -> bool:
    """
    Return True if every non-whitespace character in the block sits inside
    a **bold** or *italic* span — i.e. the block has no plain prose at all.
    Marker-pdf produces this when the source PDF uses a heavy body-text font.
    """
    s = block.strip()
    if not (s.startswith('**') and s.endswith('**')):
        return False
    # Strip all *...* and **...** spans; if nothing but whitespace remains
    # the block is entirely bold/italic.
    plain = re.sub(r'\*{1,2}.+?\*{1,2}', '', s, flags=re.DOTALL).strip()
    return plain == ''

def remove_paragraph_bold(text: str) -> str:
    """
    Strip ** markers from paragraphs where the entire block is bolded.
    Headings are left untouched. Inline bold within a paragraph is preserved.
    """
    blocks = re.split(r'\n{2,}', text)
    result = []
    for block in blocks:
        if not _HEADING.match(block.strip()) and _is_entirely_bold(block):
            block = re.sub(r'\*\*', '', block)
        result.append(block)
    return '\n\n'.join(result)


# ---------------------------------------------------------------------------
# Rule #9 — Inline page markers
# ---------------------------------------------------------------------------

def remove_inline_page_markers(text: str) -> str:
    """
    Remove page-number artefacts that marker-pdf injects mid-sentence.
    Only targets markers that appear after a word character (i.e., mid-text),
    to avoid removing legitimate reference numbers at the start of a line.
    """
    # [43] appearing after text
    text = re.sub(r'(?<=\w)\s*\[(\d{1,4})\]', '', text)
    # — 43 — / – 43 – style
    text = re.sub(r'\s*[—–]\s*\d{1,4}\s*[—–]\s*', ' ', text)
    return text


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

def clean(text: str) -> str:
    text = fix_broken_hyphenation(text)
    text = normalize_footnote_markers(text)
    text = remove_paragraph_bold(text)
    text = remove_inline_page_markers(text)
    text = remove_spurious_pipes(text)
    text = remove_duplicate_paragraphs(text)
    text = re.sub(r'\n{3,}', '\n\n', text)   # collapse excessive blank lines
    return text.strip() + '\n'


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    # Force UTF-8 output so filenames with decomposed Unicode (common on
    # iCloud-synced files from macOS) don't crash the cp1252 console encoder.
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

    if len(sys.argv) < 2:
        print("Usage: python marker_cleanup.py <file.md> [file2.md ...]")
        sys.exit(1)

    for arg in sys.argv[1:]:
        path = Path(arg)
        if not path.exists():
            print(f"Skipping (not found): {path}")
            continue
        if path.suffix.lower() != '.md':
            print(f"Skipping (not a .md file): {path}")
            continue

        original = path.read_text(encoding='utf-8')
        cleaned  = clean(original)

        out_path = path.with_stem(path.stem + '_cleaned')
        out_path.write_text(cleaned, encoding='utf-8')

        original_lines = original.count('\n')
        cleaned_lines  = cleaned.count('\n')
        print(f"{path.name}  →  {out_path.name}  ({original_lines} → {cleaned_lines} lines)")

        meta_json = path.with_name(path.stem + '_meta.json')
        if meta_json.exists():
            meta_json.unlink()
            print(f"Deleted: {meta_json.name}")


if __name__ == '__main__':
    main()
