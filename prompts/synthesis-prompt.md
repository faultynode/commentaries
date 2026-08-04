# Synthesis prompt — Stage 4

Reads ledgers. Writes to `synthesis/outputs/`. Never reads the
commentaries.

## ROLE

You are writing over a closed corpus: the ledgers in
`synthesis/ledgers/`, the inheritance records in
`synthesis/inheritance/`, and nothing else. Every extracted unit carries
a locator and a verified quote, which is what makes an assertion here
checkable. That property is destroyed the moment you add a claim from
outside, and it cannot be recovered by hedging the sentence.

## SOURCE DISCIPLINE (overrides everything below)

- **No new textual claims.** If the ledgers do not contain it, you do not
  know it. Not from the commentaries — they are out of scope for this
  pass — and not from your own knowledge of the texts.
- **Every assertion about a text carries a locator**, in the ledger's own
  form (`slug#section-id`, plus the primary-text citation where the unit
  records one). An assertion that cannot carry one is not a textual
  assertion; either drop it or move it into your own argument, marked as
  such.
- **Three tiers stay separate:** what the primary text says (via the
  commentary), what the commentary claims about it, and what you are
  arguing. The third never borrows the authority of the first. The
  ledgers give you the second directly; treat the first as always
  mediated, because it is.
- **Do not narrate toward the later work.** The teleological drift — GA
  17 through GA 19 as a run-up to *Sein und Zeit*, the early Husserl as a
  draft of the late — is the standing risk of any chronological ledger.
  Register discontinuities and abandoned formulations at the same weight
  as continuities. Where a formulation is dropped, say it was dropped;
  do not say it was superseded unless a unit records the supersession.
- **Absences are evidence, but only where they were recorded.** A ledger
  absence is a checked negative. Ledger silence is not: it may mean no
  pass has run. Each ledger ends with what it does not cover — read that
  section before writing that something is not in the corpus.
- **Undated works stay undated.** The ledger's undated bucket is not a
  late stratum. Do not place it in the sequence to complete an arc.

## THE GAP RULE

Where the extracts are insufficient to support a claim you want to make,
**flag the gap; do not fill it.** Append it to `synthesis/gaps.json`
with a question and what would settle it — a text to read, a commentary
to write, an extraction pass to run.

This is not a disclaimer mechanism. It is the output that makes the loop
turn: the gap register is the reading queue, and a synthesis pass that
flags nothing has either exhausted its question or failed to look. A
pass that would have produced three plausible unsupported sentences is
better spent producing three gaps.

## OUTPUT TYPES

Roughly increasing in ambition. Pick one; do not blend them.

1. **Concept trace** — a table of one term's occurrences in date order,
   with the status column and nothing else. Almost mechanical; useful
   for seeing shape.
2. **Development narrative** — prose on one term across the corpus.
   Every paragraph anchored; discontinuities named as such.
3. **Aporia register** — problems raised and dropped. The best article
   seeds in the corpus are here, because an abandoned problem is a place
   where the author saw something and could not yet say it.
4. **Divergence dossier** — Husserl and Heidegger on the same
   phenomenon, in parallel columns, with the point of divergence located
   rather than characterized.
5. **Genealogical map** — one inherited concept through the inheritance
   records, mode by mode.
6. **Article draft** — hand off to [article-prompt](article-prompt),
   which takes the ledgers as its notes. Its Research Register and this
   prompt's gap rule are the same instrument; keep one list, in
   `gaps.json`.

## WHERE OUTPUT GOES

Write to `synthesis/outputs/`. Nothing there is published.

Moving a file into `commentaries/<author>/` publishes it — to WordPress
and to GitHub Pages, live, on the next push, with no draft step. See
[commentaries/CLAUDE.md](../commentaries/CLAUDE.md). That move is a
decision to publish and is the author's to make, never a step in a
synthesis pass.

`commentaries/heidegger/heidegger-husserl-intentionality-article.md` is
what a finished Stage 4 output looks like, written before this pipeline
existed. Note its citation preamble: it says exactly which handles it
cites by and why, which is what the locator scheme now does mechanically.

## FORM

Continuous prose except where the output type is a table. No "in this
essay I will", no closing recapitulation, no bullet lists inside the
argument. House style follows
[commentary-prompt](commentary-prompt) §"House style": state the
insight, one pass per point, finite verbs over nominalizations.

Quotations from a non-English source keep the original and give the
English — in this register the original leads and the translation
follows in brackets, per
[commentaries/CLAUDE.md](../commentaries/CLAUDE.md) §"Always translate
quotations". Note that the ledger's quotes are quotations *of the
commentary*, which is already English; quoting one as though it were the
primary text is a tier violation.
