#!/usr/bin/env python3
"""Work the term lexicon: check it, expand it into search terms, attest it.

`synthesis/lexicon.json` registers the corpus's terms of art - one entry
per headword, its original-language forms, and the English renderings it
travels under. It is retrieval apparatus. It says what to search for and,
where a commentary glossed a term itself, where that rendering was seen.
It never says what a text claims: an extraction unit may quote only a
commentary, and nothing here is quotable. See docs/lexicon-design.md.

    # every check: schema, references, and the attested renderings
    python3 scripts/synthesis_lexicon.py --check

    # what themes.json is missing, for one theme or all of them
    python3 scripts/synthesis_lexicon.py --expand --theme leib
    python3 scripts/synthesis_lexicon.py --expand --theme leib --json

    # which registered renderings the corpus actually contains
    python3 scripts/synthesis_lexicon.py --attest --theme sorge

    # headwords with no theme, by how much of the corpus they touch
    python3 scripts/synthesis_lexicon.py --candidates

Nothing here writes. `--expand` prints a diff for a human to paste into
`themes.json`, because widening a theme's search terms changes what an
absence claim means and that is a judgement, not a merge.
"""

import argparse
import os
import sys

import synthesislib as lib

LEXICON_PATH = os.path.join(lib.SYNTHESIS_DIR, "lexicon.json")
SCHEMA_PATH = os.path.join(lib.SYNTHESIS_DIR, "schema", "lexicon.schema.json")


def load_lexicon():
    if not os.path.exists(LEXICON_PATH):
        raise SystemExit("synthesis/lexicon.json is missing")
    return lib.load_json(LEXICON_PATH)


def entry_terms(entry):
    """Everything an entry contributes to a search: forms and renderings."""
    return list(entry["forms"]) + [r["english"] for r in entry["renderings"]]


def select(lexicon, args):
    out = []
    for e in lexicon["entries"]:
        if args.theme and e.get("theme") != args.theme:
            continue
        if args.author and args.author not in e.get("authors", []):
            continue
        if args.entry and e["id"] != args.entry:
            continue
        out.append(e)
    return out


def term_hits(body, needle):
    """`lib.count_terms(body, [term])` for one already-normalized term.

    Same answer, different cost. An attestation pass counts every
    registered term against every document - a hundred-odd terms over 53
    files is six thousand scans of a 2.9-million-word corpus, and at
    regex speed that is three quarters of a minute. The matcher's pattern
    is a literal with a left-hand word boundary, so the work splits: find
    the occurrences with `str.find`, which is a memchr and not a
    backtracker, then reject the ones that begin inside a longer word.
    Cost becomes proportional to how often the term occurs rather than to
    how long the corpus is.

    Exact, not approximate: `normalize_quote` has already stripped the
    only non-alphanumeric character `\w` matches, so the preceding-char
    test and the lookbehind agree. Checked against `count_terms` over
    every term in the lexicon and every document in the corpus.
    """
    n = 0
    i = body.find(needle)
    while i != -1:
        if i == 0 or not body[i - 1].isalnum():
            n += 1
        i = body.find(needle, i + 1)
    return n


def present(body, term):
    return term_hits(body, lib.normalize_quote(term)) > 0


# ------------------------------------------------------------------- check


def check(lexicon, quiet=False):
    """Schema, referential integrity, and every attested rendering.

    The last of those is the only one with teeth: a rendering sourced to
    the corpus names a section, and this looks the section up and
    confirms both halves of the pairing are in it. An entry can still be
    wrong about what a term means - nothing here checks that - but it
    cannot claim a commentary renders Vorhandenheit as `occurrent` at a
    place where neither word appears.
    """
    errors, warnings = [], []
    schema = lib.load_json(SCHEMA_PATH)
    for err in lib.check_schema(lexicon, schema):
        errors.append("lexicon.json: %s" % err)
    if errors:
        return errors, warnings

    sources = {s["id"]: s for s in lexicon["sources"]}
    themes = lib.themes()
    ids = set()
    corpus = lib.build_corpus()
    cmap = lib.corpus_map(corpus)
    checked = 0

    for e in lexicon["entries"]:
        where = "lexicon.json [%s]" % e["id"]
        if e["id"] in ids:
            errors.append("%s: duplicate entry id" % where)
        ids.add(e["id"])
        if e.get("theme") and e["theme"] not in themes:
            errors.append("%s: theme %r is not in themes.json" % (where, e["theme"]))

        for r in e["renderings"]:
            src = sources.get(r["source"])
            if src is None:
                errors.append("%s: unknown source %r" % (where, r["source"]))
                continue
            if src["kind"] == "commentary-corpus" and not r.get("locator"):
                errors.append("%s: rendering %r is sourced to the corpus and "
                              "must carry a locator" % (where, r["english"]))
                continue
            if not r.get("locator"):
                continue

            try:
                slug, sec_id = lib.parse_locator(r["locator"])
            except ValueError as exc:
                errors.append("%s: %s (%s)" % (where, exc, r["locator"]))
                continue
            doc = cmap.get(slug)
            if doc is None:
                errors.append("%s: unknown commentary %r" % (where, slug))
                continue
            sec = lib.section_map(doc).get(sec_id)
            if sec is None:
                errors.append("%s: no section %r in %s" % (where, sec_id, slug))
                continue

            checked += 1
            body = lib.normalize_quote(lib.section_text(doc, sec))
            if not present(body, r["english"]):
                errors.append("%s: %r does not occur in %s"
                              % (where, r["english"], r["locator"]))
            if not any(present(body, f) for f in e["forms"]):
                errors.append("%s: no form of %s occurs in %s - the rendering "
                              "is not attested there, only the English"
                              % (where, e["headword"], r["locator"]))

    for e in lexicon["entries"]:
        for other in e.get("contrast_with", []):
            if other not in ids:
                errors.append("lexicon.json [%s]: contrast_with names unknown "
                              "entry %r" % (e["id"], other))

        # The matcher lowercases before searching, so two forms differing only
        # in case are one search term written twice - harmless in the file,
        # misleading in an --attest report that shows the same count twice.
        folded = {}
        for f in e["forms"]:
            folded.setdefault(f.lower(), []).append(f)
        for _, group in sorted(folded.items()):
            if len(group) > 1:
                warnings.append("[%s]: forms %s differ only in case and search "
                                "as one term" % (e["id"], ", ".join(group)))

    # A rendering two entries share is a real property of this corpus, not a
    # mistake - Besorgen and Bekuemmerung are both 'concern' here. What must
    # not happen is that it goes unrecorded: a search on the shared English
    # cannot separate them, and an absence claim over it says nothing about
    # which term is absent. contrast_with is where that gets written down.
    by_rendering = {}
    for e in lexicon["entries"]:
        for r in e["renderings"]:
            by_rendering.setdefault(r["english"].lower(), []).append(e)
    for english, sharers in sorted(by_rendering.items()):
        if len(sharers) < 2:
            continue
        for e in sharers:
            linked = set(e.get("contrast_with", []))
            unlinked = [o["id"] for o in sharers
                        if o["id"] != e["id"] and o["id"] not in linked]
            if unlinked:
                warnings.append("[%s]: renders as %r, and so does %s, with no "
                                "contrast_with between them"
                                % (e["id"], english, ", ".join(sorted(unlinked))))

    # A theme whose terms nobody registered is not an error - the lexicon is
    # allowed to lag - but it is the reason --expand exists, so say it.
    registered = {e["theme"] for e in lexicon["entries"] if e.get("theme")}
    for tid in sorted(set(themes) - registered):
        warnings.append("theme %r has no lexicon entry" % tid)

    if not quiet:
        print("%d entries, %d renderings, %d attested against the corpus"
              % (len(lexicon["entries"]),
                 sum(len(e["renderings"]) for e in lexicon["entries"]),
                 checked))
    return errors, warnings


# ------------------------------------------------------------------ expand


def expand(lexicon, args):
    """Diff the lexicon's terms for a theme against themes.json.

    Both directions matter. A term the lexicon has and the theme lacks is
    a commentary the theme's searches are currently missing. A search term
    with no entry behind it is a term nobody has accounted for - it may be
    a good one, and it may be a relic that fires twice in the whole corpus.
    """
    registry = lib.themes()
    theme_ids = [args.theme] if args.theme else sorted(registry)
    for tid in theme_ids:
        if tid not in registry:
            print("unknown theme %r; known: %s" % (tid, ", ".join(sorted(registry))))
            return 2
        theme = registry[tid]
        current = list(theme["search_terms"])
        current_lc = {t.lower() for t in current}

        proposed, seen = [], set()
        for e in lexicon["entries"]:
            if e.get("theme") != tid:
                continue
            for term in entry_terms(e):
                if term.lower() not in seen:
                    seen.add(term.lower())
                    proposed.append(term)

        missing = [t for t in proposed if t.lower() not in current_lc]
        orphan = [t for t in current if t.lower() not in seen]

        print("%s (%s) - %d search terms, %d from the lexicon\n"
              % (tid, theme["english"], len(current), len(proposed)))
        if missing:
            print("  missing from search_terms (%d):" % len(missing))
            for t in missing:
                print("      %s" % t)
        if orphan:
            print("  in search_terms with no lexicon entry (%d):" % len(orphan))
            for t in orphan:
                print("      %s" % t)
        if not missing and not orphan:
            print("  in step")

        if args.json:
            merged = current + missing
            print("\n  \"search_terms\": [")
            print("    " + ", ".join('"%s"' % t for t in merged))
            print("  ]")
        print()
    return 0


# ------------------------------------------------------------------ attest


def attest(lexicon, args):
    """Count each registered term against the corpus.

    A rendering with no hits is dead weight in a search term list, and
    worse than that in an `absent_terms` list, where it makes an absence
    look checked when nothing was checked. A form with no hits usually
    means the corpus renders that term into English everywhere and never
    glosses it - which is exactly the hole gap-004 names.
    """
    corpus = lib.load_corpus()
    docs = [d for d in corpus["documents"]
            if not args.commentary or d["slug"] == args.commentary]
    entries = select(lexicon, args)
    if not entries:
        print("no entries match")
        return 0

    bodies = [(d, lib.normalized_document(d)) for d in docs]
    for e in entries:
        print("%s - %s" % (e["id"], e["headword"]))
        rows = ([("form", f) for f in e["forms"]]
                + [("rendering", r["english"]) for r in e["renderings"]])
        for kind, term in rows:
            needle = lib.normalize_quote(term)
            hits = ndocs = 0
            for _, body in bodies:
                n = term_hits(body, needle)
                hits += n
                ndocs += 1 if n else 0
            flag = "  <- not in the corpus" if not hits else ""
            print("  %-9s %-34s %6d hits  %2d docs%s"
                  % (kind, term[:34], hits, ndocs, flag))
        print()
    return 0


# -------------------------------------------------------------- candidates


def candidates(lexicon, args):
    """Unregistered headwords, ranked by how much corpus they touch.

    Theme selection is otherwise a matter of what someone thought of. This
    makes it a measurement: a headword with six thousand hits and no theme
    is a gap in the registry whether or not anyone finds it interesting.
    Density is not importance, and the ranking does not pretend otherwise -
    it only stops a term being missed for want of noticing.
    """
    corpus = lib.load_corpus()
    bodies = [(d, lib.normalized_document(d)) for d in corpus["documents"]]
    rows = []
    for e in select(lexicon, args):
        if e.get("theme"):
            continue
        terms = entry_terms(e)
        hits = ndocs = 0
        for _, body in bodies:
            n = lib.count_terms(body, terms)
            hits += n
            ndocs += 1 if n else 0
        rows.append((hits, ndocs, e))

    if not rows:
        print("every lexicon entry is registered to a theme")
        return 0

    rows.sort(key=lambda r: (-r[0], r[2]["id"]))
    print("%d headword(s) with no theme, by corpus density\n" % len(rows))
    for hits, ndocs, e in rows[:args.top]:
        print("%7d hits  %2d docs  %-16s %s"
              % (hits, ndocs, e["id"], ", ".join(entry_terms(e))[:60]))
    return 0


# -------------------------------------------------------------------- main


def parse_args(argv):
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true",
                      help="schema, references, and every attested rendering")
    mode.add_argument("--expand", action="store_true",
                      help="diff the lexicon's terms against themes.json")
    mode.add_argument("--attest", action="store_true",
                      help="count registered terms against the corpus")
    mode.add_argument("--candidates", action="store_true",
                      help="headwords with no theme, by corpus density")
    p.add_argument("--theme", help="restrict to one theme id")
    p.add_argument("--author", help="restrict to one author folder")
    p.add_argument("--entry", help="restrict to one lexicon entry id")
    p.add_argument("--commentary", help="--attest: count in one commentary only")
    p.add_argument("--json", action="store_true",
                   help="--expand: also print the merged search_terms array")
    p.add_argument("--top", type=int, default=25, help="rows to print (default 25)")
    p.add_argument("--quiet", action="store_true")
    return p.parse_args(argv[1:])


def main(argv):
    args = parse_args(argv)
    lexicon = load_lexicon()

    if args.expand:
        return expand(lexicon, args)
    if args.attest:
        return attest(lexicon, args)
    if args.candidates:
        return candidates(lexicon, args)

    errors, warnings = check(lexicon, args.quiet)
    for w in warnings:
        print("warning: %s" % w)
    for e in errors:
        print("error:   %s" % e)
    if errors:
        print("\nFAILED: %d error(s), %d warning(s)" % (len(errors), len(warnings)))
        return 1
    if not args.quiet:
        print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
