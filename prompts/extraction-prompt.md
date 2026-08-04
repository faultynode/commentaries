# Extraction prompt — Stage 1

One pass, one commentary, one theme. Produces
`synthesis/extractions/<theme>/<commentary-slug>.json`.

## ROLE

You are extracting, not reading. The output is a table of what one
commentary says about one theme, at named places, in a form another pass
can collate. It is not an interpretation, a summary, or an argument, and
nothing downstream will treat it as one.

## HARD RULES (these are what the validator enforces)

- **No interpretation.** State what is claimed at that place. Not what it
  means, not what it anticipates, not how it relates to anything else.
  Connective prose is a rule violation, not a stylistic lapse.
- **Every unit carries a verbatim quote** from the commentary, inside the
  section its locator names. `scripts/synthesis_validate.py` checks the
  quote character by character (modulo whitespace, smart quotes, dashes
  and emphasis marks). A unit whose quote cannot be found fails the
  build. Copy quotes; never retype them from memory.
- **Only the commentary.** The commentary is the corpus for this pass.
  Do not reach past it to the primary text, to another commentary, or to
  anything you know. `primary_locator` records the citation *the
  commentary itself gives*; where it gives none, omit the field.
- **Substantive work only.** A unit is a place where the theme does
  argumentative work. Passing mentions, list items and repetitions of a
  point already recorded are not units.
- **Absences are part of the output.** List the places you expected the
  theme and did not find it. An empty `absences` array asserts that no
  such place exists — the validator re-checks every absence you claim
  against the section text, so a false absence fails too.

## PROCEDURE

1. Find the sections worth reading:

       python3 scripts/synthesis_query.py --theme <theme> \
           --commentary <slug> --sections --top 40

   Sections already carrying a record are marked `[done]`. Skip them
   unless you are deliberately re-extracting.

2. Read those sections in full, in the file, in order. The query is a
   pointer, not a substitute — a section with two hits can be where the
   theme is introduced.

3. Record the digest you read against:

       python3 -c "import hashlib,sys;print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest())" <path>

   Or take it from `synthesis/corpus.json`, which is the same value.

4. Write the record. Schema: `synthesis/schema/extraction.schema.json`.
   Locators are `<commentary-slug>#<section-id>`; section ids come from
   `synthesis/corpus.json` and nowhere else — do not invent one from a
   heading.

5. Validate, and fix what it reports:

       python3 scripts/synthesis_validate.py

## THE STATUS COLUMN

Four values, and the choice is the whole point of the column:

- `introduced` — the term is put into play here, with or without a
  definition.
- `presupposed` — used as already available, doing work it is not given
  here.
- `revised` — the sense is altered from an earlier use in the same
  commentary.
- `criticized` — the term or its received sense is put in question.

If two apply, choose the one that would change most if it were wrong.

## COVERAGE

`complete` asserts you scanned the whole commentary. If you covered part
of it, say `partial` and state the range in `coverage_note` — the status
report treats a partial pass as unfinished and keeps it in the queue.
Overstating coverage is the one failure the validator cannot catch.

## SHAPE OF THE OUTPUT

```json
{
  "schema_version": 1,
  "theme": "sorge",
  "commentary": "heidegger-ga-20-prolegomena-zur-geschichte-des-zeitbegriffs-commentary",
  "source_sha256": "<64 hex>",
  "extracted_at": "YYYY-MM-DD",
  "extractor": { "agent": "<model or person>", "prompt": "prompts/extraction-prompt.md" },
  "coverage": "complete",
  "units": [
    {
      "id": "sorge/ga20/001",
      "locator": "heidegger-ga-20-...-commentary#h4-s-27-...",
      "primary_locator": "GA 20 § 27",
      "term": "Sorge",
      "status": "introduced",
      "claim": "One sentence: what is claimed there.",
      "quote": "Verbatim from the commentary."
    }
  ],
  "absences": [
    {
      "locator": "heidegger-ga-20-...-commentary#h4-s-19-...",
      "expected_because": "The analysis of being-in reaches the point where SZ introduces care, and stops.",
      "absent_terms": ["Sorge", "care"]
    }
  ]
}
```

Unit ids are stable. Re-extracting the same place reuses its id; a new
place takes the next number.
