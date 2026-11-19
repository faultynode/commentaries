# -*- coding: utf-8 -*-
"""Build research/constitution-husserl-ideas-ii/evidence.md (second study).

Each entry: (id, file key, section, hint line, [fragments]).
The script finds the fragments in the file, records the line span, takes the
page from the page markers, and for Hua IV derives the English page opening
from the bracketed Hua page numbers printed in the English file.
"""
import io
import os
import re
import sys

# Paths derived from this file's location (draft/ -> constitution-husserl-ideas-ii/
# -> research/ -> repo root); the sources repo is the sibling checkout.
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SRC = os.path.join(os.path.dirname(REPO), "sources", "sources")
sys.path.insert(0, os.path.join(REPO, "scripts"))
import study_prep as sp  # noqa: E402

FILES = {
    "H4": "husserl/husserl-hua-4-ideen-ii-phanomenologische-untersuchungen-zur-konstitution.md",
    "H3": "husserl/husserl-hua-3-1-ideen-i-allgemeine-einfuhrung-in-die-reine-phanomenologie-recheck.md",
    "G20": "heidegger/heidegger-ga-20-prolegomena-zur-geschichte-des-zeitbegriffs.md",
    "MC": "moran/moran-cohen-the-husserl-dictionary.md",
    "NY": "new-yearbook-for-phenomenology/The new yearbook for phenomenology and phenomenological - M Brainard; Burt C Hopkins; Steven Galt Crowell.md",
}
EN = "husserl/husserl-cw3-ideas-pertaining-to-a-pure-phenomenology-and-to-a-phenomenological-philosophy-second-book.md"

from entries import ENTRIES as _E1  # noqa: E402
from entries2 import ENTRIES2  # noqa: E402
ENTRIES = _E1 + ENTRIES2

# Pages settled against the page breaks printed in the English file, where a
# marker in the German file stands before a paragraph that begins on the
# page before (see reading-log.md, "Pages").
OVERRIDE = {"B1": 4, "B2": 4, "C3": 37, "C4": 37, "C8": 42, "C9": 42,
            "C10": 42, "C12": 43, "C13": 43, "C21": 57, "C22": 57, "C27": 65,
            "E6": 124, "E22": 138, "E25": 143, "E26": 145, "E28": 155,
            "G2": 183, "G5": 189, "G22": 244, "G23": 245, "G24": 245,
            "G28": 246, "G29": 248, "G32": 251, "C17": 44, "C38": 44,
            "H3": 297, "H10": 301, "G46": 201, "E42": 124, "E43": 125,
            "G63": 248, "C34": 36, "C36": 36, "B13": 24, "B14": 27,
            "B15": 27, "C42": 53, "N5": 305, "N11": 139, "N12": 301,
            "N13": 301, "N14": 300, "N15": 302, "N6": 245, "N7": 245,
            "N9": 252, "N4": 175}
SHOWN = {"G22": "244–245"}
_cache = {}


def lines_of(key):
    if key not in _cache:
        with io.open(os.path.join(SRC, FILES[key]), encoding="utf-8") as f:
            _cache[key] = f.read().split("\n")
    return _cache[key]


def locate(lines, hint, frags):
    nfr = [sp.normalize(f) for f in frags]

    def try_at(i):
        # i is 0-based start; window grows until all fragments found
        for width in range(1, 14):
            span = sp.normalize("\n".join(lines[i:i + width]))
            if span.find(nfr[0]) < 0:
                continue
            if sp.find_fragments(span, nfr):
                return i, i + width - 1
        return None

    order = []
    if hint:
        for d in range(0, 8):
            for s in (hint - 1 - d, hint - 1 + d):
                if 0 <= s < len(lines) and s not in order:
                    order.append(s)
    order += [i for i in range(len(lines)) if i not in set(order)]
    for i in order:
        if sp.normalize(lines[i]).find(nfr[0][:25]) < 0 and \
                sp.normalize("\n".join(lines[i:i + 2])).find(nfr[0]) < 0:
            continue
        got = try_at(i)
        if got:
            # tighten the start: first line that holds the start of fragment 1
            return got[0] + 1, got[1] + 1
    return None


def marker_page(body, page):
    """Page carried by a comment, given the page reached so far."""
    body = body.strip()
    m = re.match(r"^p[.]\s*([0-9]{1,4})", body)
    if m:
        return int(m.group(1))
    p = sp.page_of_marker(body)
    if p is None:
        return None
    if re.fullmatch(r"\d{1,4}", body) and page is not None and not (
            page < p <= page + 2):
        return None  # line counters and sheet numbers
    if page is not None and not (page <= p <= page + 12):
        return None
    return p


def page_at(lines, first, frag):
    """Last page marker before the fragment (markers inside the line count)."""
    page = None
    for i, line in enumerate(lines[:first], 1):
        if i < first:
            for m in sp.COMMENT_RE.finditer(line):
                p = marker_page(m.group(1), page)
                if p is not None:
                    page = p
    line = lines[first - 1]
    key = re.sub(r"\W+", "", frag)[:12].lower()
    pos = None
    stripped = ""
    idx = []
    for j, ch in enumerate(line):
        if ch.isalnum():
            stripped += ch.lower()
            idx.append(j)
    k = stripped.find(key)
    if k >= 0:
        pos = idx[k]
    for m in sp.COMMENT_RE.finditer(line):
        p = marker_page(m.group(1), page)
        if p is None:
            continue
        if pos is None or m.start() < pos:
            page = p
    return page


def english_map():
    with io.open(os.path.join(SRC, EN), encoding="utf-8") as f:
        el = f.read().split("\n")
    out = {}
    last_num = None
    for i, line in enumerate(el, 1):
        s = line.strip()
        if re.fullmatch(r"\d{1,3}", s) and i > 200:
            last_num = int(s)
        for m in re.finditer(r"\[(\d{1,3})\]", line):
            p = int(m.group(1))
            if i > 200 and p not in out and last_num and                     p <= last_num <= p + 16:
                out[p] = (last_num, i)
    return out


def opening(n):
    return (n - 1, n) if n % 2 else (n, n)


def english_for(emap, page):
    if page is None:
        return "—", "—"
    a = emap.get(page)
    b = emap.get(page + 1)
    if a is None:
        lower = [p for p in emap if p < page]
        if not lower:
            return "—", "—"
        a = emap[max(lower)]
        note = " (no bracket for %d; from [%d])" % (page, max(lower))
    else:
        note = ""
    lo = opening(a[0])[0]
    hi = opening(b[0])[1] if b else opening(a[0])[1]
    if hi < lo or hi - lo > 4:
        hi = opening(a[0])[1]
    return str(a[1]), ("%d–%d" % (lo, hi) if hi != lo else str(lo)) + note


def main():
    emap = english_map()
    rows, problems = [], []
    for eid, key, section, hint, frags, *rest in ENTRIES:
        lines = lines_of(key)
        got = locate(lines, hint, frags)
        if not got:
            problems.append("NOT FOUND %s: %s" % (eid, frags[0][:60]))
            continue
        first, last = got
        page = page_at(lines, first, frags[0])
        shown = page
        if eid in OVERRIDE:
            page = OVERRIDE[eid]
            shown = SHOWN.get(eid, page)
        if key == "H4":
            eline, epage = english_for(emap, page if isinstance(page, int) else None)
            efile = "`%s`" % os.path.basename(EN)
        else:
            eline, epage, efile = "—", "—", "—"
        rows.append("| %s | `%s` | %s | %s | %s | %s | %s | %s | %s |" % (
            eid, os.path.basename(FILES[key]),
            str(first) if first == last else "%d–%d" % (first, last),
            section, shown if shown is not None else "[page not located]",
            " … ".join(frags).replace("|", "\\|"), efile, eline, epage))
    head = """# Evidence: the concept of constitution in *Ideen II* (second study)

Step 8 of `prompts/study-prompt.md`, 2026-11-14. Generated by a scratch script (`build_evidence.py` with `entries.py`) and checked with `python scripts/study_prep.py check`. The table of the first study is kept in `previous-2026-11-13/evidence.md`. Paths under `../sources/sources/`. Page = the page marker standing before the wording in the file (Hua, GA). English page (Hua IV rows only) = the opening or openings of *Ideas II* (Rojcewicz and Schuwer, CW3) in which the Hua page stands, found from the bracketed Hua page numbers the English file prints: the bare page numeral before `[p]` to the one before `[p+1]`. The English file runs facing pages together, so an opening is given as its two pages. English lines = the line of the bracket `[p]`. '—' = no English held with page markers for this text.

| ID | File | Lines | Section | Page | Original | English file | English lines | English page |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
"""
    out = os.path.join(REPO, "research", "constitution-husserl-ideas-ii", "evidence.md")
    with io.open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(head + "\n".join(rows) + "\n")
    sys.stdout.reconfigure(encoding="utf-8")
    print("%d rows written" % len(rows))
    for p in problems:
        print(p)


if __name__ == "__main__":
    main()
