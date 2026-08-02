---
name: paragraph-by-paragraph-philosophical-commentary
description: "Writes an exhaustive, unit-by-unit commentary on a primary text as one growing markdown file. Use whenever asked to comment on, work through, or continue a commentary on a philosophical work."
---

# Paragraph-by-Paragraph Philosophical Commentary

## Core rules (read this block before every drafting pass, not just once)

These are the rules most at risk of being silently dropped as source text and prior commentary accumulate in context. Re-read this block immediately before drafting each new unit, not just at the start of the run.

1. **Never skip or merge a unit.** Every native unit (paragraph, proposition, definition, aphorism, dialectical move) gets its own full commentary block, at equal depth, however minor or transitional it looks. Merging two units into one block is a rule violation, not an acceptable compression.
2. **Segment and count before drafting.** Number every native unit in the range before writing any commentary prose for it. Draft against that fixed numbered list, not against a re-skim of the raw source.
3. **Reconcile after drafting.** Before running style passes, count the drafted commentary blocks and check the count against the fixed unit count from step 2. Expand any block that covers more than one unit.
4. **One file, clean boundaries only.** Append everything to a single `<ShortTitle>_Commentary.md`. Stop a turn only at a clean structural boundary — never mid-unit. Prefer stopping earlier at a smaller boundary over compressing units to cover more ground.
5. **State the insight; do not narrate the reading or re-gloss a point already made.** See House style below for the full list of banned scaffolding.

If a turn's context is getting long (large source range, long prior commentary already in the file), treat that as a signal to re-check rules 1–3 more often, not less — length is exactly the condition under which silent merging happens.

## When to use this skill

Trigger this skill whenever the request involves writing, running, or continuing a sustained commentary on a primary philosophical (or comparable primary-source) text — phrasing like "comment on," "work through," "commentary on [work]," "paragraph-by-paragraph," or "continue the commentary."

## Inputs to confirm at the start of a run

Confirm these only if not already clear from the request or the file itself — don't stall on a question if the answer is inferable:

- **Source file / passage** and its location.
- **Target work and the range** to cover (whole work, or specified Parts/sections).
- **Original language** (sets whether the translation + retained-term layer applies).
- **Native structural unit** (sets the unit of commentary) and the **citation system**.

Absent other instruction, proceed on the defaults below: adaptive unit; original-language terms held to a fixed glossary, otherwise rendered in idiomatic English; headings translated; equal-depth/no-skipping; prose-only concise house style; a single growing file, ending each turn only at a clean structural boundary; meaning-bearing notes folded in; misreading-guards derived from the text itself.

## Task

Work through the **main text** of the target work, from beginning to end, treating **every native unit of the text, in order, one at a time.** For each unit:

- Reconstruct the argument **in your own words**.
- Identify the key philosophical moves and distinctions.
- Note connections to earlier passages in the work and to the broader project of the author.

Audience: graduate-level familiarity with the author and the tradition.

**Work end-to-end and autonomously, producing a single markdown file.** Append all commentary to one file (`<ShortTitle>_Commentary.md`) rather than splitting across multiple files. If the work is short enough to finish in one turn, deliver the whole commentary as that one file. If it is too long to complete in a single turn, write as much as the turn allows — always stopping at a clean structural boundary — then append the continuation to the *same* file on each subsequent turn, re-presenting the one growing file. Await "continue" only when a turn's output limit forces a stop; never pause for input mid-work for any other reason. The goal is the fewest files possible — one whenever achievable.

## Adaptive unit of commentary

Before starting, identify the text's **native structural unit** and make that the unit of commentary. Do not force a paragraph grid onto a text that isn't built that way. Typical cases:

- **Continuous treatise with paragraphs** (e.g. Husserl, Kant's prose, most modern monographs) → the typographically distinct **paragraph**.
- **Numbered propositions** (e.g. *Tractatus*) → each **numbered proposition**, at its own level.
- **Geometric order** (e.g. Spinoza's *Ethics*) → each **definition, axiom, proposition, demonstration, corollary, and scholium** as its own unit.
- **Aphoristic works** (e.g. Nietzsche, Wittgenstein's *Investigations*, Pascal) → each **aphorism / numbered remark / fragment**.
- **Dialogues** (e.g. Plato) → work through the argument in **Stephanus-keyed chunks** that track the dialectical moves, treating each distinct move/exchange as a unit.
- **Lecture courses / unparagraphed treatises** → segment into the smallest coherent argumentative steps and treat each as a unit.

Whatever the unit, the rule below holds: treat **every** unit, at **equal depth**, in order.

## Unit segmentation and pre-count (mandatory, before drafting)

Long-context drafting has a known failure mode: as more source material and prior commentary accumulate in context, models silently compress — quietly folding two or three native units into a single commentary block to conserve effort, without ever being told to do so. This is the single largest cause of quality loss in this skill and must be actively engineered against, not left to instruction-following alone.

Before writing any commentary prose for a new range, perform this segmentation step explicitly:

1. **Extract and number every native unit** in the range about to be covered (e.g., every typographically distinct paragraph, every numbered proposition, every definition/axiom/proposition/scholium). Produce a plain numbered list of unit openings (first few words of each) as a scratch artifact — this is bookkeeping, not part of the delivered commentary.
2. **Fix the unit count** for the range (e.g., "this section contains 14 paragraphs, numbered 1–14") before drafting a single sentence of commentary.
3. Draft commentary **unit by unit against that fixed list**, never against a re-skim of the raw source. If a unit seems minor or transitional, it still gets its own numbered slot and its own full treatment — do not let apparent thinness justify silent merging.
4. If the source's own paragraphing is ambiguous (e.g., run-on OCR text, inconsistent line breaks), resolve the ambiguity at segmentation time and commit to a unit count, rather than deciding paragraph boundaries impressionistically while drafting.

Never skip this step to save time under a tight turn budget — skipping it is exactly what produces the merged-unit compression this section exists to prevent.

## Coverage rule (equal depth, no skipping)

Explain **every** unit at **equal depth**. Never summarize, compress, or skip a unit, however transitional or minor it seems. Each gets its own full treatment in its own words. (This restates rule 1 in Core rules above — re-check it here, immediately before drafting, not only at the top of the file.)

## Post-draft verification checklist (mandatory, before presenting)

Run this as a discrete, mechanical check — not a general impression — after drafting a section and before the clarity/concision passes below:

- [ ] Fixed unit count from segmentation step: ___
- [ ] Number of distinct commentary blocks actually drafted: ___
- [ ] Do the two numbers match? If not, identify exactly which unit(s) were merged or dropped and split them back out.
- [ ] Does any single commentary block visibly discuss the content of two or more numbered units? If so, expand it — even if the section runs longer or the turn must stop sooner at the boundary.
- [ ] Only once the counts reconcile exactly, proceed to the monolingual clarity pass and concision-and-insight pass.

This check is cheap and mechanical (a count comparison), which is precisely why it catches the failure mode reliably where a general instruction to "not skip units" does not — it converts an implicit norm into an explicit, checkable step.

## Headings

Reproduce the work's own structural divisions (Parts, Books, Chapters, numbered §§, lettered subsections, and the like) as headings, mirroring the text's *actual nesting depth* — not a fixed number of levels.

- Map each level of the work's division hierarchy to a successive heading level, in order, starting at **H2** for the outermost division you reproduce (reserve **H1** for the commentary's own title, if any).
- Descend one heading level per level of nesting. A four-level work (e.g. a lecture course: Part → Chapter → § → lettered subsection a/b/c) becomes H2 → H3 → H4 → H5; a two-level treatise (Part → Chapter, or Chapter → §) becomes H2 → H3; a work divided only into §§ uses H2.
- If a work nests deeper than H6 allows (rare), fold the deepest divisions into bold plain-text lead-ins rather than inventing a seventh level. Reproduce **only** the divisions the author or critical editor actually wrote — do not invent structure or insert your own subheadings. If the source is **not in English**, **translate the headings into English.** The commentary's own units (the paragraphs, propositions, or argumentative steps below the lowest division) carry **no** headings of their own; a light plain-text lead-in identifying the unit ("Husserl states that…", "Proposition 7 asserts…") is fine.

## Original-language terms and quotations

If the source is not in English (the default assumption for primary-source work):

- Retain the original language only for a short, fixed glossary of genuinely untranslatable terms of art (see Translating into idiomatic English below), giving the English on first use (e.g., Dasein — being-there). Cite any other source word in parentheses after its English equivalent, never as the inline subject.
- Translate ordinary prose into clear English in your own words.

If the source **is** in English, retain the author's own technical vocabulary verbatim (do not paraphrase away the terms of art), but no translation layer is needed.

In all cases:

- **Do not** prefix each unit with its opening line in the original language in brackets. **No bracketed original-language incipits anywhere.**
- Correct obvious OCR/transcription corruptions of proper names and terms silently (see OCR block below).

## Footnotes / apparatus

Footnotes, marginalia, or critical-apparatus notes that **substantially bear on the meaning** of a unit → fold their content into the commentary on that unit. Otherwise omit them. (Examples of meaning-bearing notes: an author's reference settling which doctrine he is correcting; a polemical note identifying a target; a cross-reference that fixes a term's sense.)

## House style (fixed defaults — all apply)

- **Concise to the point of pressure.** Every sentence must earn its place. Prefer the shortest formulation that keeps the argument's rigour. Short, direct sentences; avoid multi-clause pile-ups. If a sentence can be cut without loss of content, cut it.
- **State the insight; do not narrate the reading.** Ban meta-scaffolding that describes what the commentary is doing instead of doing it: "The point of method is that…", "The reformulation is characteristic…", "Two things are doing work here…", "The rhetorical structure is deliberate…", "What is doing the work is…", "Already here we see…", "This is the first enactment of…". Say the thing directly. If Heidegger subordinates a thesis, write that he subordinates it and why it matters — not that "the rhetorical structure is deliberate."
- **One pass per point, not two.** Do not state a claim and then re-gloss it in a following sentence that adds no new content. The commentary explains the text once, at depth; it does not explain, then explain its own explanation. Reserve a second sentence only for a genuinely new move (a consequence, a connection, a guarded distinction).
- **Land insight, don't pad toward it.** The value of a unit's commentary is the non-obvious move it surfaces — the distinction the text turns on, the target it is correcting, the later doctrine it seeds. Lead with that. Cut throat-clearing ("It is worth noting that", "Here Heidegger", "We should observe") and the restatement of what the paraphrase already made plain.
- **Prefer the finite verb to the nominalization.** "Descartes converts truth into certainty," not "there is a conversion of truth into certainty on Descartes' part." Kill hedge-nominalizations ("the demotion of", "a stripping-away of", "the pairing is methodologically loaded") in favour of a subject doing something.
- **Use italics sparingly** — mainly for first-use original-language technical terms. Not for general emphasis.
- **No italic summary-of-work blocks** at the start or end of a file.
- **Prose only.** No bullet points, numbered lists, headers beyond the H2/H3 scheme, or excessive bolding inside the commentary body.
- Spell out proper names correctly even where the source corrupts them.

## Translating into idiomatic English (when the source is not in English)

The commentary must read as English written by someone who understands the argument — not as a transposition of the original's syntax. These are fixed defaults; all apply.

- **Idiomatic English first.** Re-express each unit's argument in natural, grammatical English. Do not mirror the source's voice, word order, or preposition government. If a literal rendering would be ungrammatical or opaque, paraphrase for sense. Fidelity is owed to the argumentative moves and the matters at issue, not to the surface form. It is fine not to follow the author's expressions verbatim if you convey the meaning or disclose the strategy behind them.
- **Restate, don't transpose.** Read the unit in the original, then look away and state its point in your own words; only then check back against the text. Never translate clause-by-clause from the source on screen — that is what produces calque ("translationese").
- **Tighten term-retention.** Keep the original language only for a short, fixed glossary of genuinely untranslatable terms of art (for Heidegger: Dasein, Sorge, Existenz, Ereignis, and the like). For everything else choose one clear English equivalent and use it consistently. Never leave a common source-language noun inline in an English sentence; if you cite the original word, put it in parentheses after its English equivalent, not as the running subject of the clause.
- **Unpack coinages in two steps.** When the author coins or hyphenates a word (Sich-mit-haben, Sehenlassen, Tagsein, In-der-Welt-sein): (a) say in plain English what it picks out, and (b) if the coinage carries philosophical weight, add a short, clearly-marked note on the morphological strategy (the hyphenation, the etymological play). Never substitute an English non-word ("being-day," "having-itself-along") for the meaning.
- **Kill the standard calque patterns.** Convert passives and nominalizations to active voice and finite verbs; replace preposition-for-preposition mappings with the idiomatic English collocation; render reflexives and causatives by their sense, not their form (German *X lässt sehen* → "X makes visible," not "lets see"; *charakterisiert sich als* → "shows up as," not "characterizes itself as"); and drop or absorb flavouring particles rather than translating each (*jeweilig, zunächst, durchaus, eigentlich, bestimmt*).
- **Monolingual clarity pass.** After drafting each section, reread it as a reader who knows no source language. Flag any sentence that is ungrammatical, has a dangling preposition, or cannot be understood without the original, and rewrite it before continuing. Test of success: graduate-level rigour, but every sentence followable by a reader with no knowledge of the source language. (For high-stakes runs, do this pass with a separate verification agent.)
- **Concision-and-insight pass.** On the same reread, apply two more tests to each paragraph. (a) *Cut test:* can any sentence be deleted with no loss of argumentative content? If so, delete it — this catches the second-gloss restatements and the meta-scaffolding banned in House style. (b) *Insight test:* does the paragraph surface the non-obvious move the unit turns on (the distinction, the target being corrected, the doctrine being seeded), or does it merely restate the paraphrase in commentary register? If the latter, rewrite so the load-bearing point leads. A unit's commentary should be shorter and sharper after this pass, never longer.

## File segmentation (single growing file)

- Use **one** file for the entire commentary: `<ShortTitle>_Commentary.md`. Save it to this project's designated output folder (in Cowork, the folder shared with the project; in standard Claude chat, `/mnt/user-data/outputs/`).
- Append to it continuously. Within a turn, write as much as the output limit allows, then **stop at a clean structural boundary** (the end of a §, proposition, chapter, or other native division) — **never mid-unit and never mid-section.**
- If a section spills past the page range already read, read forward and complete that section before stopping, so the file always ends a turn at a clean boundary.
- On each subsequent turn, **append** to the same file (do not create a new file), then re-present the one growing file. The result is a single document, however many turns it takes to finish.
- Prefer stopping a turn **earlier**, at a smaller clean boundary, over pushing through a larger range by compressing units to fit — the segmentation and verification steps above take priority over turn-level coverage speed.

## Workflow per turn

1. Read the source for the next range (`pdftotext …`).
2. **Segment and pre-count** the native units in that range per "Unit segmentation and pre-count" above, before drafting.
3. Look away and restate each unit's point in your own words before drafting — never translate clause-by-clause from the on-screen source.
4. For headings or unclear pages, rasterize with `pdftoppm …` and view the image.
5. Append the new commentary to the working copy of `<ShortTitle>_Commentary.md` (recreate from the saved version first if missing), drafting one commentary block per numbered unit.
6. End the turn at a clean structural boundary (complete any spilled-over section first).
7. **Run the post-draft verification checklist**: reconcile the drafted block count against the fixed unit count and expand any collapsed unit.
8. Run the monolingual clarity pass and the concision-and-insight pass on the new section.
9. Copy the updated file to the output folder and present it.
10. Give a brief plain stopping-point note in chat only if the output limit forced the stop, then await "continue."

---

## Reference material (consult only when the situation applies; not needed on every turn)

The sections below are conditional — they matter only for specific source types or situations (OCR'd scans, non-standard citation systems, tracking interpretive traps across a long run). They do not need to be re-read on every drafting pass the way the Core rules block does.

### OCR / scan-artifact handling (apply only if the source needs it)

If the source is an OCR'd or scanned document, expect and silently correct artifacts: spaced-letter emphasis ("W a h r n e h m u n g"), broken or doubled quotation marks, mangled diacritics (ß, umlauts, accents), and corrupted proper names (e.g. an author's name garbled the same way throughout). **Watch for facing-page duplication**: some scans repeat each two-page span via a form-feed — read each span once and ignore the immediate repeat. If the source is clean (born-digital PDF, EPUB, plain text), ignore this block.

### Citation / pagination

Identify the work's **standard scholarly citation system** and use it throughout: marginal critical-edition pagination (e.g. Husserliana, Akademie-Ausgabe), Stephanus numbers (Plato), Bekker numbers (Aristotle), proposition numbers (*Tractatus*, *Ethics*), or the author's own section numbers. If the critical pagination is printed in the margins of the source, treat it as the citation standard and **map it to the source's physical pages empirically** — the offset between citation page and physical page often drifts across a volume, so re-anchor by searching forward from the last confirmed landmark and confirm headings by rasterizing rather than trusting a fixed offset.

### Interpretive conventions to keep steady

- **Track the characteristic misreadings of this particular text.** At the outset, identify the standard traps and conflations that beset the work (the distinctions readers habitually collapse, the terms that get assimilated to a neighboring doctrine), state them briefly, and guard against them consistently across all files. (For *Ideen I* these were, e.g., transcendental ≠ Berkeleyan idealism, constitution ≠ causation, noema ≠ mental image, evidence ≠ a feeling. Every text has its own set — derive them from the text and its reception.)
- **Flag forward- and backward-connections** as they arise: when a unit introduces a term, distinction, or thesis that the work develops later, or relies on one established earlier, say so. Where relevant, point to the author's other works that take up the same theme.
- Keep terminology, transliteration, and cross-reference conventions **uniform** across the whole run.
