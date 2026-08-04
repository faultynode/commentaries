#!/usr/bin/env python3
"""Validate every synthesis record against the corpus it claims to quote.

This is the part that makes the pipeline worth having. An extraction
record is a set of claims about what a commentary says at a named place;
each claim carries a verbatim quote; this script checks that the quote is
there. A claim that cannot be checked is not evidence, and CI refuses it.

Checks, in order of how much they matter:

  quote      Every unit's quote appears, verbatim, inside the section its
             locator names. Normalization covers smart quotes, dashes,
             emphasis marks and line wrapping - not wording.
  absence    Every claimed absence is re-checked: if the term is in fact
             present in that section, the absence is a false negative and
             fails. Absences periodize, so they get the same rigour.
  locator    Slug and section id resolve against synthesis/corpus.json.
  schema     Records conform to synthesis/schema/*.json.
  registry   Themes, strata and chronology entries referenced exist.
  staleness  The commentary's digest still matches the one the pass read.

Staleness is a warning, not an error, and it downgrades quote failures on
the same record to warnings: when a commentary has been edited under a
record, the right report is "re-extract this", not "you lied about a
quote". Everything else stays an error.

    python3 scripts/synthesis_validate.py [--strict] [--quiet]

--strict promotes warnings to errors (used on pull requests, not on the
push that edits a commentary).
"""

import os
import re
import sys

import synthesislib as lib

SCHEMA_DIR = os.path.join(lib.SYNTHESIS_DIR, "schema")
EXTRACTIONS_DIR = os.path.join(lib.SYNTHESIS_DIR, "extractions")
INHERITANCE_DIR = os.path.join(lib.SYNTHESIS_DIR, "inheritance")


class Report:
    def __init__(self):
        self.errors = []
        self.warnings = []

    def error(self, where, msg):
        self.errors.append("%s: %s" % (where, msg))

    def warn(self, where, msg):
        self.warnings.append("%s: %s" % (where, msg))


def term_present(text, term):
    return re.search(r"(?<!\w)%s" % re.escape(term.lower()), text) is not None


def iter_records(root, suffix=".json"):
    for dirpath, _, names in os.walk(root):
        for name in sorted(names):
            if name.endswith(suffix):
                yield os.path.join(dirpath, name)


def check_registries(rep, corpus, schemas):
    reg = schemas["registry"]["$defs"]
    out = {}

    for name, key in (("themes", "themes"), ("chronology", "chronology"),
                      ("gaps", "gaps")):
        path = os.path.join(lib.SYNTHESIS_DIR, name + ".json")
        if not os.path.exists(path):
            out[name] = None
            continue
        data = lib.load_json(path)
        for err in lib.check_schema(data, reg[key], schemas["registry"]):
            rep.error(name + ".json", err)
        out[name] = data

    slugs = set(lib.corpus_map(corpus))

    themes = out.get("themes")
    if themes:
        seen = set()
        for t in themes["themes"]:
            if t["id"] in seen:
                rep.error("themes.json", "duplicate theme id %r" % t["id"])
            seen.add(t["id"])

    chron = out.get("chronology")
    if chron:
        covered, strata = set(), set()
        for e in chron["entries"]:
            if e["commentary"] not in slugs:
                rep.error("chronology.json",
                          "%s is not a commentary in the corpus" % e["commentary"])
            covered.add(e["commentary"])
            for s in e["strata"]:
                if s["id"] in strata:
                    rep.error("chronology.json", "duplicate stratum id %r" % s["id"])
                strata.add(s["id"])
                if not s["stated_in_commentary"] and not s.get("evidence"):
                    rep.error("chronology.json",
                              "stratum %r is not stated in the commentary and "
                              "gives no evidence for its date" % s["id"])
            resolved = any(s["year_start"] is not None for s in e["strata"])
            if e["status"] == "resolved" and not resolved:
                rep.error("chronology.json",
                          "%s is marked resolved with no dated stratum" % e["commentary"])
            if e["status"] == "unresolved" and resolved:
                rep.error("chronology.json",
                          "%s is marked unresolved but has a dated stratum"
                          % e["commentary"])
        for missing in sorted(slugs - covered):
            rep.warn("chronology.json",
                     "no entry for %s - it cannot appear on any ledger" % missing)

    gaps = out.get("gaps")
    if gaps:
        for g in gaps["gaps"]:
            src = g.get("raised_by")
            if src and not os.path.exists(os.path.join(lib.REPO_ROOT, src)):
                rep.warn("gaps.json", "%s: raised_by path %s does not exist"
                         % (g["id"], src))
    return out


def resolve(rep, where, locator, expected_slug, cmap):
    """Locator -> (doc, section), or None with the failure reported."""
    try:
        slug, sec_id = lib.parse_locator(locator)
    except ValueError as exc:
        rep.error(where, "%s (%s)" % (exc, locator))
        return None
    if expected_slug and slug != expected_slug:
        rep.error(where, "locator points at %s but the record is about %s"
                  % (slug, expected_slug))
        return None
    doc = cmap.get(slug)
    if doc is None:
        rep.error(where, "unknown commentary %r" % slug)
        return None
    sec = lib.section_map(doc).get(sec_id)
    if sec is None:
        rep.error(where, "no section %r in %s" % (sec_id, slug))
        return None
    return doc, sec


def check_quote(rep, where, quote, doc, sec, stale):
    body = lib.normalize_quote(lib.section_text(doc, sec))
    if lib.normalize_quote(quote) in body:
        return True
    msg = ("quote not found in %s#%s (lines %d-%d)"
           % (doc["slug"], sec["id"], sec["line_start"], sec["line_end"]))
    if stale:
        rep.warn(where, msg + " - record is stale, re-extract")
    else:
        rep.error(where, msg)
    return False


def check_extractions(rep, corpus, schemas, registries):
    cmap = lib.corpus_map(corpus)
    themes = {t["id"]: t for t in (registries.get("themes") or {"themes": []})["themes"]}
    strata = {s["id"]
              for e in (registries.get("chronology") or {"entries": []})["entries"]
              for s in e["strata"]}
    seen_ids = {}
    counts = {"records": 0, "units": 0, "absences": 0, "stale": 0}

    for path in iter_records(EXTRACTIONS_DIR):
        rel = os.path.relpath(path, lib.REPO_ROOT).replace(os.sep, "/")
        rec = lib.load_json(path)
        errs = lib.check_schema(rec, schemas["extraction"])
        for err in errs:
            rep.error(rel, err)
        if errs:
            continue
        counts["records"] += 1

        if rec["theme"] not in themes:
            rep.error(rel, "theme %r is not in themes.json" % rec["theme"])
        if os.path.basename(os.path.dirname(path)) != rec["theme"]:
            rep.error(rel, "file sits under a directory that is not its theme")
        if os.path.splitext(os.path.basename(path))[0] != rec["commentary"]:
            rep.error(rel, "filename does not match the commentary slug")

        doc = cmap.get(rec["commentary"])
        if doc is None:
            rep.error(rel, "unknown commentary %r" % rec["commentary"])
            continue

        stale = doc["sha256"] != rec["source_sha256"]
        if stale:
            counts["stale"] += 1
            rep.warn(rel, "stale: %s has changed since this pass "
                          "(recorded %s, now %s)"
                     % (rec["commentary"], rec["source_sha256"][:12],
                        doc["sha256"][:12]))
        if rec["coverage"] == "partial" and not rec.get("coverage_note"):
            rep.error(rel, "partial coverage must say what it covered")

        for unit in rec["units"]:
            counts["units"] += 1
            where = "%s [%s]" % (rel, unit["id"])
            if unit["id"] in seen_ids:
                rep.error(where, "duplicate unit id, also in %s" % seen_ids[unit["id"]])
            seen_ids[unit["id"]] = rel
            if not unit["id"].startswith(rec["theme"] + "/"):
                rep.error(where, "unit id must begin with the theme id")
            if unit.get("stratum") and unit["stratum"] not in strata:
                rep.error(where, "unknown stratum %r" % unit["stratum"])
            found = resolve(rep, where, unit["locator"], rec["commentary"], cmap)
            if found:
                check_quote(rep, where, unit["quote"], found[0], found[1], stale)

        theme_terms = themes.get(rec["theme"], {}).get("search_terms", [])
        for i, absence in enumerate(rec["absences"]):
            counts["absences"] += 1
            where = "%s [absence %d]" % (rel, i)
            found = resolve(rep, where, absence["locator"], rec["commentary"], cmap)
            if not found:
                continue
            doc_a, sec = found
            body = lib.normalize_quote(lib.section_text(doc_a, sec))
            for term in absence.get("absent_terms") or theme_terms:
                if term_present(body, lib.normalize_quote(term)):
                    msg = ("claims %r is absent from %s#%s, but it occurs there"
                           % (term, doc_a["slug"], sec["id"]))
                    if stale:
                        rep.warn(where, msg + " - record is stale")
                    else:
                        rep.error(where, msg)
    return counts


def check_inheritance(rep, corpus, schemas):
    cmap = lib.corpus_map(corpus)
    seen_ids = {}
    counts = {"records": 0, "engagements": 0, "stale": 0}

    for path in iter_records(INHERITANCE_DIR):
        rel = os.path.relpath(path, lib.REPO_ROOT).replace(os.sep, "/")
        rec = lib.load_json(path)
        errs = lib.check_schema(rec, schemas["inheritance"])
        for err in errs:
            rep.error(rel, err)
        if errs:
            continue
        counts["records"] += 1

        if os.path.splitext(os.path.basename(path))[0] != rec["commentary"]:
            rep.error(rel, "filename does not match the commentary slug")
        doc = cmap.get(rec["commentary"])
        if doc is None:
            rep.error(rel, "unknown commentary %r" % rec["commentary"])
            continue
        stale = doc["sha256"] != rec["source_sha256"]
        if stale:
            counts["stale"] += 1
            rep.warn(rel, "stale: %s has changed since this pass" % rec["commentary"])

        for eng in rec["engagements"]:
            counts["engagements"] += 1
            where = "%s [%s]" % (rel, eng["id"])
            if eng["id"] in seen_ids:
                rep.error(where, "duplicate engagement id, also in %s"
                          % seen_ids[eng["id"]])
            seen_ids[eng["id"]] = rel
            found = resolve(rep, where, eng["locator"], rec["commentary"], cmap)
            if found:
                check_quote(rep, where, eng["quote"], found[0], found[1], stale)
    return counts


def main(argv):
    strict = "--strict" in argv[1:]
    quiet = "--quiet" in argv[1:]
    rep = Report()

    schemas = {
        "extraction": lib.load_json(os.path.join(SCHEMA_DIR, "extraction.schema.json")),
        "inheritance": lib.load_json(os.path.join(SCHEMA_DIR, "inheritance.schema.json")),
        "registry": lib.load_json(os.path.join(SCHEMA_DIR, "registry.schema.json")),
    }

    # Validate against the corpus as it is now, not as it was last indexed:
    # a pull request that edits a commentary must be checked against the
    # edited text. A stale index on disk is worth saying, but it is a
    # bookkeeping problem, not a reason to reject the records.
    corpus = lib.build_corpus()
    try:
        if lib.load_corpus() != corpus:
            rep.warn("synthesis/corpus.json",
                     "out of date - run python3 scripts/synthesis_index.py")
    except SystemExit:
        rep.warn("synthesis/corpus.json", "missing - run scripts/synthesis_index.py")

    registries = check_registries(rep, corpus, schemas)
    ex = check_extractions(rep, corpus, schemas, registries)
    inh = check_inheritance(rep, corpus, schemas)

    if not quiet:
        print("checked %d extraction records (%d units, %d absences) "
              "and %d inheritance records (%d engagements)"
              % (ex["records"], ex["units"], ex["absences"],
                 inh["records"], inh["engagements"]))
        stale = ex["stale"] + inh["stale"]
        if stale:
            print("%d record(s) stale - see synthesis/STATUS.md" % stale)

    for w in rep.warnings:
        print("warning: %s" % w)
    for e in rep.errors:
        print("error:   %s" % e)

    failed = bool(rep.errors) or (strict and bool(rep.warnings))
    if failed:
        print("\nFAILED: %d error(s), %d warning(s)"
              % (len(rep.errors), len(rep.warnings)))
    elif not quiet:
        print("OK")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
