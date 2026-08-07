# synthesis/

Machinery for reading *across* the commentaries: extraction records that
pin a claim to a place in a commentary, ledgers that order those records
by date, and a synthesis stage that may write only from the ledgers.

- **Why it is built this way** — [synthesis-design.md](../docs/synthesis-design.md)
- **How to run it** — [synthesis-operations.md](../docs/synthesis-operations.md)
- **What binds you while working here** — this file.

Nothing in this folder is published. That is load-bearing: see
"Publication seam" below.

## The invariant

> Every claim about a text carries a locator and a verbatim quote, and a
> script looks the quote up.

`scripts/synthesis_validate.py` resolves
`<commentary-slug>#<section-id>` against `corpus.json` and searches the
named section for the quote. Normalization forgives smart quotes, dashes,
emphasis marks and line wrapping; it forgives nothing about wording. A
quote that is not there fails the build, and CI runs the same check on
every pull request.

Everything below is downstream of keeping that check meaningful.

## Rules

1. **Copy quotes out of the file. Never retype one from context.** A
   remembered quote is the one failure mode the whole apparatus exists to
   catch, and it will be caught.
2. **Take locators from `corpus.json`.** Do not construct a section id
   from a heading by hand — the id scheme transliterates Greek, maps `§`
   to `s`, and prefixes the heading level.
3. **Stay inside the commentary.** Stage 1 and 3 read one commentary and
   nothing else — not the primary text, not another commentary, not what
   you know. `primary_locator` records the citation *the commentary
   gives*; where it gives none, omit the field.
4. **Extraction does not interpret; synthesis does not make new textual
   claims.** Connective prose in a `claim` is a rule violation, not a
   stylistic lapse. A `claim` over 400 characters is almost always
   interpretation and the schema rejects it.
5. **Set `absent_terms` when the English is an ordinary word.** "Care",
   "concern", "the body" occur non-technically all over this corpus; an
   absence claim checked against them will fail for the wrong reason.
6. **Never supply a date from memory.** `chronology.json` records what
   the commentaries state. If a date must come from elsewhere, set
   `stated_in_commentary: false` and put the source in `evidence` — the
   validator requires it. Same rule, same reason as
   [filename-prompt.md](https://github.com/faultynode/prompts/blob/main/repo-maintenance/filename-prompt.md) §Process step 4.
7. **Declare `coverage` honestly.** `partial` plus a `coverage_note` is
   always available and keeps the record in the queue. Overstated
   coverage is the one failure the validator cannot catch.
8. **Do not hand-edit generated files** (below). They are rebuilt by CI
   and your edit will vanish.
9. **Flag gaps; do not fill them.** A Stage 4 pass that cannot support a
   claim appends to `gaps.json`. That register is the reading queue, and
   it is the output that makes the next iteration possible.

## Authored vs. generated

| Authored — edit these | Generated — never edit |
|---|---|
| `themes.json` | `corpus.json` |
| `chronology.json` | `ledgers/*.md` |
| `gaps.json` | `STATUS.md` |
| `extractions/<theme>/<slug>.json` | |
| `inheritance/<slug>.json` | |
| `schema/*.json` | |
| `outputs/` | |

Generated files are pure functions of the authored ones — no timestamps —
so rebuilding without a change produces no diff.

## Layout

Design and operations docs live in [`docs/`](../docs)
([synthesis-design.md](../docs/synthesis-design.md),
[synthesis-operations.md](../docs/synthesis-operations.md)); this folder
holds the data.

    themes.json          Theme registry. search_terms must include the
                         English renderings - the commentaries are English
                         by construction, so German alone finds almost
                         nothing.
    chronology.json      Dates and strata, with evidence.
    gaps.json            The reading queue. Written by Stage 4.
    corpus.json          Generated. Heading tree, line spans, digests.
    schema/              JSON Schema for all of the above.
    extractions/<theme>/<commentary-slug>.json
    inheritance/<commentary-slug>.json
    ledgers/             Generated. One markdown ledger per theme.
    outputs/             Stage 4 drafts. Not published.
    STATUS.md            Generated. The queue for the next pass.

Prompts live in the separate
[faultynode/prompts](https://github.com/faultynode/prompts) repo, under
`synthesis-pipeline/`: extraction (Stage 1), inheritance (Stage 3),
synthesis (Stage 4). Stage 2 is a script and has no prompt, because it
needs no judgement.

## Gotchas

**Ledger silence is not absence.** Every ledger ends with "Not covered by
this ledger" — commentaries where the terms occur and no pass has run.
Read it before writing that something is not in the corpus. A recorded
absence is evidence; an unread file is not.

**Editing a commentary stales the records that quote it.** Nothing breaks
and no build fails: the recorded digest stops matching, and the records
appear in `STATUS.md` as re-extraction tasks. Rewording a heading does
more — it changes the section id, so locators pointing at it stop
resolving.

**Hua IV is six strata, not one date.** 1912 draft, 1915 rework, two
Stein copies, the Landgrebe typescript, Husserl's insertions to 1928 —
all stated in that commentary's own editor's introduction. Volume number
is never a proxy for composition date, and this is the corpus's standing
counterexample.

**`role: output` files must not re-enter as evidence.**
`heidegger-husserl-intentionality-article.md` is a Stage 4 product. A
corpus that cites its own outputs has stopped being anchored to anything.

## Publication seam

`scripts/sync_wordpress.py` globs `commentaries/*/*.md`, exactly one
directory level. Everything here is outside that glob and therefore
unpublished — deliberately, not incidentally. See
[commentaries/CLAUDE.md](../commentaries/CLAUDE.md) §"Every push
auto-publishes": a file that lands in `commentaries/<author>/` goes live
to WordPress and GitHub Pages on the next push, with no draft step.

So moving a Stage 4 output into `commentaries/<author>/` **is the act of
publishing it**. That is the author's decision, never a step in a
synthesis pass. The procedure, once the decision is made, is
[synthesis-operations.md](../docs/synthesis-operations.md) §P8.
