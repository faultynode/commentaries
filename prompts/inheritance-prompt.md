# Inheritance prompt — Stage 3

One pass, one commentary, no theme. Produces
`synthesis/inheritance/<commentary-slug>.json`.

## ROLE

A separate pass over the same commentaries asking a different question:
where does the author engage a predecessor, and how. The classification
is what turns a citation list into a genealogy; without it this is a
bibliography.

## HARD RULES

Stage 1's rules hold unchanged — no interpretation, verbatim quotes
inside the located section, the commentary is the only corpus, absences
are claims. Two more apply here:

- **Name the predecessor text only where the commentary identifies it.**
  If the commentary says "Aristotle" and not which treatise, record the
  author and omit `text`. Supplying the work from your own knowledge is
  the failure this pass exists to avoid.
- **The mode is a judgement about the commentary's report,** not about
  the philosophical relation. If the commentary describes Heidegger
  taking a distinction over without attribution, that is
  `silent-appropriation` in the commentary's account. Do not correct it
  from outside.

## MODES

- `acknowledged-debt` — the predecessor is named and credited.
- `silent-appropriation` — a distinction or move is taken over without
  attribution, and the commentary says so.
- `polemical-rejection` — the predecessor's position is named and
  refused.
- `terminological-borrowing` — the word is taken, the sense altered.
  Record the altered sense in `claim`; that is the interesting half.
- `destructive-appropriation` — the concept is taken over and its
  received sense dismantled in the same move. A local addition for
  Destruktion, which neither rejection nor borrowing describes. Use it
  only where the commentary presents both halves; where it presents one,
  use the mode for that half.

## PROCEDURE

Predecessor names are the retrieval key, so query by term rather than by
theme:

    python3 scripts/synthesis_query.py \
        --terms "Aristotle,Descartes,Kant,Brentano,Natorp,Husserl" \
        --commentary <slug> --sections --top 40

Then read those sections, write the record against
`synthesis/schema/inheritance.schema.json`, and validate:

    python3 scripts/synthesis_validate.py

Dense returns are expected where the commentary is itself an exercise in
reading a predecessor — Aristotle in GA 18 and GA 19, Descartes in the
Cartesian Meditations commentary, Brentano and Natorp wherever the
Marburg setting is being fixed. Density is not significance: a course
that cites Aristotle on every page may take nothing from him that it
does not also refuse.

## SHAPE OF THE OUTPUT

```json
{
  "schema_version": 1,
  "commentary": "heidegger-ga-19-platon-sophistes-commentary",
  "source_sha256": "<64 hex>",
  "extracted_at": "YYYY-MM-DD",
  "extractor": { "agent": "<model or person>", "prompt": "prompts/inheritance-prompt.md" },
  "coverage": "partial",
  "coverage_note": "Preliminary Considerations only.",
  "engagements": [
    {
      "id": "inh/ga19/001",
      "locator": "heidegger-ga-19-platon-sophistes-commentary#h5-b-...",
      "primary_locator": "GA 19 § 2",
      "predecessor": { "author": "Aristotle" },
      "mode": "acknowledged-debt",
      "claim": "One sentence: what is taken, refused, or renamed.",
      "quote": "Verbatim from the commentary."
    }
  ]
}
```
