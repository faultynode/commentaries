#!/usr/bin/env python3
"""Rank candidate (R, P) pairs for paragraph-by-paragraph comparative commentaries.

R (reading text) is any commentary with an inheritance record; P (read text) is any
commentary on a work by a predecessor named in that record. Joins:

  synthesis/inheritance/*.json  who R engages, in what mode, with how many engagements
  synthesis/corpus.json         which commentaries exist, and whose work each treats
  synthesis/chronology.json     whether R could have known P
  runs/*.md                     pairs already done or under way
  ../sources/sources/<author>/  whether a primary text is on disk for R and P

The inheritance records are partial and name an author far more often than a text, so
the output is a shortlist to check by hand, not a verdict. Pairs are scored from the
engagement count, the weight of the mode, and a bonus when a named text matches P.

    python3 scripts/comparative_candidates.py              # top 25
    python3 scripts/comparative_candidates.py --r henry    # only R's whose slug contains 'henry'
    python3 scripts/comparative_candidates.py --p heidegger --top 50
    python3 scripts/comparative_candidates.py --all --json

synthesis_status.py imports context(), candidate_rows(check_sources=False),
unserved_texts() and runs() for the "Comparative readiness" section of STATUS.md. CI
has no sources checkout, so STATUS.md never shows the source columns.
"""
import argparse
import glob
import json
import os
import re
import sys
import unicodedata
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCES = os.path.normpath(os.path.join(ROOT, "..", "sources", "sources"))

# What each mode adds to a pair's score: the typology is richest where R appropriates
# or rejects, thinnest where R only borrows a term.
MODE_WEIGHT = {
    "destructive-appropriation": 3.0,
    "silent-appropriation": 3.0,
    "polemical-rejection": 2.5,
    "acknowledged-debt": 2.0,
    "terminological-borrowing": 1.0,
}
# Predecessor spellings that do not reduce to the commentary folder name.
AUTHOR_ALIAS = {}
STOP = {"the", "of", "und", "der", "die", "das", "und", "zur", "zum", "von", "de", "la",
        "le", "des", "du", "et", "on", "to", "and", "a", "an", "in", "zu", "uber", "ueber"}


def fold(s):
    s = unicodedata.normalize("NFKD", s)
    return "".join(c for c in s if not unicodedata.combining(c)).lower()


def last_name(author):
    """'Edmund Husserl' -> 'husserl'; 'Fink, Eugen' -> 'fink'; 'Heidegger' -> 'heidegger'."""
    a = fold(author)
    if "," in a:
        a = a.split(",")[0]
    elif ";" in a:
        a = a.split(";")[0]
    parts = re.sub(r"[^a-z\s-]", " ", a).split()
    return AUTHOR_ALIAS.get(parts[-1], parts[-1]) if parts else ""


def load_json(*path):
    with open(os.path.join(ROOT, *path), encoding="utf-8") as f:
        return json.load(f)


def tokens(s):
    return {t for t in re.findall(r"[a-z0-9]+", fold(s)) if t not in STOP and len(t) > 2}


def work_key(slug):
    """'heidegger-ga-3-kant-...' -> ('ga','3'); 'husserliana-4-ideas-ii-...' -> ('hua','4')."""
    m = re.search(r"(?:^|-)ga-(\d+)", slug)
    if m:
        return ("ga", m.group(1))
    m = re.search(r"husserliana-(\d+)", slug)
    if m:
        return ("hua", m.group(1))
    return None


def source_status(author_folder, slug):
    """Cheap check that a primary text is on disk. 'yes' = a file carrying the work's
    volume number; 'author' = the author has files but none matched; 'no' = none."""
    d = os.path.join(SOURCES, author_folder)
    if not os.path.isdir(d):
        return "no"
    files = [fold(f) for f in os.listdir(d)]
    if not files:
        return "no"
    key = work_key(slug)
    if key:
        kind, n = key
        pats = {"ga": [rf"ga-{n}-", rf"ga{n}-", rf"gesamtausgabe-{n}-"],
                "hua": [rf"hua-?{n}-", rf"husserliana-{n}-", rf"cw{n}-"]}[kind]
        if any(re.search(p, f) for f in files for p in pats):
            return "yes"
        return "author"
    # No volume key: match on distinctive slug words (not the author, not 'commentary')
    words = tokens(slug) - {author_folder, "commentary"}
    for f in files:
        if len(words & tokens(f)) >= 2:
            return "yes"
    return "author"


def runs():
    """Every runs/*.md with its R, P and the first line of its Progress section."""
    out = []
    for f in sorted(glob.glob(os.path.join(ROOT, "runs", "*.md"))):
        with open(f, encoding="utf-8") as fh:
            txt = fh.read()
        r = re.search(r"Commentary R[^:]*:\s*\S*?([\w.-]+?)\.md", txt)
        p = re.search(r"Commentary P[^:]*:\s*\S*?([\w.-]+?)\.md", txt)
        progress = re.search(r"(?m)^## Progress[ \t]*\r?\n(.+)", txt)
        out.append({"file": "runs/" + os.path.basename(f),
                    "R": r.group(1) if r else None, "P": p.group(1) if p else None,
                    "progress": progress.group(1).strip() if progress else None})
    return out


def context(corpus=None, chronology=None):
    """Everything the rankings read. synthesis_status.py passes what it has loaded:
    the corpus as corpus.json holds it, the chronology as {slug: entry}."""
    corpus = corpus or load_json("synthesis", "corpus.json")
    if chronology is None:
        chronology = {e["commentary"]: e for e in load_json("synthesis", "chronology.json")["entries"]}
    docs = {d["slug"]: d for d in corpus["documents"]}
    by_author = defaultdict(list)
    for slug, d in docs.items():
        by_author[AUTHOR_ALIAS.get(d["author"], d["author"])].append(slug)
    records = [load_json("synthesis", "inheritance", os.path.basename(path))
               for path in sorted(glob.glob(os.path.join(ROOT, "synthesis", "inheritance", "*.json")))]
    return {"docs": docs, "chron": chronology, "by_author": by_author, "records": records}


def years(ctx, slug):
    strata = ctx["chron"].get(slug, {}).get("strata", [])
    ys = [s["year_start"] for s in strata if s.get("year_start")]
    ye = [s.get("year_end") or s["year_start"] for s in strata if s.get("year_start")]
    return (min(ys), max(ye)) if ys else (None, None)


def text_hits(ctx, pred, named, exclude=None):
    """{P slug: [named texts it matches]} over the predecessor's commentaries."""
    docs = ctx["docs"]
    return {p: [t for t in named if tokens(t) & (tokens(p) | tokens(docs[p]["title"])) - {pred}]
            for p in ctx["by_author"].get(pred, []) if p != exclude}


def candidate_rows(ctx, check_sources=True):
    """Every (R, P) pair the records support, scored and sorted. Without check_sources
    the rows depend on this repo alone, which is what STATUS.md needs."""
    docs = ctx["docs"]
    done = {(r["R"], r["P"]): r["file"] for r in runs()}
    rows = []
    for rec in ctx["records"]:
        r_slug = rec["commentary"]
        r_author = docs.get(r_slug, {}).get("author", "")
        groups = defaultdict(list)
        for e in rec.get("engagements", []):
            groups[last_name(e["predecessor"]["author"])].append(e)
        for pred, engs in groups.items():
            named = [e["predecessor"]["text"] for e in engs if e["predecessor"].get("text")]
            hits = text_hits(ctx, pred, named, exclude=r_slug)
            cands = list(hits)
            # If R names a text that one of this author's commentaries treats, the author's
            # other commentaries are noise for this group; otherwise keep them, discounted.
            if any(hits.values()):
                cands = [p for p in cands if hits[p]]
            for p_slug in cands:
                matched = hits[p_slug]
                modes = Counter(e["mode"] for e in engs)
                score = sum(MODE_WEIGHT.get(m, 1.0) * n for m, n in modes.items())
                score += 4 * len(matched)  # a named text that matches P is the strongest signal
                # Several P's by one author: only the text-matched ones deserve the full score
                n_p = len(ctx["by_author"][pred])
                author_level = n_p > 1 and not matched
                if author_level:
                    score /= n_p ** 0.5
                r0, r1 = years(ctx, r_slug)
                p0, p1 = years(ctx, p_slug)
                note = []
                if r1 and p0 and p0 > r1:
                    note.append("P dated after R")
                if author_level:
                    note.append("author-level only")
                if rec.get("coverage") == "partial":
                    note.append("partial record")
                row = {
                    "score": round(score, 1), "R": r_slug, "P": p_slug,
                    "engagements": len(engs), "modes": dict(sorted(modes.items())),
                    "text_match": matched, "R_years": [r0, r1], "P_years": [p0, p1],
                    "done": done.get((r_slug, p_slug)), "notes": note,
                }
                if check_sources:
                    row["source_P"] = source_status(pred, p_slug)
                    row["source_R"] = source_status(AUTHOR_ALIAS.get(r_author, r_author),
                                                    r_slug) if r_author else "no"
                rows.append(row)
    rows.sort(key=lambda r: (-r["score"], r["R"], r["P"]))
    return rows


def unserved_texts(ctx):
    """Predecessor texts the records name that no commentary in the corpus treats: the
    P side of a pair that cannot be run yet. Variants of one title are merged when one
    title's words contain the other's ('Kritik der reinen Vernunft, Preface to the 2nd
    edition' joins 'Kritik der reinen Vernunft')."""
    groups = []  # [author, label, words, readers, engagements]
    for rec in ctx["records"]:
        for e in rec.get("engagements", []):
            text = e["predecessor"].get("text")
            pred = last_name(e["predecessor"]["author"])
            if not text or not tokens(text) or any(text_hits(ctx, pred, [text]).values()):
                continue
            words = tokens(text)
            g = next((g for g in groups if g[0] == pred and (words <= g[2] or g[2] <= words)), None)
            if g is None:
                groups.append([pred, text, words, {rec["commentary"]}, 1])
                continue
            if len(words) < len(g[2]):
                g[1], g[2] = text, words
            g[3].add(rec["commentary"])
            g[4] += 1
    out = [{"author": a, "text": t, "readers": sorted(r), "engagements": n}
           for a, t, _, r, n in groups]
    out.sort(key=lambda g: (-len(g["readers"]), -g["engagements"], g["author"], g["text"]))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--r", help="keep only R commentaries whose slug contains this")
    ap.add_argument("--p", help="keep only P commentaries whose slug contains this")
    ap.add_argument("--top", type=int, default=25)
    ap.add_argument("--all", action="store_true", help="no row limit")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--ready", action="store_true", help="only pairs whose P has a source file on disk")
    args = ap.parse_args()

    rows = [r for r in candidate_rows(context()) if not r["done"]]
    rows = [r for r in rows if (not args.r or args.r in r["R"]) and (not args.p or args.p in r["P"])]
    if args.ready:
        rows = [r for r in rows if r["source_P"] == "yes"]
    if not args.all:
        rows = rows[: args.top]

    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")
    if args.json:
        json.dump(rows, sys.stdout, ensure_ascii=False, indent=2)
        return
    short = lambda s, n: s if len(s) <= n else s[: n - 1] + "…"
    print(f"{'score':>5}  {'R':<44} {'P':<44} {'n':>2}  {'src P/R':<9} modes / notes")
    for r in rows:
        modes = ", ".join(f"{m.split('-')[0][:5]}{n}" for m, n in r["modes"].items())
        extra = "; ".join(r["notes"] + ([f"text: {', '.join(r['text_match'])}"] if r["text_match"] else []))
        print(f"{r['score']:>5}  {short(r['R'], 44):<44} {short(r['P'], 44):<44} {r['engagements']:>2}  "
              f"{r['source_P']}/{r['source_R']:<6} {modes}  {extra}")
    print(f"\n{len(rows)} rows. src: yes = source file found, author = author has files but none matched, no = none.")


if __name__ == "__main__":
    main()
