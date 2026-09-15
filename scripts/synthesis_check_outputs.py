#!/usr/bin/env python3
"""Check Stage 4 outputs against the ledgers and inheritance records.

`synthesis/outputs/*.md` is the one place in the pipeline
`synthesis_validate.py` does not reach: it validates extraction and
inheritance records against the commentaries, but nothing re-checks the
prose written from those records against the records themselves. This
script closes that gap, at the same grain - resolve every locator, look
up every quote - and nothing more. Whether an output's argument is sound
is still a review problem; whether its citations resolve and its quotes
are verbatim is not.

Checks:

  unit id     Every backticked `<theme>/<record>/<NNN>` (or bare
              `<record>/<NNN>`, resolved against the theme inferred from
              the output's filename) names a unit that is actually in
              that theme's ledger.
  inh id      Every backticked `inh/<record>/<NNN>` names an engagement
              that is actually in `synthesis/inheritance/`.
  absence     Every backticked `<slug>#<section-id>` whose slug is a real
              commentary is checked against the recorded absences across
              all extraction records - the convention this pipeline uses
              to cite a checked negative.
  quote       Every double-quoted span of some length is found, verbatim
              up to normalization, inside the ledger and inheritance text
              the output claims to be written from. An ellipsis in the
              quoted span is allowed to elide ledger text between two
              fragments that both must still appear, in order.

A filename that does not start with a registered theme id (as
`<theme>-<type>.md`) falls back to checking unit ids against every
ledger, which is more permissive, not less - only report bugs, do not
invent policy about naming that the pipeline itself does not enforce.

    python3 scripts/synthesis_check_outputs.py [path ...]

With no paths, checks every file in synthesis/outputs/ except README.md.
Exit 0 if clean, 1 if any output has an unresolved citation or a quote
that is not there.
"""
import os
import re
import sys

import synthesislib as lib

OUTPUTS_DIR = os.path.join(lib.SYNTHESIS_DIR, "outputs")

INH_TOKEN = re.compile(r"^inh/([a-z0-9.\-]+)/(\d{3})$")
UNIT3_TOKEN = re.compile(r"^([a-z0-9.\-]+)/([a-z0-9.\-]+)/(\d{3})$")
UNIT2_TOKEN = re.compile(r"^([a-z0-9.\-]+)/(\d{3})$")

_ledger_cache = {}
_inh_cache = None
_absence_cache = None
_corpus_slugs = None


def _loose(s):
    """normalize_quote, plus two typographic allowances quoting-within-
    quoting makes routine and wording never does:

    - the two quote characters collapse together, because house style
      lets a Stage 4 pass re-nest a quotation in single quotes where the
      ledger (quoting the commentary) used double, or vice versa, when
      the passage sits inside an outer quoted span;
    - punctuation immediately before a quote mark drops, because a
      fragment quoted mid-sentence legitimately omits the source's own
      trailing comma or period where the citing sentence continues past
      it instead.

    A real wording change on either side of a swapped quote or an
    interior comma still fails, because nothing else about the text is
    touched.
    """
    s = lib.normalize_quote(s).replace("'", '"')
    return re.sub(r'[.,;:!?]+(?=")', "", s)


def theme_ids():
    return set(lib.themes().keys())


def infer_theme(path):
    stem = os.path.basename(path)
    for tid in sorted(theme_ids(), key=len, reverse=True):
        if stem == tid + ".md" or stem.startswith(tid + "-"):
            return tid
    return None


def load_ledger(theme):
    if theme not in _ledger_cache:
        path = os.path.join(lib.LEDGERS_DIR, "%s-ledger.md" % theme)
        if not os.path.exists(path):
            _ledger_cache[theme] = None
        else:
            text = lib.read_text(path)
            ids = set(
                re.findall(r"`(%s/[a-z0-9.\-]+/\d{3})`" % re.escape(theme), text)
            )
            _ledger_cache[theme] = {"ids": ids, "norm": _loose(text)}
    return _ledger_cache[theme]


def load_inheritance():
    global _inh_cache
    if _inh_cache is None:
        ids = set()
        chunks = []
        for _, rec in lib.iter_records(lib.INHERITANCE_DIR):
            for e in rec.get("engagements", []):
                ids.add(e["id"])
                chunks.append(e.get("claim", ""))
                chunks.append(e.get("quote", ""))
        _inh_cache = {"ids": ids, "norm": _loose("\n".join(chunks))}
    return _inh_cache


def load_absence_locators():
    global _absence_cache
    if _absence_cache is None:
        locs = set()
        for _, rec in lib.iter_records(lib.EXTRACTIONS_DIR):
            for a in rec.get("absences", []):
                if "locator" in a:
                    locs.add(a["locator"])
        _absence_cache = locs
    return _absence_cache


def corpus_slugs():
    global _corpus_slugs
    if _corpus_slugs is None:
        _corpus_slugs = set(lib.corpus_map(lib.load_corpus()).keys())
    return _corpus_slugs


def extract_quotes(text):
    parts = text.split('"')
    return [parts[i] for i in range(1, len(parts), 2)]


def check_token(tok, themes_to_check, errors):
    m = INH_TOKEN.match(tok)
    if m:
        if tok not in load_inheritance()["ids"]:
            errors.append("inheritance id does not resolve: `%s`" % tok)
        return True

    m = UNIT3_TOKEN.match(tok)
    if m:
        theme, _record, _num = m.groups()
        if theme not in theme_ids():
            return False  # not a unit id - some other slash-shaped token
        ledger = load_ledger(theme)
        if ledger is None:
            errors.append(
                "`%s` names theme %r, which has no ledger at synthesis/ledgers/%s-ledger.md"
                % (tok, theme, theme)
            )
        elif tok not in ledger["ids"]:
            errors.append("unit id does not resolve in the %s ledger: `%s`" % (theme, tok))
        return True

    m = UNIT2_TOKEN.match(tok)
    if m:
        resolved = False
        checked = []
        for theme in themes_to_check:
            ledger = load_ledger(theme)
            if ledger is None:
                continue
            full = "%s/%s" % (theme, tok)
            checked.append(theme)
            if full in ledger["ids"]:
                resolved = True
                break
        if not resolved and checked:
            errors.append(
                "unit id does not resolve against %s: `%s`" % (" or ".join(checked), tok)
            )
        return True

    return False


def check_output(path):
    text = lib.read_text(path)
    theme = infer_theme(path)
    themes_to_check = [theme] if theme else sorted(theme_ids())

    errors = []
    slugs = corpus_slugs()
    absences = load_absence_locators()

    for tok in sorted(set(re.findall(r"`([^`]+)`", text))):
        if "#" in tok and not tok.startswith("http"):
            slug = tok.split("#", 1)[0]
            if slug in slugs and tok not in absences:
                errors.append(
                    "locator cited as a recorded absence but no extraction record "
                    "carries it: `%s`" % tok
                )
            continue
        check_token(tok, themes_to_check, errors)

    ledgers = [l for l in (load_ledger(t) for t in themes_to_check) if l]
    combined_norm = " ||| ".join(l["norm"] for l in ledgers) + " ||| " + load_inheritance()["norm"]

    for q in extract_quotes(text):
        if len(q.strip()) < 10:
            continue
        nq = _loose(q)
        if nq in combined_norm:
            continue
        if "..." in nq:
            frags = [f.strip() for f in nq.split("...") if f.strip()]
            pos, ok = 0, True
            for f in frags:
                i = combined_norm.find(f, pos)
                if i < 0:
                    ok = False
                    break
                pos = i + len(f)
            if ok:
                continue
        errors.append("quoted span not found verbatim in the ledger/inheritance: %s" % q.strip()[:160])

    return theme, errors


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if args:
        paths = args
    else:
        paths = sorted(
            os.path.join(OUTPUTS_DIR, n)
            for n in os.listdir(OUTPUTS_DIR)
            if n.endswith(".md") and n != "README.md"
        )

    total = 0
    for path in paths:
        rel = os.path.relpath(path, lib.REPO_ROOT).replace(os.sep, "/")
        theme, errors = check_output(path)
        if errors:
            label = theme or "no theme inferred from filename - checked against all ledgers"
            print("%s (%s): FAILED" % (rel, label))
            for e in errors:
                print("  -", e)
            total += len(errors)
        else:
            print("%s: OK" % rel)

    if total:
        print("\n%d issue(s) across %d output(s)." % (total, len(paths)))
        sys.exit(1)
    print("\n%d output(s) checked, all clean." % len(paths))


if __name__ == "__main__":
    main()
