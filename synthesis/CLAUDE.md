# synthesis/

Machinery for reading *across* the commentaries: an extraction layer that
turns 1.3 million words of paragraph-by-paragraph commentary into
locator-bearing records, ledgers that order those records by date, and a
synthesis stage that may write only from the ledgers.

Nothing in this folder is published. See "Publication seam" below —
the boundary is one directory move, and it is deliberate.

## Why an intermediate layer at all

The commentaries are locally focused by construction: each unit explains
its own unit. Nothing in them looks across works, and no synthesis prompt
can hold the corpus — `synthesis/corpus.json` puts it at 29 commentaries,
2,569 sections, 1,322,667 words. Feeding excerpts straight into an essay
prompt produces the failure this whole folder exists to prevent: fluent
claims with no textual anchor, indistinguishable at a glance from claims
that have one.

So the pipeline splits the labour, and each stage is forbidden the other's
move:

| Stage | What it does | Forbidden |
|---|---|---|
| 1. Extract | One commentary, one theme, one pass. Records what is claimed where, with a verbatim quote. | Interpreting. Connecting. Reaching past the commentary. |
| 2. Collate | Merge records into a ledger ordered by composition date. **A script, not a prompt.** | — |
| 3. Inheritance | Same commentaries, different question: engagements with predecessors, classified by mode. | Naming a predecessor text the commentary does not name. |
| 4. Synthesize | Write over the ledgers. | New textual claims. Filling gaps instead of flagging them. |

Stage 2 has no prompt because it needs no judgement, and a stage that
needs no judgement should not be given one. Everything a model could
smooth over while "collating" — dates, order, the difference between an
absence and an omission — is exactly what must not be smoothed.

## Locators, or: what makes a claim checkable

Every extracted unit carries `locator` and `quote`.

    locator   <commentary-slug>#<section-id>
    quote     verbatim text from inside that section

`scripts/synthesis_validate.py` looks the quote up and fails the build if
it is not there. Normalization forgives smart quotes, dashes, emphasis
marks and line wrapping; it forgives nothing about wording. This is the
one property that separates this pipeline from an elaborate way of
producing plausible sentences, and it is worth more than any amount of
instruction in the prompts.

Section ids come from `synthesis/corpus.json` and nowhere else. They are
minted by `section_id()` in `scripts/synthesislib.py`: NFKD, Greek
transliterated (φρόνησις → phronesis, because half the headings in this
corpus are Greek and dropping it leaves ids that name a section without
saying which), `§` → `s`, everything else hyphenated, prefixed with the
heading level.

That id is deliberately **not** the anchor GitHub Pages renders. Kramdown
strips every leading non-letter, so `§ 44` and an untitled section
collapse together — fine for a URL, useless for an address. The corpus
index carries the kramdown anchor separately, in `sections[].anchor`, for
link building only. WordPress renders the same files through
python-markdown's `toc` extension, which slugifies differently again;
a locator keyed to either dialect would break on one of the two published
surfaces.

## Absences are first-class

Stage 1 records where a theme was expected and is *not* present, and the
validator re-checks each claimed absence against the section: if the term
is in fact there, the record fails. A checked negative is evidence.

This is not a formality. The seed pass found exactly one occurrence of
`Sorge` in the whole GA 19 commentary — the glossary line — while GA 20,
one semester later, gives care its own chapter and calls it the being of
Dasein. That shape is invisible in the presences and obvious in the
absences.

Two cautions the schema exists to enforce:

- **Set `absent_terms` when the English is ambiguous.** "Care" and
  "concern" are ordinary English words. The GA 19 records check the German
  family only, because the commentary uses "care" non-technically on the
  same page.
- **Ledger silence is not absence.** Every ledger ends with "Not covered
  by this ledger" — the commentaries where the terms occur and no pass has
  run. Without it a reader cannot tell a finding from an unread file.

## Dating: composition, never volume number

`synthesis/chronology.json` orders the ledger spine, and orders it by
composition or delivery date. Volume number is not a proxy: Hua IV is a
1912 draft, a 1915 rework, two Stein copies, a Landgrebe typescript, and
four years of Husserl's insertions into it — six strata between 1912 and
1928, all of them stated in the commentary's own editor's introduction.
Units carry `stratum` where the commentary assigns them one.

**Dates come from what the commentaries state.** Seven entries are
`unresolved` because their commentary never dates its own text; they sit
in a separate undated bucket on every ledger rather than being placed on a
guess. Resolving one is a reading task — the date belongs in the
commentary first — and `STATUS.md` keeps the list. This mirrors
[prompts/filename-prompt.md](../prompts/filename-prompt.md) §Process step
4: never supply a volume number from outside knowledge. The same rule, for
the same reason.

Secondary literature is `role: reception` and sits alongside the spine,
not on it. `heidegger-husserl-intentionality-article.md` is `role: output`
and excluded from ledgers entirely: it is a Stage 4 product, and feeding
one back in as evidence is how a corpus starts citing itself.

## Layout

    themes.json          Theme registry. search_terms must include the
                         English renderings - the commentaries are English
                         by construction, so the German alone finds almost
                         nothing.
    chronology.json      Dates and strata, with evidence, hand-maintained.
    gaps.json            The reading queue. Written by Stage 4.
    corpus.json          Generated. Heading tree, line spans, digests.
    schema/              JSON Schema for all of the above.
    extractions/<theme>/<commentary-slug>.json
    inheritance/<commentary-slug>.json
    ledgers/             Generated. One markdown ledger per theme.
    outputs/             Stage 4 drafts. Not published.
    STATUS.md            Generated. The queue for the next pass.

## Running it

    python3 scripts/synthesis_index.py       # after any commentary changes
    python3 scripts/synthesis_query.py --theme sorge --sections
    python3 scripts/synthesis_validate.py    # after any record changes
    python3 scripts/synthesis_ledger.py --all
    python3 scripts/synthesis_status.py

Standard library only, deliberately: `jsonschema` and `frontmatter` are
not installed on a bare machine, and validation that cannot be run
locally will be run only by CI, which is too late. The schema files stay
the single statement of the format; `check_schema` in `synthesislib.py`
reads them.

Both generators are pure functions of their inputs — no timestamps — so a
rebuild that changes nothing produces no diff and no commit.

## What CI does and does not do

`.github/workflows/synthesis.yml`. **The model never runs in CI.**
Extraction is a scholarly act that wants a human in the loop, and a record
generated by a workflow is a record nobody read before it landed. CI is
the auditor:

- On a pull request: re-check every quote and every claimed absence
  against the commentaries *as the branch has them*. Errors fail the build.
- On a push to `main`: rebuild `corpus.json`, the ledgers and `STATUS.md`,
  and commit them `[skip ci]`.

The `[skip ci]` matters concretely: `wordpress-sync.yml` triggers on every
`**.md` push, and `synthesis/ledgers/*.md` would otherwise start a sync run
with nothing to publish. Both workflows can commit to `main`, so the
rebuild pulls with rebase and retries before pushing.

Staleness — a commentary edited after a record quoted it — is a warning,
never an error. The right report is "re-extract this", not "you lied about
a quote", and `STATUS.md` carries the list.

## Publication seam

`scripts/sync_wordpress.py` globs `commentaries/*/*.md`, exactly one
directory level. Everything here is outside that glob and therefore
unpublished — deliberately, not incidentally. See
[commentaries/CLAUDE.md](../commentaries/CLAUDE.md) §"Every push
auto-publishes": a file that lands in `commentaries/<author>/` goes live to
WordPress and GitHub Pages on the next push, with no draft step.

So moving a Stage 4 output from `synthesis/outputs/` into
`commentaries/<author>/` **is the act of publishing it**. That is the
author's decision and never a step in a synthesis pass. When it is made,
the file needs frontmatter, a filename per the convention, and — if it
quotes German or French — the translation discipline that
`commentaries/CLAUDE.md` spells out.

## The loop

The pipeline is only worth its weight if it says what to do next.
`STATUS.md` is that report, and each of its sections is a queue fed by a
different part of the machine:

- **Next candidates** — commentaries where a theme's terms occur and no
  pass has run, ranked by density. From the retrieval layer.
- **Stale records** — a commentary changed under a record. From the
  digests.
- **Chronology to resolve** — commentaries that do not date their own
  text. From `chronology.json`.
- **Open gaps** — what a synthesis pass could not support. From
  `gaps.json`.

The last is the one that matters. Stage 4 is required to flag what the
ledgers cannot support rather than fill it, which turns the synthesis
pass into an instrument for finding what to read next: gap → extraction
pass or new commentary → richer ledger → a synthesis that can now make
the claim, or a sharper gap. A pass that flags nothing has either
exhausted its question or failed to look.

## Prompts

[prompts/extraction-prompt.md](../prompts/extraction-prompt.md) ·
[prompts/inheritance-prompt.md](../prompts/inheritance-prompt.md) ·
[prompts/synthesis-prompt.md](../prompts/synthesis-prompt.md) ·
[prompts/article-prompt](../prompts/article-prompt) (Stage 4's most
ambitious output hands off to it; its Research Register and the gap rule
are the same instrument — keep one list, in `gaps.json`).
