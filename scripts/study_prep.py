#!/usr/bin/env python3
"""Preparation checks for a study written under prompts/study-prompt.md.

Three subcommands, one for each thing the first study could only report
on its own word:

  survey  Sweep the whole sources archive for the topic's vocabulary and
          say where it is dense, section by section, and which of those
          sections no note points to. The corpus of a study should come
          from the archive, not from the pointers of one note.

  lit     Query the indexes database for secondary literature, so that
          the received view has holders and the thesis is checked for
          precedents.

  check   Look up every row of the evidence table: the file exists, the
          original wording stands at the stated lines, and the stated
          page agrees with the page markers around it.

    python scripts/study_prep.py survey --terms "Welt*" "Umwelt*" "world*" \
        --notes transcendence-husserl-heidegger.md \
        --authors husserl heidegger --out research/<slug>/survey.md
    python scripts/study_prep.py lit 'husserl AND heidegger AND (world OR welt)' \
        --out research/<slug>/literature-candidates.md
    python scripts/study_prep.py check research/<slug>/evidence.md

Terms match whole words, case-insensitively. A trailing * opens the
right edge ("Welt*" matches Weltglaube), a leading * the left edge
("*welt" matches Umwelt, Lebenswelt). A term with neither matches the
bare word only, so "transcendent" does not fire inside "transcendental".

Paths: the sources archive is taken from --sources, else $SOURCES_DIR,
else ../sources/sources beside this repository. The index database is
taken from --db, else ../indexes/build/index.db.

`check` exits 1 if any wording is not found. `survey` and `lit` always
exit 0; they report and do not judge.
"""
import argparse
import os
import re
import sqlite3
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_SOURCES = os.environ.get("SOURCES_DIR") or os.path.normpath(
    os.path.join(REPO_ROOT, "..", "sources", "sources"))
DEFAULT_DB = os.path.normpath(
    os.path.join(REPO_ROOT, "..", "indexes", "build", "index.db"))

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
COMMENT_RE = re.compile(r"<!--(.*?)-->")
VARIANT_RE = re.compile(r"-(?:[a-c]|recheck)\.md$")
WINDOW = 60  # lines; the grain at which "densest stretch" is reported

STOPWORDS = {
    "de": {"der", "die", "das", "und", "ist", "nicht", "sich", "als"},
    "en": {"the", "and", "of", "is", "that", "which", "not", "this"},
    "fr": {"le", "la", "les", "et", "est", "une", "dans", "qui"},
    "nl": {"het", "een", "van", "niet", "zijn", "dat", "wordt", "ook"},
}


def read_lines(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read().split("\n")


def write_out(text, out):
    if out:
        os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
        with open(out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        print("wrote " + out)
    else:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stdout.write(text)


def text_files(sources, authors=None):
    """(folder, filename, path) for every text file outside notes/."""
    out = []
    for folder in sorted(os.listdir(sources)):
        full = os.path.join(sources, folder)
        if not os.path.isdir(full) or folder == "notes":
            continue
        if authors and folder not in authors:
            continue
        for name in sorted(os.listdir(full)):
            path = os.path.join(full, name)
            if name.endswith(".md") and os.path.getsize(path) > 0:
                out.append((folder, name, path))
    return out


# ------------------------------------------------------------- survey

def term_regex(terms):
    parts = []
    for term in terms:
        core = term.strip("*")
        if not core:
            continue
        # An open edge is simply left unanchored. The match then covers
        # only the stem, which is all a count needs, and the pattern
        # keeps a literal prefix, which keeps the sweep fast.
        left = "" if term.startswith("*") else r"(?<!\w)"
        right = "" if term.endswith("*") else r"(?!\w)"
        parts.append(left + re.escape(core) + right)
    if not parts:
        sys.exit("no usable terms")
    return re.compile("|".join(parts), re.IGNORECASE)


def guess_language(lines):
    counts = dict.fromkeys(STOPWORDS, 0)
    sample = " ".join(lines[len(lines) // 4:len(lines) // 4 + 1500]).lower()
    for word in re.findall(r"[a-zäöüéèàß]+", sample):
        for lang, words in STOPWORDS.items():
            if word in words:
                counts[lang] += 1
    best = max(counts, key=counts.get)
    return best if counts[best] else "?"


def sections_of(lines):
    """[(start, end, heading)], 1-based inclusive, covering the file."""
    starts = [(1, "(before first heading)")]
    for i, line in enumerate(lines, 1):
        m = HEADING_RE.match(line)
        if m:
            starts.append((i, m.group(2).strip("*# ")))
    out = []
    for n, (start, head) in enumerate(starts):
        end = starts[n + 1][0] - 1 if n + 1 < len(starts) else len(lines)
        if end >= start:
            out.append((start, end, head))
    return out


def densest_window(hit_lines):
    """(first line, hits) of the WINDOW-line stretch holding most hits."""
    best, best_n, lo = hit_lines[0], 1, 0
    for hi in range(len(hit_lines)):
        while hit_lines[hi] - hit_lines[lo] >= WINDOW:
            lo += 1
        if hi - lo + 1 > best_n:
            best, best_n = hit_lines[lo], hi - lo + 1
    return best, best_n


def note_pointers(sources, note_names):
    """{filename: set(line)} from `file.md:123`, `:123` and `:1`–`:9`.

    A bare `:n` belongs to the file named most recently in the note,
    which is how the topic notes are written. A range adds every line in
    it, so a section counts as pointed-to if a range crosses it.
    """
    pointers = {}
    token = re.compile(
        r"`([^`\s]+?\.md)?(?::(\d+))?`(?:\s*[–-]\s*`:(\d+)`)?")
    for name in note_names:
        path = os.path.join(sources, "notes", name)
        if not os.path.exists(path):
            print("note not found: " + path, file=sys.stderr)
            continue
        current = None
        for m in token.finditer("\n".join(read_lines(path))):
            fname, start, end = m.groups()
            if fname:
                current = os.path.basename(fname)
            if start and current:
                first, last = int(start), int(end or start)
                if last < first or last - first > 5000:
                    last = first
                pointers.setdefault(current, set()).update(
                    range(first, last + 1))
    return pointers


def cmd_survey(args):
    rx = term_regex(args.terms)
    pointers = note_pointers(args.sources, args.notes or [])
    files = text_files(args.sources, args.authors)
    rows, unpointed, silent = [], [], 0
    for folder, name, path in files:
        lines = read_lines(path)
        hits = [i for i, line in enumerate(lines, 1)
                for _ in range(len(rx.findall(line)))]
        if not hits:
            silent += 1
            continue
        pts = pointers.get(name, set())
        flags = []
        if not any(COMMENT_RE.search(l) for l in lines):
            flags.append("no page markers")
        if VARIANT_RE.search(name):
            flags.append("variant or recheck file")
        secs = []
        for start, end, head in sections_of(lines):
            in_sec = [h for h in hits if start <= h <= end]
            if not in_sec:
                continue
            peak, peak_n = densest_window(in_sec)
            pointed = any(start <= p <= end for p in pts)
            secs.append((len(in_sec), start, end, head, peak, peak_n, pointed))
            if not pointed and len(in_sec) >= args.min_hits:
                unpointed.append((len(in_sec), folder, name, start, end,
                                  head, peak, peak_n))
        secs.sort(reverse=True)
        rows.append((len(hits), folder, name, len(lines),
                     guess_language(lines), flags, secs, bool(pts)))
    rows.sort(key=lambda r: (-r[0], r[2]))
    unpointed.sort(key=lambda r: (-r[0], r[2]))

    o = ["# Corpus survey", ""]
    o.append("Terms: " + ", ".join("`%s`" % t for t in args.terms) + "  ")
    o.append("Notes compared: " + (", ".join(args.notes) if args.notes
                                   else "none") + "  ")
    o.append("Files swept: %d (%d with hits, %d silent)%s" % (
        len(files), len(rows), silent,
        "; folders: " + ", ".join(args.authors) if args.authors else ""))
    o += ["",
          "A hit count is a count of words, not of doctrine. Use it to "
          "decide what to open, never as evidence. A silent file is "
          "silent for these terms only.", ""]

    o += ["## Files by hits", "",
          "| Hits | File | Lang | Lines | Sections with hits | "
          "In the notes | Flags |", "| ---: | --- | --- | ---: | ---: | "
          "--- | --- |"]
    for hits, folder, name, n, lang, flags, secs, noted in rows[:args.top_files]:
        o.append("| %d | `%s/%s` | %s | %d | %d | %s | %s |" % (
            hits, folder, name, lang, n, len(secs),
            "yes" if noted else "**no**", "; ".join(flags)))
    if len(rows) > args.top_files:
        o.append("")
        o.append("%d further files with hits are not shown; raise "
                 "`--top-files`." % (len(rows) - args.top_files))

    o += ["", "## Dense sections no note points to", "",
          "Sections with at least %d hits in which none of the compared "
          "notes has a pointer. Each is to be read or excluded with a "
          "reason in the reading log. \"Peak\" is the first line of the "
          "%d-line stretch with most hits." % (args.min_hits, WINDOW), "",
          "| Hits | File | Lines | Section | Peak (hits) |",
          "| ---: | --- | --- | --- | --- |"]
    for hits, folder, name, start, end, head, peak, peak_n in \
            unpointed[:args.top_sections]:
        o.append("| %d | `%s/%s` | %d–%d | %s | :%d (%d) |" % (
            hits, folder, name, start, end,
            head[:70].replace("|", "/"), peak, peak_n))
    if len(unpointed) > args.top_sections:
        o.append("")
        o.append("%d further sections are not shown; raise "
                 "`--top-sections`." % (len(unpointed) - args.top_sections))

    o += ["", "## Densest sections per file", ""]
    for hits, folder, name, n, lang, flags, secs, noted in rows[:args.top_files]:
        o.append("**`%s/%s`** (%d hits)" % (folder, name, hits))
        o.append("")
        for count, start, end, head, peak, peak_n, pointed in secs[:args.per_file]:
            o.append("- %d–%d, %s: %d hits, peak :%d (%d)%s" % (
                start, end, head[:70], count, peak, peak_n,
                "" if pointed else "; not in the notes"))
        o.append("")
    write_out("\n".join(o) + "\n", args.out)
    return 0


# ---------------------------------------------------------------- lit

def cmd_lit(args):
    if not os.path.exists(args.db):
        sys.exit("no index database at %s; run `python3 scripts/build.py` "
                 "in the indexes repository" % args.db)
    con = sqlite3.connect(args.db)
    total = con.execute("select count(*) from sources").fetchone()[0]
    try:
        ids = [r[0] for r in con.execute(
            "select record_id from search where search match ? and "
            "record_type = 'source' order by rank limit ?",
            (args.query, args.limit))]
    except sqlite3.OperationalError as exc:
        sys.exit("query not accepted by FTS5: %s" % exc)
    o = ["# Literature candidates", "",
         "Query: `%s`  " % args.query,
         "Database: %d source records. If that is far below the count in "
         "the indexes README, the build is stale; rebuild before trusting "
         "a thin result." % total, "",
         "These are harvested, unreviewed metadata. A record shows that a "
         "publication exists and what its abstract says. It is not a "
         "reading of the publication, and nothing here may be quoted or "
         "paraphrased as the author's argument beyond the abstract.", ""]
    for rid in ids:
        row = con.execute(
            "select title, subtitle, year, container, id_doi, abstract "
            "from sources where id = ?", (rid,)).fetchone()
        if not row:
            continue
        title, sub, year, container, doi, abstract = row
        authors = [r[0] for r in _authors(con, rid)]
        o.append("- **%s%s** (%s). %s%s  " % (
            title, ": " + sub if sub else "", year or "n.d.",
            ", ".join(authors) + ". " if authors else "",
            container or ""))
        o.append("  `%s`%s  " % (rid, " · doi:" + doi if doi else ""))
        if abstract:
            text = " ".join(abstract.split())
            o.append("  Abstract: " + (text[:args.abstract_chars] + "…"
                     if len(text) > args.abstract_chars else text))
        else:
            o.append("  No abstract held: title only.")
    o.append("")
    o.append("%d records shown (limit %d)." % (len(ids), args.limit))
    write_out("\n".join(o) + "\n", args.out)
    return 0


def _authors(con, rid):
    rows = con.execute(
        "select family, given from source_authors where source_id = ? "
        "order by position", (rid,)).fetchall()
    return [(" ".join(p for p in (given, family) if p),)
            for family, given in rows if family or given]


# -------------------------------------------------------------- check

def normalize(s):
    s = COMMENT_RE.sub(" ", s)
    s = s.replace("­", "").replace(" ", " ")
    s = re.sub(r"[„“”‚‘’«»\"']", '"', s)
    s = re.sub(r"[*_`]", "", s)
    s = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", s)  # hyphenation at line end
    return re.sub(r"\s+", " ", s).strip().lower()


def find_fragments(haystack, fragments):
    pos = 0
    for frag in fragments:
        at = haystack.find(frag, pos)
        if at < 0:
            return False
        pos = at + len(frag)
    return True


def page_of_marker(comment):
    """The page number a marker carries, or None.

    Markers are running heads: '<!-- 44 -->', '<!-- 94 Destruktion … -->',
    '<!-- § 5. … 95 -->'. Bracketed numbers ('[7]') are the pagination of
    an earlier edition and are skipped.
    """
    body = comment.strip()
    if re.fullmatch(r"\[\d+\]", body):
        return None
    # Printer's signature marks in the Husserliana files ("Husserl Ideen II
    # 5", "14 Husserl Ideen II", "Husserl, Die Krisis 1") number the
    # binding sheets, not the pages.
    if re.search(r"(^|\d\s+)Husserl(,|\s+Ideen|\s+Die)\b", body):
        return None
    for pattern in (r"^(\d{1,4})\b", r"\b(\d{1,4})$"):
        m = re.search(pattern, body)
        if m:
            return int(m.group(1))
    return None


def markers_around(lines, first, last):
    before = after = None
    for i, line in enumerate(lines, 1):
        for m in COMMENT_RE.finditer(line):
            page = page_of_marker(m.group(1))
            if page is None:
                continue
            if i <= first:
                before = (page, i)
            elif i > last and after is None:
                after = (page, i)
    return before, after


def parse_table(path):
    """Rows of the first pipe table that has `file` and `lines` columns."""
    rows, header = [], None
    for raw in read_lines(path):
        if not raw.strip().startswith("|"):
            if header and rows:
                break
            continue
        cells = [c.strip().replace("\\|", "|") for c in
                 re.split(r"(?<!\\)\|", raw.strip().strip("|"))]
        if header is None:
            low = [c.lower() for c in cells]
            if "file" in low and "lines" in low:
                header = low
            continue
        if all(re.fullmatch(r":?-+:?", c) for c in cells if c):
            continue
        rows.append(dict(zip(header, cells)))
    if header is None:
        sys.exit("no table with `File` and `Lines` columns in " + path)
    return rows


def resolve(sources, name):
    name = name.strip("` ")
    direct = os.path.join(sources, name)
    if os.path.exists(direct):
        return direct
    base = os.path.basename(name)
    for folder in os.listdir(sources):
        cand = os.path.join(sources, folder, base)
        if os.path.exists(cand):
            return cand
    return None


def cmd_check(args):
    rows = parse_table(args.table)
    bad = warn = 0
    sys.stdout.reconfigure(encoding="utf-8")
    for n, row in enumerate(rows, 1):
        label = row.get("id") or row.get("passage") or "row %d" % n
        path = resolve(args.sources, row.get("file", ""))
        if not path:
            print("FAIL  %s: file not found: %s" % (label, row.get("file")))
            bad += 1
            continue
        nums = [int(x) for x in re.findall(r"\d+", row.get("lines", ""))]
        if not nums:
            print("FAIL  %s: no line numbers" % label)
            bad += 1
            continue
        first, last = min(nums), max(nums)
        lines = read_lines(path)
        original = row.get("original", "").strip()
        if not original or original in ("-", "–", "(paraphrase)"):
            print("WARN  %s: no original wording to look up" % label)
            warn += 1
        else:
            frags = [normalize(f) for f in re.split(r"…|\.\.\.|\[\.\.\.\]",
                                                    original)]
            frags = [f for f in frags if f]
            span = normalize("\n".join(
                lines[max(0, first - 1 - args.slack):last + args.slack]))
            if find_fragments(span, frags):
                print("ok    %s" % label)
            else:
                found = None
                for i in range(len(lines)):
                    window = normalize("\n".join(lines[i:i + 12]))
                    if window.find(frags[0]) >= 0 and find_fragments(
                            normalize("\n".join(
                                lines[i:i + 12 + (last - first)])), frags):
                        found = i + 1
                        break
                if found:
                    print("MOVED %s: not at %d–%d; found from line %d"
                          % (label, first, last, found))
                    warn += 1
                else:
                    print("FAIL  %s: wording not in %s"
                          % (label, os.path.basename(path)))
                    bad += 1
        stated = [int(x) for x in re.findall(
            r"\d+", re.sub(r"\(.*?\)|\[.*?\]", "", row.get("page", "")))]
        before, after = markers_around(lines, first, last)
        if before is None and after is None:
            if stated:
                print("WARN  %s: page %s stated, but the file has no page "
                      "markers near these lines" % (label, row.get("page")))
                warn += 1
        elif stated:
            lo = (before[0] - 1) if before else min(stated)
            hi = after[0] if after else max(stated)
            if min(stated) < lo or max(stated) > hi:
                print("WARN  %s: page %s stated; markers give %s before "
                      "and %s after" % (
                          label, row.get("page"),
                          "%d (line %d)" % before if before else "none",
                          "%d (line %d)" % after if after else "none"))
                warn += 1
    print("\n%d rows: %d failed, %d warnings" % (len(rows), bad, warn))
    return 1 if bad else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("survey", help="where the topic's words are dense")
    s.add_argument("--terms", nargs="+", required=True)
    s.add_argument("--notes", nargs="*", help="files in sources/notes/")
    s.add_argument("--authors", nargs="*", help="limit to these folders")
    s.add_argument("--sources", default=DEFAULT_SOURCES)
    s.add_argument("--min-hits", type=int, default=8)
    s.add_argument("--top-files", type=int, default=40)
    s.add_argument("--top-sections", type=int, default=60)
    s.add_argument("--per-file", type=int, default=6)
    s.add_argument("--out")
    s.set_defaults(func=cmd_survey)

    l = sub.add_parser("lit", help="secondary literature from indexes")
    l.add_argument("query", help="an FTS5 query")
    l.add_argument("--db", default=DEFAULT_DB)
    l.add_argument("--limit", type=int, default=60)
    l.add_argument("--abstract-chars", type=int, default=600)
    l.add_argument("--out")
    l.set_defaults(func=cmd_lit)

    c = sub.add_parser("check", help="look up the evidence table")
    c.add_argument("table")
    c.add_argument("--sources", default=DEFAULT_SOURCES)
    c.add_argument("--slack", type=int, default=3,
                   help="lines either side of the stated span")
    c.set_defaults(func=cmd_check)

    args = ap.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
