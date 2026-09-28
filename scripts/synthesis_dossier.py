#!/usr/bin/env python3
"""Stage 5: bind a Stage 4 draft's unit ids to the primary texts.

Stage 4 writes from the ledgers and nothing else, so every quote it
carries is a quote *of a commentary* - English prose that paraphrases
Husserl closely but is not his words. That discipline is what makes the
draft checkable; it is also why the draft cannot quote. A dossier is the
seam where that changes: one entry per unit id the draft cites, holding
the commentary-tier evidence the ledger already validated *and* a slot
for the passage in `sources/` that stands behind it.

    # build (or refresh) the dossier for a Stage 4 output
    python3 scripts/synthesis_dossier.py build \\
        synthesis/outputs/intentionalitaet-article-draft.md

    # what is still unfilled, by record
    python3 scripts/synthesis_dossier.py status intentionalitaet-article-draft

    # every filled quote must still be where it says it is
    python3 scripts/synthesis_dossier.py check intentionalitaet-article-draft

`build` is re-runnable. It rewrites the commentary-tier half of every
entry from the extraction records and leaves the `primary` half alone,
so filling the dossier is incremental and a re-extraction upstream never
costs the work already done below it.

The two halves differ in kind and the schema keeps them apart:

  commentary tier  Generated. Copied verbatim out of
                   `synthesis/extractions/<theme>/*.json`, already
                   checked by `synthesis_validate.py` against the
                   commentary it quotes.

  primary tier     Authored, by a pass that is allowed to open
                   `sources/` - the only stage that is. It may
                   substantiate a claim the ledger already carries. It
                   may never add one. A passage that says something the
                   ledger does not is a Stage 1 extraction task, not a
                   dossier entry.

`state: no-source` is a first-class answer and the honest one for most
of the Husserl spine: the corpus holds no copy of Hua XXVIII, Hua XLIII/2
or Hua XXXIII, so the claims that matter most cannot be raised to the
primary tier at all. `status` prints those separately, because they are
an acquisition list rather than a backlog.
"""

import argparse
import json
import os
import re
import sys
import unicodedata

import synthesislib as lib

DOSSIER_DIR = os.path.join(lib.SYNTHESIS_DIR, "dossiers")

# Where the primary texts live. The sources repo is a sibling checkout,
# not a submodule, so the path is a guess with an override rather than a
# fact. Nothing here writes to it.
DEFAULT_SOURCES = os.path.join(
    os.path.dirname(lib.REPO_ROOT), "sources", "sources")

UNIT_RE = re.compile(r"`((?:inh|[a-z0-9-]+)/[a-z0-9._-]+/\d{3})`")

# iCloud Drive rewrites accented filenames to NFD behind the repo's back,
# so `husserl-hua-13-zur-phänomenologie...` on disk may not be the byte
# string anything else in the corpus spells. Compare names decomposed and
# the mismatch stops existing. Same failure the PDF pipeline hits.
def _nfc(s):
    return unicodedata.normalize("NFC", s)


def sources_root(argv_value=None):
    root = argv_value or os.environ.get("SOURCES_ROOT") or DEFAULT_SOURCES
    root = os.path.abspath(root)
    if not os.path.isdir(root):
        sys.exit("no sources checkout at %s - pass --sources or set "
                 "SOURCES_ROOT" % root)
    return root


def resolve_source(root, rel):
    """Return the on-disk path for a `<author>/<file>.md` in sources/.

    Matches on the NFC-folded name so an iCloud-decomposed filename still
    resolves. Returns None rather than raising: an entry naming a file
    that is not there is a dossier error to report, not a crash.
    """
    rel = rel.replace("\\", "/")
    parts = rel.split("/")
    here = root
    for part in parts:
        if not os.path.isdir(here):
            return None
        want = _nfc(part)
        match = next((e for e in os.listdir(here) if _nfc(e) == want), None)
        if match is None:
            return None
        here = os.path.join(here, match)
    return here if os.path.isfile(here) else None


# ------------------------------------------------------------------ build


def index_units(theme):
    """Map every unit id in a theme's extraction records to its unit.

    The id prefix (`hua28`, `hga24`) is a record's own short key and is
    written into the ids rather than declared anywhere, so the only way
    to resolve one is to have read them all.
    """
    units = {}
    for path, rec in lib.load_extractions(theme):
        for unit in rec["units"]:
            units[unit["id"]] = (rec, unit)
    return units


def cited_ids(text):
    """Unit ids the draft actually cites, in order of first appearance.

    Order matters: a dossier read top to bottom should walk the article's
    argument, so the pass filling it stays in one text at a time instead
    of hopping between volumes.
    """
    seen = []
    for m in UNIT_RE.finditer(text):
        if m.group(1) not in seen:
            seen.append(m.group(1))
    return seen


BLANK_PRIMARY = {
    "state": "unfilled",
    "note": "",
    "original": None,
    "translation": None,
}

# Two different things end a hunt with nothing, and collapsing them would
# put a book on the buying list that no purchase could help:
#
#   not-in-corpus   The text exists; sources/ has no copy. Acquirable,
#                   and the one case that belongs on an acquisition list.
#   no-primary      There is nothing to find. The claim is the
#                   commentator's own gloss, reading or reconstruction,
#                   and stays at commentary tier however many volumes
#                   arrive.
NO_SOURCE_REASONS = ("not-in-corpus", "no-primary")


def build(args):
    out_path = os.path.join(lib.REPO_ROOT, args.output)
    if not os.path.isfile(out_path):
        sys.exit("no such Stage 4 output: %s" % args.output)
    text = lib.read_text(out_path)

    slug = os.path.splitext(os.path.basename(args.output))[0]
    theme = args.theme or slug.split("-")[0]
    units = index_units(theme)

    dossier_path = os.path.join(DOSSIER_DIR, slug + ".json")
    kept = {}
    if os.path.isfile(dossier_path):
        for e in lib.load_json(dossier_path)["entries"]:
            kept[e["id"]] = e.get("primary", dict(BLANK_PRIMARY))

    entries, unknown = [], []
    for uid in cited_ids(text):
        if uid.startswith("inh/"):
            continue  # inheritance records cite commentaries, not sources
        if uid not in units:
            unknown.append(uid)
            continue
        rec, unit = units[uid]
        entries.append({
            "id": uid,
            "commentary": rec["commentary"],
            "locator": unit["locator"],
            "primary_locator": unit.get("primary_locator", ""),
            "term": unit.get("term", ""),
            "status": unit.get("status", ""),
            "claim": unit.get("claim", ""),
            "commentary_quote": unit.get("quote", ""),
            "primary": kept.get(uid, dict(BLANK_PRIMARY)),
        })

    lib.write_json(dossier_path, {
        "schema_version": 1,
        "theme": theme,
        "output": args.output.replace("\\", "/"),
        "output_sha256": lib.sha256_of(out_path),
        "entries": entries,
    })

    print("%s: %d entries from %d cited ids"
          % (os.path.relpath(dossier_path, lib.REPO_ROOT),
             len(entries), len(entries) + len(unknown)))
    if kept:
        carried = sum(1 for e in entries
                      if e["primary"]["state"] != "unfilled")
        print("carried %d filled entr%s forward"
              % (carried, "y" if carried == 1 else "ies"))
    for uid in unknown:
        print("warning: %s cited by the draft, not in any extraction record"
              % uid)
    return 0


# ------------------------------------------------------------------- fill


def slice_quote(path, line, start, end, window=40):
    """Cut a passage out of a source file between two anchors.

    The pass filling a dossier types the anchors - a few words at each
    edge - and never the quote. That is the whole point: rule 1 of
    synthesis/CLAUDE.md says copy quotes out of the file and never
    retype one, and a remembered quote is the failure the apparatus
    exists to catch. Anchors are cheap to verify and a wrong one fails
    loudly here rather than quietly in the prose.

    Reads a window rather than the single line because the German
    volumes are hard-wrapped from print, so a sentence is routinely four
    lines. Line-break hyphens are rejoined on the way out.
    """
    lines = lib.read_text(path).split("\n")
    if not 1 <= line <= len(lines):
        return None, "line %d outside file (%d lines)" % (line, len(lines))
    chunk = "\n".join(lines[line - 1:line - 1 + window])

    i = chunk.find(start)
    if i == -1:
        return None, "start anchor not found at line %d: %r" % (line, start)
    j = chunk.find(end, i + len(start))
    if j == -1:
        return None, "end anchor not found after start: %r" % end

    text = LINE_HYPHEN.sub(r"\1\2", chunk[i:j + len(end)])
    return re.sub(r"\s+", " ", text).strip(), None


def fill(args):
    """Apply a spec file of anchors to a dossier.

    The spec is a list of {id, side, file, line, from, to, language} for
    passages found, and {id, state: "no-source", note} for the ones the
    corpus cannot supply. Re-running is safe: an entry named twice is
    simply re-sliced from the file as it now stands.
    """
    path, dossier = load_dossier(args.slug)
    root = sources_root(args.sources)
    spec = lib.load_json(os.path.join(lib.REPO_ROOT, args.spec))
    by_id = {e["id"]: e for e in dossier["entries"]}

    filled, blocked, problems = 0, 0, []
    for item in spec:
        entry = by_id.get(item["id"])
        if entry is None:
            problems.append("%s: not in this dossier" % item["id"])
            continue

        if item.get("state") == "no-source":
            if item.get("reason") not in NO_SOURCE_REASONS:
                problems.append("%s: no-source needs reason %s"
                                % (item["id"], "/".join(NO_SOURCE_REASONS)))
                continue
            entry["primary"] = {"state": "no-source",
                                "reason": item["reason"],
                                "note": item["note"],
                                "original": None, "translation": None}
            blocked += 1
            continue

        src = resolve_source(root, item["file"])
        if src is None:
            problems.append("%s: no such file in sources/: %s"
                            % (item["id"], item["file"]))
            continue
        quote, err = slice_quote(src, item["line"], item["from"], item["to"])
        if err:
            problems.append("%s [%s]: %s" % (item["id"], item["side"], err))
            continue

        if entry["primary"]["state"] != "found":
            entry["primary"] = {"state": "found", "note": item.get("note", ""),
                                "original": None, "translation": None}
        elif item.get("note"):
            entry["primary"]["note"] = item["note"]
        entry["primary"][item["side"]] = {
            "file": item["file"],
            "line": item["line"],
            "language": item.get("language", ""),
            "quote": quote,
        }
        filled += 1

    lib.write_json(path, dossier)
    print("sliced %d passage(s), recorded %d no-source entr%s"
          % (filled, blocked, "y" if blocked == 1 else "ies"))
    for p in problems:
        print("error:   %s" % p)
    return 1 if problems else 0


# ----------------------------------------------------------------- status


def load_dossier(slug):
    path = os.path.join(DOSSIER_DIR, slug + ".json")
    if not os.path.isfile(path):
        sys.exit("no dossier at %s - run `build` first"
                 % os.path.relpath(path, lib.REPO_ROOT))
    return path, lib.load_json(path)


def status(args):
    _, dossier = load_dossier(args.slug)
    by_record = {}
    for e in dossier["entries"]:
        key = e["id"].rsplit("/", 1)[0]
        by_record.setdefault(key, []).append(e)

    def state(e):
        return e["primary"]["state"]

    print("%-30s %5s %5s %5s %5s" % ("record", "n", "found", "none", "todo"))
    for key in sorted(by_record, key=lambda k: -len(by_record[k])):
        rows = by_record[key]
        print("%-30s %5d %5d %5d %5d"
              % (key.split("/")[-1], len(rows),
                 sum(1 for e in rows if state(e) == "found"),
                 sum(1 for e in rows if state(e) == "no-source"),
                 sum(1 for e in rows if state(e) == "unfilled")))

    for reason, heading in (
            ("not-in-corpus", "no copy in sources/ - acquisition list:"),
            ("no-primary", "nothing to acquire - stays at commentary tier:")):
        rows = [e for e in dossier["entries"]
                if state(e) == "no-source"
                and e["primary"].get("reason") == reason]
        if not rows:
            continue
        print("\n%s" % heading)
        for e in rows:
            print("  %-28s %s" % (e["id"], e["primary"]["note"]))
    return 0


# ------------------------------------------------------------------ check


# A hyphen at a line break is the typesetter's, not Heidegger's:
# `Mißdeu-\ntung` is one word broken across two printed lines, and the
# converted markdown keeps the break. Quoting it back with the hyphen in
# place would be faithful to the file and wrong about the German.
#
# Which hyphen it is can only be told while the line breaks survive.
# `Haß- und Liebbare` is a suspended compound and keeps its hyphen;
# `Haß-\nund` would be a broken word. Both look identical once the text
# is flattened to spaces, so LINE_HYPHEN - the one that edits a recorded
# quote - insists on the newline, and SOFT_HYPHEN - which only ever
# widens what a search will match - is allowed to guess.
LINE_HYPHEN = re.compile(r"([a-zäöüß])-\n(\w)")
SOFT_HYPHEN = re.compile(r"([a-zäöüß])-\s+([a-zäöüß])")

_FLAT = {}


def dehyphenate(s):
    return SOFT_HYPHEN.sub(r"\1\2", s)


def flatten(path):
    """Normalized whole-file text, plus a map from offset back to line.

    Matching line by line would work for GA 24, whose paragraphs are one
    long line each, and fail for GA 20, which is hard-wrapped mid-
    sentence from the print edition - "Jede / Intention hat in sich eine
    Tendenz zur Erfüllung" is two lines and one sentence. Since the
    corpus holds both conventions and a quote must not care which, the
    check runs against the flattened document and reports the line the
    match starts on.

    Returned twice over, plain and de-hyphenated, so either spelling of a
    line-broken word verifies. De-hyphenating deletes characters and so
    shifts every offset after the first hyphen - by hundreds of
    characters in a volume this size - which would put the reported line
    pages away from the quote. `anchors` maps a position in the
    de-hyphenated text back to one in the plain text so the line number
    stays exact either way.
    """
    if path in _FLAT:
        return _FLAT[path]
    starts, parts, offset = [], [], 0
    for line in lib.read_text(path).split("\n"):
        norm = lib.normalize_quote(line)
        starts.append((offset, len(norm)))
        parts.append(norm)
        offset += len(norm) + 1
    flat = " ".join(parts)

    pieces, anchors, pos, seen = [], [], 0, 0
    for m in SOFT_HYPHEN.finditer(flat):
        piece = flat[pos:m.start(1) + 1]     # up to and excluding the hyphen
        anchors.append((seen, pos))
        pieces.append(piece)
        seen += len(piece)
        pos = m.start(2)                     # resume at the word's tail
    anchors.append((seen, pos))
    pieces.append(flat[pos:])

    _FLAT[path] = (flat, "".join(pieces), starts, anchors)
    return _FLAT[path]


def to_plain(anchors, offset):
    """Map an offset in the de-hyphenated text back to the plain one."""
    lo, hi = 0, len(anchors) - 1
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if anchors[mid][0] <= offset:
            lo = mid
        else:
            hi = mid - 1
    seen, pos = anchors[lo]
    return pos + (offset - seen)


def line_of(starts, offset):
    lo, hi = 0, len(starts) - 1
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if starts[mid][0] <= offset:
            lo = mid
        else:
            hi = mid - 1
    return lo + 1


def check_side(root, entry, side, errors, warnings):
    """Verify one recorded passage is verbatim where the entry says.

    A quote that has moved is a warning, not an error: re-converting a
    source file shifts every line below the change, and the passage is
    still the passage. A quote that is nowhere in the file is the failure
    this whole apparatus exists to catch.
    """
    block = entry["primary"].get(side)
    if not block:
        return
    where = "%s [%s]" % (entry["id"], side)
    path = resolve_source(root, block["file"])
    if path is None:
        errors.append("%s: no such file in sources/: %s"
                      % (where, block["file"]))
        return

    want = lib.normalize_quote(block["quote"])
    if not want:
        errors.append("%s: empty quote" % where)
        return

    flat, flat_dehy, starts, anchors = flatten(path)
    if want in flat:
        haystack, remap = flat, lambda o: o
    else:
        haystack = flat_dehy
        remap = lambda o: to_plain(anchors, o)
        if want not in haystack:
            want = dehyphenate(want)

    hits, at = [], haystack.find(want)
    while at != -1 and len(hits) < 5:
        hits.append(line_of(starts, remap(at)))
        at = haystack.find(want, at + 1)

    if not hits:
        errors.append("%s: quote not in %s" % (where, block["file"]))
    elif block.get("line") in hits:
        return
    else:
        warnings.append("%s: line %s -> %s"
                        % (where, block.get("line"),
                           ", ".join(str(h) for h in hits)))
        if len(hits) == 1:
            block["line"] = hits[0]


def check(args):
    path, dossier = load_dossier(args.slug)
    root = sources_root(args.sources)

    errors, warnings = [], []
    checked = 0
    for entry in dossier["entries"]:
        primary = entry["primary"]
        if primary["state"] == "found" and not (primary.get("original")
                                                or primary.get("translation")):
            errors.append("%s: state 'found' with nothing recorded" % entry["id"])
        if primary["state"] == "no-source" and not primary.get("note"):
            errors.append("%s: state 'no-source' needs a note saying why"
                          % entry["id"])
        for side in ("original", "translation"):
            if primary.get(side):
                checked += 1
                check_side(root, entry, side, errors, warnings)

    print("checked %d recorded passage(s) in %s"
          % (checked, os.path.relpath(path, lib.REPO_ROOT)))
    for w in warnings:
        print("warning: %s" % w)
    for e in errors:
        print("error:   %s" % e)

    if warnings and args.fix:
        lib.write_json(path, dossier)
        print("rewrote line numbers for %d passage(s)" % len(warnings))

    if errors:
        print("\nFAILED: %d error(s), %d warning(s)"
              % (len(errors), len(warnings)))
        return 1
    print("OK")
    return 0


# ----------------------------------------------------------------- verify

# Blockquote runs and any long span between double quotes. Short spans
# are skipped: "Dasein", "intentio" and the like are terms in use, not
# quotations, and checking them would drown the real findings.
QUOTED_RE = re.compile(r'(?:^> .*\n)+|[""]([^""]{25,})[""]|"([^"]{25,})"', re.M)
ELLIPSIS_RE = re.compile(r"\s*\[(?:\.\.\.|…)\]\s*")
CITATION_RE = re.compile(r"\((?:GA|SZ|Hua)[^)]*\)")


def quoted_spans(text):
    """Every span of an article that presents itself as a quotation."""
    spans = []
    for m in QUOTED_RE.finditer(text):
        raw = m.group(1) or m.group(2)
        if raw is None:                      # a blockquote run
            raw = " ".join(l.lstrip("> ") for l in m.group(0).strip().split("\n"))
        raw = CITATION_RE.sub("", raw)
        for part in ELLIPSIS_RE.split(raw):
            part = part.strip().strip('".,;:')
            if len(part) >= 25:
                spans.append(part)
    return spans


def verify(args):
    """Check an article's quotations against the texts they claim.

    The dossier proves a passage exists. It cannot prove the prose
    reproduced it, and prose is where quotes get bent - a word order
    swapped, a page-break word silently mended, a clause closed with a
    full stop the sentence does not have. This re-reads the finished
    article and puts every quoted span back against the files.

    A span found in a source file is primary tier and passes. A span
    found only in a commentary is reported rather than failed: quoting a
    commentary is legitimate, provided the sentence says that is what it
    is doing, and only the author can confirm that it does. A span found
    in neither is an error, and no article ships with one.
    """
    _, dossier = load_dossier(args.slug)
    root = sources_root(args.sources)

    sources, missing = [], []
    for entry in dossier["entries"]:
        for side in ("original", "translation"):
            block = entry["primary"].get(side)
            if not block:
                continue
            path = resolve_source(root, block["file"])
            if path:
                sources.append((block["file"], path))
            else:
                missing.append(block["file"])
    commentaries = []
    for slug in sorted({e["commentary"] for e in dossier["entries"]}):
        for doc in lib.load_corpus()["documents"]:
            if doc["slug"] == slug:
                commentaries.append((slug, os.path.join(lib.REPO_ROOT, doc["path"])))

    def holds(pool, needle):
        for name, path in pool:
            flat, dehy, _, _ = flatten(path)
            if needle in flat or needle in dehy or dehyphenate(needle) in dehy:
                return name
        return None

    text = lib.read_text(os.path.join(lib.REPO_ROOT, args.article))
    spans = quoted_spans(text)
    errors, reported = [], []
    for span in spans:
        want = re.sub(r"^[^0-9a-zäöüß]+", "", lib.normalize_quote(span))
        if holds(sources, want):
            continue
        where = holds(commentaries, want)
        if where:
            reported.append((span, where))
        else:
            errors.append(span)

    print("checked %d quoted span(s) in %s"
          % (len(spans), args.article.replace("\\", "/")))
    for name in sorted(set(missing)):
        print("warning: dossier names a file not in sources/: %s" % name)
    for span, where in reported:
        print("commentary tier: %.90s\n                 (%s)" % (span, where))
    for span in errors:
        print("error:   not in any cited text: %.100s" % span)

    if errors:
        print("\nFAILED: %d span(s) match nothing" % len(errors))
        return 1
    print("OK")
    return 0


# -------------------------------------------------------------------- cli


def main(argv):
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("build", help="create or refresh a dossier")
    b.add_argument("output", help="repo-relative path of the Stage 4 output")
    b.add_argument("--theme", help="theme id (default: the slug's first word)")
    b.set_defaults(func=build)

    f = sub.add_parser("fill", help="apply a spec of anchors, slicing from sources/")
    f.add_argument("slug")
    f.add_argument("spec", help="repo-relative path of the anchor spec (JSON)")
    f.add_argument("--sources", help="path to the sources/sources checkout")
    f.set_defaults(func=fill)

    s = sub.add_parser("status", help="what is filled, what is missing")
    s.add_argument("slug", help="dossier slug, e.g. intentionalitaet-article-draft")
    s.set_defaults(func=status)

    v = sub.add_parser("verify", help="check a finished article's quotations")
    v.add_argument("slug")
    v.add_argument("article", help="repo-relative path of the article")
    v.add_argument("--sources", help="path to the sources/sources checkout")
    v.set_defaults(func=verify)

    c = sub.add_parser("check", help="re-verify every recorded passage")
    c.add_argument("slug")
    c.add_argument("--sources", help="path to the sources/sources checkout")
    c.add_argument("--fix", action="store_true",
                   help="write back line numbers that have drifted")
    c.set_defaults(func=check)

    args = p.parse_args(argv[1:])
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
