# Stage 5: a quoting article from a Stage 4 draft

Stage 4 writes from the ledgers and may open nothing else, so every
quotation it carries is a quotation of a commentary — English prose that
paraphrases Husserl closely and is not his words. That is what makes a
draft checkable, and it is why a draft narrates where it ought to quote.

Stage 5 is the one pass allowed to open `sources/`. It takes a finished
Stage 4 draft and re-voices it against the primary texts: the same
argument, in continuous prose, with the texts speaking in their own
language where the corpus holds them.

## The seam, and the rule that guards it

Opening the primary text is a real loosening of the discipline the rest
of the pipeline runs on, so it comes with one restriction that is not
negotiable:

> A Stage 5 pass may **substantiate** a claim the ledger already
> carries. It may never **add** one.

If a passage says something the ledger does not, that is a Stage 1
extraction task. Note it in the register and leave it out of the prose.
An article that argues from what a Stage 5 pass happened to notice while
reading around has stopped being anchored to the ledger and has quietly
become a fourth thing nobody validated.

Rule 1 of `synthesis/CLAUDE.md` holds here with more force than
anywhere: **copy quotes out of the file, never retype one.** The
machinery enforces it — `scripts/synthesis_dossier.py fill` slices the
passage off disk between two anchors you supply, so the recorded quote
is disk text and a wrong anchor fails loudly instead of quietly.

## 1. Build the dossier

    python scripts/synthesis_dossier.py build synthesis/outputs/<slug>.md

One entry per unit id the draft cites, carrying the commentary-tier
evidence the ledger already validated and an empty `primary` slot.

## 2. Fill it, one text at a time

Work through the entries in dossier order — that is the order the
argument runs in, so you stay in one volume at a time. For each, find
the passage the commentary was reporting and write an anchor spec to
`synthesis/dossiers/specs/<slug>-<author>.json`:

    {"id": "...", "side": "original", "language": "de",
     "file": "heidegger/heidegger-ga-24-die-grundprobleme....md",
     "line": 950, "from": "Die Intentionalität ist die ratio",
     "to": "in ihren verschiedenen Weisen."}

Record `original` and, where the corpus holds one, `translation`. Then:

    python scripts/synthesis_dossier.py fill <slug> <spec>
    python scripts/synthesis_dossier.py check <slug>

`check` must print OK before any prose is written.

Where nothing can be found, say which kind of nothing it is — the
distinction decides whether anyone can do something about it:

- `not-in-corpus` — the text exists, `sources/` has no copy. This is an
  acquisition list, and `status` prints it as one.
- `no-primary` — there is nothing to find, because the claim is the
  commentator's own gloss or reconstruction. No volume will fix it.

Both are results. Neither is a failure, and neither licenses quoting
something else instead.

## 3. Write

Follow `prompts/article-prompt.md` for ROLE, ARGUMENT, FORM and the
Research Register, with these overrides.

**Do not re-argue.** The thesis, its sequence and its concessions were
settled at Stage 4 against 600-odd units. Stage 5 changes the voice, not
the claim. Where a primary passage genuinely embarrasses a step of the
draft, do not quietly repair it: say so in the prose and record it in
the register. That is the most valuable thing this stage produces.

**Three tiers, visible in the sentence.** The draft kept its tiers apart
by citing unit ids. Prose cannot do that without becoming unreadable, so
the tier has to show in how the sentence is built:

- *Primary.* Quote it, original first, translation after, with the
  archive line pointer. Only for a dossier entry in state `found`.
- *Commentary.* "The commentary records him as holding…" — never a bare
  "Husserl says" over a `no-source` entry, and never a quotation.
- *Yours.* Carries nothing, and borrows the authority of neither.

**Cite by the handles the texts supply** — Husserliana and GA section
numbers, `§` numbers for *Sein und Zeit* — plus the archive's own line
pointer in the form `GA 24:950`. These pointers are not pagination and
will drift when a file is re-converted; they are given so a reader can
check the claim against the same text you checked it against. Say so
once, in a note on citation, as
`articles/heidegger-husserl-intentionality-article.md` does.

**Say which edition spoke.** Where the archive holds a translation
rather than an original, name it at the point of use. In an argument
about what a word does, whose English it is stops being a pedantry: GA
17's `jedes Urteil, jedes Wollen, jedes Lieben` and a commentary's
"every willing, loving, hating" are not the same claim.

## 4. Output

`articles/<topic>-article.md`, with the frontmatter and slug rules in
`prompts/article-prompt.md`. Articles are published; `synthesis/` is
not, and the draft stays where it is.

Append to the Research Register, after the four sections
`article-prompt.md` specifies:

5. **What the primary texts changed.** Every place a passage narrowed,
   widened or embarrassed a claim the draft made from the commentary
   alone — with both wordings.
6. **What could not be raised.** The `not-in-corpus` list, as an
   acquisition queue, and the `no-primary` list, as the claims that stay
   at commentary tier whatever arrives.
