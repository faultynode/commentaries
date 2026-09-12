# Synthesis pipeline — operations

Runbook. For why any of it is shaped this way, see
[synthesis-design.md](synthesis-design.md).

---

## Prerequisites

`python3`. Nothing else — the synthesis scripts import only the standard
library, deliberately (synthesis-design.md §D7). Run them from anywhere; paths resolve
against the repo root.

## Command reference

| Command | Does | Exit codes |
|---|---|---|
| `python3 scripts/synthesis_index.py` | rebuild `corpus.json` | 0 |
| `python3 scripts/synthesis_index.py --check` | is it current? | 0 / 1 stale |
| `python3 scripts/synthesis_query.py --theme <id>` | commentaries ranked by term density | 0 / 2 bad args |
| `… --theme <id> --commentary <slug> --sections` | the sections to read, with locators | |
| `… --terms "a,b,c" --sections --urls` | ad-hoc search, with published links | |
| `python3 scripts/synthesis_validate.py` | check every record | 0 / 1 errors |
| `python3 scripts/synthesis_validate.py --strict` | warnings count as errors | 0 / 1 |
| `python3 scripts/synthesis_ledger.py --all` | rebuild every ledger | 0 / 2 unknown theme |
| `python3 scripts/synthesis_ledger.py --theme <id>` | rebuild one | |
| `python3 scripts/synthesis_ledger.py --all --check` | are they current? | 0 / 1 stale |
| `python3 scripts/synthesis_status.py [--check]` | rebuild `STATUS.md` | 0 / 1 |
| `python3 scripts/synthesis_lexicon.py --check` | schema, references, attested renderings | 0 / 1 errors |
| `python3 scripts/synthesis_lexicon.py --expand --theme <id>` | what `themes.json` is missing, both directions | 0 / 2 unknown theme |
| `… --expand --theme <id> --json` | the merged `search_terms` array, ready to paste | |
| `python3 scripts/synthesis_lexicon.py --attest [--theme <id>]` | which registered terms the corpus contains | 0 |
| `python3 scripts/synthesis_lexicon.py --candidates` | headwords with no theme, by corpus density | 0 |

Useful query flags: `--author husserl`, `--top 40`, `--min-hits 3`,
`--urls`. Sections already carrying a record print as `[done]`.

## The short loop

    python3 scripts/synthesis_query.py --theme sorge --commentary <slug> --sections
    # read those sections; write the record
    python3 scripts/synthesis_validate.py
    # fix what it reports, repeat until OK
    git commit

Ledgers and `STATUS.md` are rebuilt by CI on push. Rebuild them locally
only if you want to read them before pushing.

---

## P1 · Run an extraction pass

Stage 1. One commentary, one theme. Prompt:
[extraction-prompt.md](https://github.com/faultynode/prompts/blob/main/synthesis-pipeline/extraction-prompt.md).

1. **Pick the target.** `synthesis/STATUS.md` §Themes lists candidates
   ranked by term density. Prefer a dated commentary over an undated one:
   an undated commentary cannot go on the ledger spine (P5).

2. **Find the sections.**

       python3 scripts/synthesis_query.py --theme sorge \
           --commentary heidegger-sein-und-zeit-commentary --sections --top 40

   The ranking is a pointer, not a verdict. A section with two hits can
   be where the term is introduced.

3. **Get the digest** — from `corpus.json`, or:

       python3 -c "import hashlib,sys;print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest())" \
           commentaries/heidegger/heidegger-sein-und-zeit-commentary.md

4. **Read the sections in the file, in order,** and write
   `synthesis/extractions/<theme>/<commentary-slug>.json`. Copy quotes;
   never retype them. Locators come from `corpus.json` and nowhere else.

5. **Record absences.** Where you expected the theme and did not find it,
   with `expected_because`. Set `absent_terms` explicitly when the
   English rendering is an ordinary word — "care", "concern", "the body"
   will otherwise appear in a section that contains no technical use.

6. **Declare coverage honestly.** `complete` asserts you scanned the whole
   commentary. Otherwise `partial` plus a `coverage_note` naming the
   range; the record stays in the `STATUS.md` queue.

7. **Validate and fix.**

       python3 scripts/synthesis_validate.py

Sizing: a substantial chapter is 8–12 units. Splitting one commentary
across several partial passes is normal and cheaper than one long pass,
because a partial pass that names its range is honest and a long pass
that silently thins out is not.

## P2 · Run an inheritance pass

Stage 3, prompt [inheritance-prompt.md](https://github.com/faultynode/prompts/blob/main/synthesis-pipeline/inheritance-prompt.md).
Same procedure as P1, but retrieval keys on predecessor names rather than
a theme:

    python3 scripts/synthesis_query.py \
        --terms "Aristotle,Descartes,Kant,Brentano,Natorp,Husserl" \
        --commentary <slug> --sections --top 40

Writes `synthesis/inheritance/<commentary-slug>.json`. One record per
commentary, covering all predecessors — not one per predecessor.

## P3 · Run a synthesis pass

Stage 4, prompt [synthesis-prompt.md](https://github.com/faultynode/prompts/blob/main/synthesis-pipeline/synthesis-prompt.md).

1. Rebuild the ledgers so you are writing against current records:

       python3 scripts/synthesis_ledger.py --all

2. **Read "Not covered by this ledger" first.** It is the list of
   commentaries where the terms occur and no pass has run. Anything you
   would say about the corpus as a whole is bounded by it.

3. Write into `synthesis/outputs/`, from the ledgers only. Every textual
   assertion carries a locator.

4. **Append every gap to `gaps.json`** rather than filling it: `id`
   (`gap-NNN`), `opened`, `question`, `needs`, `status: open`, and
   `raised_by` pointing at the output file. This is the deliverable that
   makes the next iteration possible.

5. `python3 scripts/synthesis_status.py` to see the gaps in the queue.

## P4 · Add a theme

Append to `synthesis/themes.json`:

```json
{
  "id": "welt",
  "english": "world",
  "glossary_terms": ["Welt", "Weltlichkeit", "Umwelt"],
  "search_terms": ["Welt", "Weltlichkeit", "Umwelt", "world", "worldhood",
                   "environing world", "surrounding world", "life-world"],
  "note": "Why this theme is worth tracing, and what the traps are."
}
```

`search_terms` **must include the English renderings** — the commentaries
are English by construction, so German alone finds almost nothing. Include
the variants of competing translations (`presence-at-hand` and `objective
presence`; `readiness-to-hand` and `handiness`) or whole commentaries drop
out of the ranking.

Then `python3 scripts/synthesis_status.py` — the theme appears with a
ranked candidate list, and it is queued.

Before typing `search_terms` by hand, check what is already registered:
`python3 scripts/synthesis_lexicon.py --expand --theme welt --json` prints
the merged array, and P9 below is the fuller loop.

## P5 · Resolve a chronology entry

Nine commentaries do not date their own text (`STATUS.md` §Chronology to
resolve). They sit off the ledger spine until fixed, and the fix is a
reading task, not a lookup.

1. Find the date **in the volume the commentary works from** and write it
   into the commentary's opening note — that is where it belongs.
2. Re-run `synthesis_index.py` (the file changed).
3. Update the `chronology.json` entry: `status: "resolved"`, and a
   stratum with `year_start`, `stated_in_commentary: true`, and `evidence`
   quoting the commentary.
4. If the commentary distinguishes layers — a rework, a copyist's
   version, a second delivery — give each its own stratum. Hua IV and Hua
   XI are the worked examples.

Never fill a date from memory. If you must record one whose source is
outside the commentary, set `stated_in_commentary: false` and put the
source in `evidence`; the validator requires it.

## P6 · Refresh a stale record

A record is stale when its commentary changed after the pass ran.
`STATUS.md` §Stale records lists them.

1. `python3 scripts/synthesis_validate.py` — read which quotes no longer
   resolve. Often none do: a stale digest with all quotes still passing
   means the edit did not touch the extracted sections.
2. Re-read the affected sections in the current file.
3. Update the changed `quote`s and any `locator` whose heading was
   reworded. **Keep the unit `id`s** — they are stable across re-runs, so
   the diff shows what the edit changed.
4. Update `source_sha256` and `extracted_at`.
5. Validate.

If the quotes all still pass, updating `source_sha256` alone is a correct
and complete refresh.

## P7 · Add or edit a commentary

Adding: nothing is required. The next `synthesis_index.py` picks it up
and it appears in `STATUS.md` as a candidate. Add a `chronology.json`
entry, or the validator warns that it cannot appear on any ledger.

Editing: expect stale records (P6). Rewording a heading also changes the
section id, so locators pointing at it stop resolving — that surfaces as
`no section '…' in …`, not as a silent mis-resolution.

Renaming or deleting a commentary file: update or delete every record
naming the old slug, and its `chronology.json` entry. The validator will
name them (`unknown commentary '…'`).

## P8 · Publish a synthesis output

**This is the only irreversible procedure here.** `sync_wordpress.py`
publishes `commentaries/*/*.md` live on push, with no draft step; there
is deliberately no automation across this line.

1. Decide to publish. Nothing else in the pipeline makes this decision.
2. `git mv synthesis/outputs/<file>.md commentaries/<author>/<slug>.md`,
   naming it per [commentaries/CLAUDE.md](../commentaries/CLAUDE.md)
   §"Filename convention".
3. Add frontmatter — `layout: default` and `title:`. Do **not** set
   `wordpress_id`; the sync writes it back.
4. Check the translation discipline: in published commentary text the
   English leads and the original follows in parentheses. Ledger quotes
   are quotations *of a commentary* and are already English; check that
   none has been carried over as though it were the primary text.
5. Add a `chronology.json` entry with `role: "output"`, so it can never
   re-enter a ledger as evidence.
6. Push. It is live on WordPress and GitHub Pages within a run.

---

## P9 · Widen a theme's search terms from the lexicon

The retrieval layer is only as good as its term list, and the list is
typed by hand. This is the loop that stops it drifting:

1. `python3 scripts/synthesis_lexicon.py --expand --theme <id>` — reads
   both directions. *Missing from search_terms* are renderings the
   lexicon knows and the theme does not: every one of them is a
   commentary the theme's searches are currently missing. *In
   search_terms with no lexicon entry* is the reverse question — a term
   nobody has accounted for, which may be good and may be a relic.
2. Decide. This is a judgement, not a merge: `absent_terms` defaults to
   the theme's search terms, so widening them changes what a recorded
   absence means. See [lexicon-design.md](lexicon-design.md) L3.
3. Paste. `--json` prints the merged array in `themes.json`'s shape.
4. `python3 scripts/synthesis_status.py` — the candidate ranking moves,
   usually a lot.
5. Any extraction record whose absences were keyed to the old terms is
   now under-checked. It is not stale — the commentary did not change —
   so nothing reports it. Re-run the absence checks by hand if the theme
   gained a rendering that matters (P6 is the procedure for the
   file-changed case, not this one).

## P10 · Register a headword

One entry per term of art, in `synthesis/lexicon.json`. The minimum is a
headword, its forms, and one rendering with a source.

```json
{
  "id": "welt",
  "headword": "Welt",
  "language": "de",
  "authors": ["heidegger"],
  "forms": ["Welt", "Weltlichkeit", "Umwelt"],
  "renderings": [
    { "english": "world", "source": "repo-registry" },
    { "english": "environing world", "source": "corpus",
      "locator": "heidegger-sein-und-zeit-commentary#h6-s-15-the-being-of-the-beings-encountered-in-the-environing-world" }
  ],
  "theme": "welt",
  "contrast_with": ["umwelt"],
  "gloss": "Your own words, under 240 characters, never a reference work's."
}
```

Then mine the corpus for the same headword — the commentaries gloss their
own terms, and those glosses are the renderings actually in use here:

    grep -rno ".\{45\}(\*\?Welt\*\?)" commentaries/*/*.md

Each `English (Welt)` hit is an attested rendering. Add it with
`source: "corpus"` and the locator of the section it sits in (take the
section id from `corpus.json`, never from the heading — CLAUDE.md rule 2),
and `--check` will confirm the section really contains both halves.

Finish with `python3 scripts/synthesis_lexicon.py --check`. Warnings about
shared renderings are asking you to record a collision in
`contrast_with`, not to delete a rendering.

## P11 · Bring in a reference work

A published dictionary of an author's terms is a headword list and a
rendering list, and both are useful here. The book itself is not: keep it
in [faultynode/sources](https://github.com/faultynode/sources) or outside
git, add it to `lexicon.json` `sources[]` with `kind: "dictionary"` and a
full bibliographic citation, and take from it only forms, renderings and
cross-references. No definition text — see
[lexicon-design.md](lexicon-design.md) L4, and note that `synthesis/` is
one `git mv` from a live public page.

Then work the batch: P10 per headword, `--check`, `--expand` per theme it
touches (P9), and `--candidates` at the end. A dictionary for an author
with no commentary in the corpus is still worth registering — its entries
rank in `--candidates` on hits from the commentaries that discuss him, and
that ranking is the coverage map for the commentary nobody has written.

Three things a bulk import always needs, learned from the first one
(Dahlstrom's Heidegger and Moran and Cohen's Husserl, 535 headwords
between them — see [lexicon-design.md](lexicon-design.md) §6):

- **Translator divergences are data.** Where the reference work marks a
  rendering as some translator's rather than its own, put it in
  `translator`. That is the field the `vorhandenheit` theme note wanted.
- **Collisions come in bulk and must be recorded, not resolved.**
  `--check` warns for every English word two entries share; the fix is
  `contrast_with` on both, never deleting a rendering.
- **Count the lines your heading pattern rejects.** Reading them is how
  you find entries a layout assumption loses — seven Husserl terms were
  missing until that check was run, all of them entries whose body text
  runs on to the heading line. Read them twice: a headword with no
  original-language parenthetical may be one the export's markup broke,
  one whose headword is Latin or Greek, an English concept for
  `language: "en"`, or a pure redirect that belongs on another entry as a
  rendering.
- **Grep the result for stray brackets.** A heading with two
  parentheticals defeats a pattern that reads from the first `(` to the
  last `)`, and the wreckage shows up as a form containing `(` or `)`.
  Finding none is the check that says the extraction is clean.
- **Check any form you derive rather than read.** Stripping the article
  off `das Man` produced `Man`, which is 87% noise; the same rule on
  `die natürliche Einstellung` is exactly right. A derived form gets the
  same `--attest` reading as a printed one.
- **Decide `unsearchable` by looking, not by counting.** Run `--attest`
  over the new entries. A form flagged "fires mostly inside longer
  words" is swamped by something else (`Natur` inside *nature*, `Leib`
  inside *Leibniz*) or compounded in German (`Wissen` inside
  *Wissenschaft*), and only the words themselves say which. Flag the
  first, leave the second.

## CI reference

`.github/workflows/synthesis.yml`. **The model never runs here.**

| Event | Job | Behaviour |
|---|---|---|
| pull request touching `synthesis/**`, `commentaries/**`, `scripts/synthesis*.py` | `validate` | quotes and absences re-checked against the branch's commentaries, then the lexicon's attested renderings; errors fail |
| push to `main`, same paths | `validate` then `rebuild` | rebuilds `corpus.json`, ledgers, `STATUS.md`; commits `[skip ci]` |
| manual `workflow_dispatch` | both | |

Notes:

- Validation on a PR uses a **freshly built** corpus, not the committed
  `corpus.json`, so a PR that edits a commentary is checked against the
  edited text. A stale committed index is a warning, never a failure.
- The rebuild commit carries `[skip ci]` because `wordpress-sync.yml`
  triggers on every `**.md` push and would otherwise start a run over
  generated ledgers with nothing to publish.
- Both workflows can commit to `main`, so the rebuild pulls with rebase
  and retries with backoff before pushing.
- Staleness never fails CI. Use `--strict` locally for a deliberate audit.

## Troubleshooting

Schema errors are reported first and **skip the rest of the checks on
that record** — fix them, re-run, then read the semantic errors.

| Message | Means | Fix |
|---|---|---|
| `quote not found in <slug>#<id> (lines N-M)` | the quote is not in that section | copy it from the file; check the locator names the right section |
| `… - record is stale, re-extract` | same, but the file changed since the pass | P6 |
| `claims 'X' is absent from …, but it occurs there` | false absence | drop the absence, or narrow `absent_terms` to the technical forms |
| `no section '<id>' in <slug>` | id does not exist — usually a reworded heading, or an id typed by hand | take it from `corpus.json`; run `synthesis_index.py` if the file changed |
| `unknown commentary '<slug>'` | slug does not match a file | check spelling; the slug is the filename stem |
| `locator points at X but the record is about Y` | a record covers exactly one commentary | move the unit to the right record |
| `locator must be '<commentary-slug>#<section-id>'` | malformed | one `#`, no spaces, no leading path |
| `duplicate unit id, also in <path>` | ids are globally unique | renumber; ids are stable, so prefer the next free number |
| `unit id must begin with the theme id` | id convention is `theme/short/NNN` | rename |
| `file sits under a directory that is not its theme` | `extractions/<theme>/` must match the record's `theme` | move the file or fix the field |
| `filename does not match the commentary slug` | filename is the slug plus `.json` | rename |
| `theme 'x' is not in themes.json` | unregistered theme | P4 |
| `unknown stratum 'x'` | `stratum` must name one in `chronology.json` | fix, or drop the field if the commentary does not assign a layer |
| `partial coverage must say what it covered` | `coverage: partial` needs `coverage_note` | state the range |
| `$.units[0].claim: longer than 400 characters (512)` | a claim is doing interpretation | one sentence: what is claimed there |
| `$.units[0].status: 'mentioned' not one of […]` | closed enum | pick the one that would change most if wrong |
| `$.units[0]: unexpected property 'note'` | schemas are `additionalProperties: false` | remove it, or add the field to the schema deliberately |
| `no entry for <slug> - it cannot appear on any ledger` (warning) | missing `chronology.json` entry | add one, `unresolved` if the commentary gives no date |
| `<slug> is marked resolved with no dated stratum` | `status` and `strata` disagree | set `unresolved`, or supply `year_start` |
| `stratum 'x' is not stated in the commentary and gives no evidence` | `stated_in_commentary: false` requires `evidence` | say where the date came from |
| `synthesis/corpus.json is missing` | never indexed | `python3 scripts/synthesis_index.py` |

## Recovery

**Deleted or corrupted `corpus.json`** — regenerate it:
`python3 scripts/synthesis_index.py`. It is derived from the commentaries
and holds nothing of its own.

**Ledgers or `STATUS.md` look wrong** — they are generated. Delete and
rebuild; if the content is still wrong, the fault is in a record, and
`synthesis_validate.py` locates it.

**A ledger changed without any record changing** — expected when a
commentary was edited: the ledger embeds section titles and links from
`corpus.json`. Check `git diff` is only titles and hit counts.

**Two workflow runs raced** — the rebuild rebases and retries. If a run
still fails to push, rerun it; the rebuild is idempotent and the artifacts
are pure functions of the inputs.

**A bulk edit staled every record** — validate, then work
`STATUS.md` §Stale records one at a time (P6). Do not mass-update
`source_sha256` without re-reading: that is exactly the move the digest
exists to prevent.

**A published output needs retracting** — deleting the file from
`commentaries/<author>/` does not delete the WordPress post; the sync only
creates and updates. Remove the post in WordPress by hand, and remove the
stray `index.html` entry if it survives a rebuild.

## Periodic maintenance

Roughly monthly, or after any run of commentary edits:

    python3 scripts/synthesis_index.py
    python3 scripts/synthesis_validate.py --strict
    python3 scripts/synthesis_ledger.py --all
    python3 scripts/synthesis_status.py

`--strict` is the point: it surfaces the staleness that everyday runs
tolerate. Then read `STATUS.md` top to bottom and pick the next pass —
stale records first (they are cheap and they decay), then open gaps (they
are the ones a synthesis pass is waiting on), then unresolved dates, then
new candidates.
