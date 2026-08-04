#!/usr/bin/env python3
"""Find the sections worth extracting from, without a model.

The corpus is 1.3 million words. No extraction pass should begin by
reading all of it, and no synthesis prompt could hold it. This is the
retrieval layer: word-boundary term search over the indexed sections,
ranked, printed as locators an extraction pass can be pointed at.

    # which commentaries carry the theme at all
    python3 scripts/synthesis_query.py --theme sorge

    # the sections to actually read, in one commentary
    python3 scripts/synthesis_query.py --theme sorge \\
        --commentary heidegger-ga-19-platon-sophistes-commentary --sections

    # anything, without touching themes.json
    python3 scripts/synthesis_query.py --terms "Bekümmerung,affliction" --sections

Sections already covered by an extraction record are marked [done], so a
second pass over a commentary can skip them. That is what makes re-runs
incremental rather than repeated.
"""

import argparse
import sys

import synthesislib as lib


def parse_args(argv):
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--theme", help="theme id from synthesis/themes.json")
    p.add_argument("--terms", help="comma-separated terms, instead of --theme")
    p.add_argument("--commentary", help="restrict to one commentary slug")
    p.add_argument("--author", help="restrict to one author folder")
    p.add_argument("--sections", action="store_true",
                   help="list matching sections instead of commentary totals")
    p.add_argument("--top", type=int, default=25, help="rows to print (default 25)")
    p.add_argument("--min-hits", type=int, default=1)
    p.add_argument("--urls", action="store_true", help="print published URLs")
    return p.parse_args(argv[1:])


def main(argv):
    args = parse_args(argv)
    registry = lib.themes()

    if args.terms:
        terms = [t.strip() for t in args.terms.split(",") if t.strip()]
        label = args.terms
    elif args.theme:
        if args.theme not in registry:
            print("unknown theme %r; known: %s"
                  % (args.theme, ", ".join(sorted(registry))))
            return 2
        terms = registry[args.theme]["search_terms"]
        label = "%s (%s)" % (args.theme, registry[args.theme]["english"])
    else:
        print("give --theme or --terms")
        return 2

    covered = set()
    if args.theme:
        for _, rec in lib.load_extractions(args.theme):
            covered.update(u["locator"] for u in rec["units"])
            covered.update(a["locator"] for a in rec["absences"])

    corpus = lib.load_corpus()
    rows = []
    for doc in corpus["documents"]:
        if args.commentary and doc["slug"] != args.commentary:
            continue
        if args.author and doc["author"] != args.author:
            continue
        text = lib.read_text(lib.os.path.join(lib.REPO_ROOT, doc["path"])).split("\n")
        doc_hits = 0
        for sec in doc["sections"]:
            body = lib.normalize_quote(
                "\n".join(text[sec["line_start"] - 1:sec["line_end"]]))
            hits = lib.count_terms(body, terms)
            doc_hits += hits
            if args.sections and hits >= args.min_hits:
                rows.append((hits, doc, sec))
        if not args.sections and doc_hits >= args.min_hits:
            rows.append((doc_hits, doc, None))

    rows.sort(key=lambda r: (-r[0], r[1]["slug"]))
    print("%s - %d %s with hits\n"
          % (label, len(rows), "sections" if args.sections else "commentaries"))

    for hits, doc, sec in rows[:args.top]:
        if sec is None:
            print("%5d  %-6s %s" % (hits, doc["author"], doc["slug"]))
            continue
        locator = "%s#%s" % (doc["slug"], sec["id"])
        mark = "[done] " if locator in covered else ""
        print("%5d  %s%s" % (hits, mark, locator))
        print("       %s  (lines %d-%d, %d words)"
              % (" > ".join(sec["path"][-2:]), sec["line_start"],
                 sec["line_end"], sec["words"]))
        if args.urls:
            print("       %s" % lib.section_url(doc, sec))

    if len(rows) > args.top:
        print("\n... %d more (use --top)" % (len(rows) - args.top))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
