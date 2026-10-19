#!/usr/bin/env python3
"""Regenerate synthesis/STATUS.md - the queue for the next pass.

The pipeline is only worth building if it tells you what to do next.
This is that report: what has been extracted, what has gone stale under
an edited commentary, which commentaries carry a theme but have never
been scanned, which dates are still unresolved, and which gaps the last
synthesis pass flagged.

    python3 scripts/synthesis_status.py [--check]

Like the ledgers, the output carries no timestamp, so an unchanged
corpus rebuilds to an unchanged file.
"""

import argparse
import os
import sys

import comparative_candidates as cc
import synthesislib as lib

STATUS_PATH = os.path.join(lib.SYNTHESIS_DIR, "STATUS.md")
CANDIDATES = 6
PAIRS = 10
UNSERVED = 10


def theme_section(theme, meta, corpus, chron, out):
    records = {rec["commentary"]: (rel, rec)
               for rel, rec in lib.load_extractions(theme)}
    cmap = lib.corpus_map(corpus)

    units = sum(len(r["units"]) for _, r in records.values())
    absences = sum(len(r["absences"]) for _, r in records.values())
    stale = [slug for slug, (_, r) in records.items()
             if cmap[slug]["sha256"] != r["source_sha256"]]
    partial = [slug for slug, (_, r) in records.items() if r["coverage"] == "partial"]

    out.append("### %s - %s" % (theme, meta["english"]))
    out.append("")
    out.append("%d commentar%s extracted · %d units · %d absences%s%s"
               % (len(records), "y" if len(records) == 1 else "ies",
                  units, absences,
                  " · %d stale" % len(stale) if stale else "",
                  " · %d partial" % len(partial) if partial else ""))
    out.append("")

    scored = []
    for doc in corpus["documents"]:
        entry = chron.get(doc["slug"])
        if entry and entry["role"] == "output":
            continue
        if doc["slug"] in records:
            continue
        hits = lib.count_terms(lib.normalized_document(doc), meta["search_terms"])
        if hits:
            scored.append((hits, doc["slug"], lib.entry_year(entry) if entry else lib.UNDATED))
    scored.sort(key=lambda r: -r[0])

    if scored:
        out.append("Next candidates, by term density:")
        out.append("")
        for hits, slug, year in scored[:CANDIDATES]:
            when = "undated" if year == lib.UNDATED else str(year)
            out.append("- [ ] `%s` (%s) - %d hits" % (slug, when, hits))
        if len(scored) > CANDIDATES:
            out.append("- ... %d more; see `synthesis_query.py --theme %s`"
                       % (len(scored) - CANDIDATES, theme))
        out.append("")
    elif records:
        out.append("Every commentary carrying these terms has a record.")
        out.append("")
    return stale


def readiness_section(corpus, chron, out):
    """What the comparative-commentary skill needs, and what is missing. Built from this
    repo alone so that CI and a laptop write the same file: work links live in
    faultynode/indexes and primary texts in faultynode/sources, both private."""
    ctx = cc.context(corpus, chron)
    out += ["## Comparative readiness", "",
            "A comparative pair (the reading text R takes up the read text P) needs an "
            "inheritance record for R that names P, a commentary on each side, and a date "
            "for each. Whether a commentary is linked to its work "
            "(`scripts/link_commentaries.py` in faultynode/indexes) and whether its "
            "primary text is in faultynode/sources are not assessed here: both repos are "
            "private. `scripts/comparative_candidates.py` adds the source check on a "
            "machine that has them.", ""]

    out += ["### Runs", ""]
    run_files = cc.runs()
    for r in run_files:
        progress = r["progress"] or "no Progress line"
        if len(progress) > 200:
            progress = progress[:199].rstrip() + "…"
        out.append("- `%s` - `%s` reads `%s`. %s" % (r["file"], r["R"], r["P"], progress))
    out.append("" if run_files else "No run files in `runs/`.")
    if not run_files:
        out.append("")

    with_record = {rec["commentary"] for rec in ctx["records"]}
    unread = [d["slug"] for d in corpus["documents"]
              if chron.get(d["slug"], {}).get("role") == "reception" and d["slug"] not in with_record]
    out += ["### Reading texts with no inheritance record", ""]
    if unread:
        out += ["Reception commentaries are reading texts by definition. Each needs a "
                "Stage 3 pass (`synthesis/prompts/inheritance-prompt.md`) before it can "
                "be paired.", ""]
        for slug in sorted(unread):
            year = lib.entry_year(chron[slug])
            out.append("- [ ] `%s` (%s)" % (slug, "undated" if year == lib.UNDATED else year))
    else:
        out.append("Every reception commentary has an inheritance record.")
    out.append("")

    missing = sorted(d["slug"] for d in corpus["documents"] if d["slug"] not in chron)
    out += ["### Not in chronology.json", ""]
    if missing:
        out += ["With no entry, a commentary's role (primary or reception) is unrecorded, "
                "so it cannot be told apart as R or P, and a pair with it cannot be "
                "dated.", ""]
        out += ["- [ ] `%s`" % slug for slug in missing]
    else:
        out.append("Every commentary has an entry.")
    out.append("")

    engagements = [e for rec in ctx["records"] for e in rec.get("engagements", [])]
    named = sum(1 for e in engagements if e["predecessor"].get("text"))
    out += ["### What the records name", "",
            "%d records · %d engagements · %d (%d%%) name the predecessor's text. An "
            "engagement that names only an author can suggest a pair at author level, "
            "never a particular P."
            % (len(ctx["records"]), len(engagements), named,
               round(100 * named / len(engagements)) if engagements else 0), ""]
    unserved = cc.unserved_texts(ctx)
    if unserved:
        out += ["Named texts that no commentary's title matches: the P side of a pair "
                "that cannot be run yet, or a title the corpus gives in another language "
                "(*Ideen I* against *Ideas I*), which only a work link can resolve.", ""]
        for g in unserved[:UNSERVED]:
            readers = ", ".join("`%s`" % r for r in g["readers"][:3])
            if len(g["readers"]) > 3:
                readers += " and %d more" % (len(g["readers"]) - 3)
            out.append("- %s, *%s* - %d engagement%s, in %s"
                       % (g["author"].title(), g["text"], g["engagements"],
                          "" if g["engagements"] == 1 else "s", readers))
        if len(unserved) > UNSERVED:
            out.append("- ... %d more" % (len(unserved) - UNSERVED))
        out.append("")

    itemized, unrecorded = cc.unsearched_names(ctx)
    out += ["### Partial records: names not yet searched", ""]
    if itemized:
        out += ["Corpus authors each partial record could engage, by date, but has neither "
                "engaged nor listed in `predecessors_queried`. A name searched without "
                "result is not listed: that absence is already a finding.", ""]
        for slug, missing in itemized:
            out.append("- [ ] `%s` - %s" % (slug, ", ".join(missing) if missing
                                             else "every corpus author searched or engaged"))
        out.append("")
    if unrecorded:
        out += ["%d partial record%s do not record which names they searched, so what "
                "they owe cannot be told: %s." % (len(unrecorded), "" if len(unrecorded) == 1 else "s",
                                                  ", ".join("`%s`" % s for s in unrecorded)), ""]

    rows = [r for r in cc.candidate_rows(ctx, check_sources=False) if not r["done"]]
    out += ["### Candidate pairs", ""]
    if rows:
        out += ["Ranked by `scripts/comparative_candidates.py`: engagements weighted by "
                "mode (destructive and silent appropriation 3, polemical rejection 2.5, "
                "acknowledged debt 2, terminological borrowing 1), plus 4 for each named "
                "text that matches P, discounted where the record names only the author "
                "and the corpus holds several of their commentaries. Pairs with a run "
                "file are left out. Check the sources before starting one.", ""]
        for r in rows[:PAIRS]:
            modes = ", ".join("%d %s" % (n, m) for m, n in
                              sorted(r["modes"].items(), key=lambda kv: (-kv[1], kv[0])))
            texts = list(dict.fromkeys(r["text_match"]))
            notes = [n for n in r["notes"] if n != "partial record"]
            if texts:
                notes.insert(0, "names " + "; ".join("*%s*" % t for t in texts))
            if r["loci"]:
                notes.insert(1 if texts else 0, "P-loci " + ", ".join(r["loci"]))
            out.append("- [ ] `%s` reads `%s` - score %s · %d engagement%s (%s)%s"
                       % (r["R"], r["P"], r["score"], r["engagements"],
                          "" if r["engagements"] == 1 else "s", modes,
                          " · " + " · ".join(notes) if notes else ""))
        if len(rows) > PAIRS:
            out.append("- ... %d more; see `comparative_candidates.py --all`" % (len(rows) - PAIRS))
    else:
        out.append("No inheritance record names a predecessor with a commentary here.")
    out.append("")


def main(argv):
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--check", action="store_true")
    args = p.parse_args(argv[1:])

    corpus = lib.load_corpus()
    chron = lib.chronology()
    registry = lib.themes()

    docs = corpus["documents"]
    out = ["# Synthesis status", "",
           "*Generated by `scripts/synthesis_status.py`. Do not edit by hand.*", "",
           "Corpus: **%d commentaries**, %s words, %d sections indexed in "
           "`synthesis/corpus.json`."
           % (len(docs), format(sum(d["words"] for d in docs), ","),
              sum(len(d["sections"]) for d in docs)),
           ""]

    out += ["## Themes", ""]
    all_stale = []
    for theme in sorted(registry):
        all_stale += [(theme, slug) for slug in
                      theme_section(theme, registry[theme], corpus, chron, out)]

    inh = lib.load_inheritance()
    cmap = lib.corpus_map(corpus)
    out += ["## Inheritance index", ""]
    if inh:
        out.append("%d commentar%s · %d engagements"
                   % (len(inh), "y" if len(inh) == 1 else "ies",
                      sum(len(r["engagements"]) for _, r in inh)))
        out.append("")
        for rel, rec in inh:
            marks = []
            if cmap[rec["commentary"]]["sha256"] != rec["source_sha256"]:
                marks.append("stale")
            if rec["coverage"] == "partial":
                marks.append("partial")
            out.append("- `%s` - %d engagements%s"
                       % (rec["commentary"], len(rec["engagements"]),
                          " (%s)" % ", ".join(marks) if marks else ""))
        out.append("")
    else:
        out += ["No inheritance records yet. Stage 3 is a separate pass over the "
                "same commentaries; see "
                "synthesis/prompts/inheritance-prompt.md.", ""]

    if all_stale:
        out += ["## Stale records", "",
                "The commentary changed after the pass ran. Quotes are no longer "
                "guaranteed; re-extract and update `source_sha256`.", ""]
        for theme, slug in all_stale:
            out.append("- [ ] `synthesis/extractions/%s/%s.json`" % (theme, slug))
        out.append("")

    unresolved = [e for e in chron.values() if e["status"] == "unresolved"
                  and e["role"] != "output"]
    out += ["## Chronology to resolve", ""]
    if unresolved:
        out += ["These commentaries do not date their own text, so they sit off "
                "the ledger spine. Each is a reading task, not a lookup: the date "
                "belongs in the commentary first.", ""]
        for e in sorted(unresolved, key=lambda e: e["commentary"]):
            out.append("- [ ] `%s`%s" % (e["commentary"],
                                         " - " + e["note"] if e.get("note") else ""))
        out.append("")
    else:
        out += ["Every commentary states a date for its text.", ""]

    readiness_section(corpus, chron, out)

    gaps = (lib.registry("gaps") or {"gaps": []})["gaps"]
    open_gaps = [g for g in gaps if g["status"] != "closed"]
    out += ["## Open gaps", ""]
    if open_gaps:
        out += ["Flagged by a synthesis pass as unsupported by the ledgers. This "
                "is the reading queue.", ""]
        for g in sorted(open_gaps, key=lambda g: g["id"]):
            out.append("- [ ] **%s** (%s%s) %s"
                       % (g["id"], g["status"],
                          ", " + g["theme"] if g.get("theme") else "", g["question"]))
            out.append("      *Needs:* %s" % g["needs"])
        out.append("")
    else:
        out += ["None recorded. A synthesis pass that flags no gaps has either "
                "exhausted its question or failed to look.", ""]

    text = "\n".join(out)
    rel = os.path.relpath(STATUS_PATH, lib.REPO_ROOT).replace(os.sep, "/")
    if args.check:
        current = lib.read_text(STATUS_PATH) if os.path.exists(STATUS_PATH) else None
        if current != text:
            print("%s is out of date - run python3 scripts/synthesis_status.py" % rel)
            return 1
        print("%s is up to date" % rel)
        return 0

    lib.write_text(STATUS_PATH, text)
    print("wrote %s" % rel)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
