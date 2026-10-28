---
name: key-passage-close-reading
description: "Writes close readings of selected key passages of a primary text, working from an existing paragraph-by-paragraph commentary and checked against the source. Use when asked to close-read, expand on, or examine the language and argument of particular paragraphs or passages of a work already commented on."
---

# Close Reading of Key Passages

## Core rules (read this block before every drafting pass, not just once)

1. **Only approved passages.** Read only the passages marked `approved` in the run's key-passage list (see "The key-passage list" below), or named by the user in the request. Never add one on your own; propose it in the list instead.
2. **The source is the evidence.** Quote from the source file and check every quoted word against it. Never quote the source through the commentary, and never repair a damaged passage from memory (see "Source integrity").
3. **One understanding per reading.** Name the term, concept or claim the passage rests on, and build the whole reading around it: how the wording develops it, what it does between the passage's neighbours, where it leads in the work and beyond. A point that does not bear on that understanding is cut, however true. A paragraph on vocabulary with no bearing on the argument fails, and so does a paragraph of argument that never touches the wording.
4. **Build on the commentary; don't restate it.** The unit's block in the main commentary already reconstructs the argument. Start from it, and add only what a close reading finds. Where the reading contradicts the block, say so and log the discrepancy (rule 6).
5. **Depth follows the passage.** No set length and no equal depth. A passage gets as much as its wording and argument support, and no more. The house style's ban on padding still applies.
6. **Never edit the main commentary in this run.** Log each error found in it under "Corrections to the commentary" in the key-passage list. Fixing it is a separate task.

## When to use this skill

Use this skill when asked to close-read, expand on, or "look closely at" particular paragraphs, block quotations or passages of a work that has a commentary under `commentaries/<author>/`. If the work has no commentary yet, say so and stop. The selection needs a commentary to come from, and so does the reading. For a paragraph-by-paragraph run, use [commentary-prompt](commentary-prompt.md). If the commentary has no key-passage list, because it was written before nominations existed, run "Backfill for existing commentaries" below first, or read only the passages the user names.

## Inputs to confirm at the start of a run

Confirm these only if not already clear from the request, the commentary or the list:

- **The commentary** (`commentaries/<author>/<file>`) and its citation system. The close readings use the same system.
- **The source file** in `faultynode/sources` that the commentary was keyed to. Confirm it is the same file and language version (see "Source integrity").
- **The passages**: the approved rows of `runs/<commentary-slug>-key-passages.md`, or the list given in the request. Add any given in the request to the list as `approved`, with criterion and reason.
- **The extent of each passage**: by default, the commentary's unit. A passage may run across two or three adjacent units when one step of the argument spans them, or narrow to a sentence or a block quotation within a unit. Record the extent in the list.

## The key-passage list

One file per commentary: `runs/<commentary-slug>-key-passages.md`. The commentary run creates it while nominating (see [commentary-prompt](commentary-prompt.md) §"Key-passage nominations"), or a backfill run creates it for an older commentary (see below). This run reads it and updates it. It is a working file and is not published as a commentary, so tables are fine in it.

```markdown
# Key passages: <work title>

Commentary: commentaries/<author>/<file>
Source: sources/<author>/<file>  (citation system; any caveat from sources/CLAUDE.md "Unsafe to quote")
Close readings: outputs/<commentary-slug>-close-readings.md

| # | citation | unit | opening (English) | criterion | reason | status |
|---|---|---|---|---|---|---|
| 1 | §7, GA 20 110–11 | 42 | "The matter itself is…" | b | the turn from method to being | approved |

## Corrections to the commentary

- <citation>: <what the block says>, <what the source says>, <line pointer>.
```

The criteria are those of the commentary prompt: **(a) term**, **(b) turn**, **(c) target**, **(d) wording**, **(e) edition**. The status is one of `nominated`, `approved`, `rejected`, `done` or `blocked`. Only the user moves a row from `nominated` to `approved` or `rejected`. This run sets `done` when a reading is written, and `blocked` when source damage stops a reading (give the reason in the row).

## Backfill for existing commentaries

A commentary written before the nomination hook has no key-passage list. A backfill run makes one. It is a run of its own: it ends with `nominated` rows and writes no close readings, because the user approves the rows first.

The finished commentary records criteria (a), (b), (c) and (e) well enough to nominate from. It is blind to (d) by design: the commentary prompt paraphrased away from the wording and cut every original the delete test did not keep. A backfill therefore runs in two stages. The commentary stage covers everything the commentary records. The source stage is a targeted search for wording, not a reread of the source.

**Stage 1: the commentary.** Grep the commentary's headings, then read it division by division, in order. Never load the whole file. For each block, look for:

- **(a) term**: the first discussion of a term of art, and any block that defines it, contrasts it with a neighbour or shifts its sense. Take the author's entries in `synthesis/lexicon.json` (each entry's `forms` and the `english` of its `renderings`) and grep the commentary for them. The first hit inside the work is a candidate, but check that the block actually discusses the term and does not merely use it.
- **(b) turn**: a block that states a thesis, reverses or restricts an earlier one, or that later blocks name as a step they depend on ("developed in §…", "on which the argument of §… rests").
- **(c) target**: a named opponent, a doctrine corrected, a phrase taken from another author.
- **(e) edition**: an edition or version difference the commentary folded in from the apparatus.
- **(d) traces**: original wording kept in parentheses beyond the run's glossary. By the repo's rule, such wording marks a place where the argument turns on the original. Coinage notes, and remarks on emphasis or etymology, are traces of the same kind.

**Stage 2: the source, for (d) only.** Run the source-integrity checks first, and record in the list header which markers the file cannot be trusted for (e.g. italics lost on the GA 20 text-layer pages). Then grep the source file for wording markers:

- emphasis: italic markup and spaced type;
- single terms in quotation marks;
- hyphenated coinages and nominalized infinitives;
- Greek, and Latin set off in the text;
- etymological and definitional phrasing: in German "heißt", "besagt", "bedeutet ursprünglich", "das Wort"; in French "signifie", "au sens propre", "le mot"; in English "literally", "the word";
- the names of other authors.

Group the hits by the commentary's units. Read the source by line range only where the hits cluster, or where a marker falls in a Stage 1 candidate. A marker alone is no nomination: nominate only where a close reading would turn on the wording, and say how in the reason. In a file the header marks unreliable for a marker, the absence of that marker is no evidence.

**Recording.** Use the list format above, with three backfill conventions:

- **Unit.** No segmentation list survives from the original run. Give the block's ordinal under its lowest heading ("§7.3" is the third block under §7), and say so once in the header.
- **Found by.** Start each reason with `commentary:`, `source:` or `both:`.
- **Order.** Append rows in the order of the work, division by division. Keep the strongest few per chapter or major division; drop the rest, even if they qualify. A merely difficult block does not qualify.

**Turns.** Work division by division and stop a turn only at the end of a major division. The list records how far the backfill has gone ("Backfill: through Part I"). Each turn presents the list, with a count of nominations per division and a note of anything Stage 2 could not search.

**Check before presenting.** Every row has a criterion and a found-by prefix. Every citation resolves to a block of the commentary. No row is marked `approved`.

## Task

Each reading follows **one understanding** that the passage carries: a term of art, a concept, or a claim. For example, what Heidegger means by "productive logic" in GA 20 §1, or what "decline" means in §2. The reading makes that understanding clear and shows how the passage builds it. It does not survey everything the passage contains. Choose the understanding first, before drafting. It is usually the one the row's criterion and reason name. If the passage seems to carry two, choose the one the later work depends on.

For each approved passage, in the order of the work, write one essay in this order.

1. **State the understanding.** Open with a short paragraph, before the quotation, that says what the author means by the term or claim. Say it plainly enough that the rest of the reading can be checked against it.
2. **Quote the passage in full**, in English, with the original (see "Quotation layout").
3. **Show how the language develops the understanding.** Attend only to the wording that builds this understanding:
   - which of the author's terms appears, and which is avoided;
   - pairs and oppositions of terms, and a word family carried through the passage;
   - morphology and coinage: hyphenation, prefixes, and etymology the author exploits or imposes;
   - syntax: what is subject, a conditional the commentary read as an assertion, the scope of a negation;
   - emphasis, and quotation marks that distance a term;
   - particles and connectives that claim more than the argument shows ("therefore", "first", "only");
   - borrowed wording, and what the context does to it.

   Mark where the inference is weaker than the wording makes it look.
4. **Place the passage in its context.** Show what comes before it and sets it up, and what comes after it and uses it. Say what the passage contributes to the author's argument at that point: why the argument needs this understanding here. Use the source for the neighbouring text and the commentary's units for orientation.
5. **Follow the understanding through the whole work.** Find where it returns, changes or is carried out later. A word that changes its subject, a promise redeemed, a thesis hedged on its return. Cite those places by § and page.
6. **Connect it to the author's other works** where that adds to the understanding: an earlier formulation, a later hardening, a revision. Draw these only from files in the sources repo, read by line range, and cite them by the volume's own pagination (Gesamtausgabe page, "SZ n", and so on). Where a commentary in this repo covers the work, its citation system governs. Never cite another work from memory. If the corpus cannot confirm a connection, leave it out. One or two connections that change how the passage reads are better than a survey.
7. **Compare translations** only when a published translation is in the corpus and departs from the original in a way that changes the understanding. Name the translation. Never cite a translation from memory.

The reading should read as one argument from the opening paragraph to the last. Each paragraph advances the understanding, and the last paragraph says where it ends up. Typical length is 900 to 1,300 words. A passage that carries less gets less.

Audience: graduate-level familiarity with the author and the tradition, the same as the main commentary.

## Quotation layout

Close reading is the case where the original earns its place. The standing rule in the [root CLAUDE.md](../CLAUDE.md) still governs: English first, every quotation translated. Within it:

- **The passage quotation.** Give the whole passage in English as a block quotation. Follow it with the original as a second block quotation, introduced by a plain line naming the language ("German:"). Keep the source's emphasis. The English is your working rendering: say so once, in the foreword, and translate closely enough to show the structure you will discuss. This is the one place where a close rendering beats idiomatic paraphrase.
- **Words and phrases in the discussion.** English first, the original in parentheses: "the matter itself (*die Sache selbst*)". Repeats in the same reading may give the original alone once it is glossed.
- **The delete test still applies**, word by word. Keep the original wherever the reading turns on it, which here is often. Cut it where it adds nothing to the English.
- No bracketed original-language incipits.

If the source is in English, quote it once as a block quotation. Discuss its wording directly, and do not set its vocabulary equal to the original's (see the sources repo `CLAUDE.md`, "Always translate quotations").

## Source integrity

A paraphrase survives small conversion damage; a close reading does not. Before reading any passage:

- **Check the "Unsafe to quote" table** in the sources repo `CLAUDE.md`, and the file's entry in `docs/corpus-map.md`. Locate the sources checkout first.
- **Confirm the version.** Many works exist in two or three languages and in `-a`/`-b`/`-c` conversions. Confirm the file is the one the commentary was keyed to. A pointer into one version does not resolve in another.
- **Read the passage from the file**, by line range, and copy the original from there.
- **Emphasis.** Where the file is known to have lost italics (e.g. the GA 20 pages taken from the text layer), do not argue from emphasis or its absence. Say the file cannot settle it.
- **Damage.** OCR errors, spliced seams, missing pages or garbled Greek: correct an obvious misspelling of a name or term silently, as the commentary prompt allows. Never repair wording the reading depends on. Quote what the file has, mark the problem in a note at that point, and say what the reading would need. If damage stops the reading, set the row to `blocked` and move on.
- **Line pointers.** Give the source file's `file:line` for each passage quotation in the key-passage list row, not in the published text. Where the corpus map says line pointers are stale (a re-converted file), re-find the passage by its wording.

## Form

- **Output file:** one file per commentary, `outputs/<commentary-slug>-close-readings.md`, appended to in the order of the work. It sits outside `commentaries/` on purpose. That folder is swept by the WordPress sync, the synthesis corpus and the filename normalizer, all of which assume one paragraph-by-paragraph commentary per file.
- **Frontmatter** as for commentaries: `layout: default` and a `title`. Quote the title in YAML if it contains a colon.
- **H1**: "<Author>, *<Work>*: close readings of key passages".
- **Foreword**, in prose: the source file and edition, the citation system, a link to the main commentary, a statement that translations are working renderings, and any source caveat that affects more than one reading.
- **One H2 per passage.** Its heading is the citation and a short English title naming the understanding: "§1, GA 20 2–3: productive logic". These headings are the file's own, unlike the commentary, which reproduces only the author's divisions. Under each heading, the first line links to the commentary unit it reads. The opening paragraph that states the understanding follows it, and the quotation comes after that paragraph.
- **Notes on the text.** Where the source is damaged at the passage, put an italic "*Note on the text.*" paragraph directly after the quotation. Say what the file has, what the reading needs, and what is left out.
- **Prose only** inside a reading, with no bullets or lists. The house style of [commentary-prompt](commentary-prompt.md) applies in full. Lead with the insight, prefer finite verbs, and avoid meta-scaffolding ("What is striking here is…", "Let us look closely at…"). A close reading invites narrating the reading. Write what the wording does, not that you are looking at it.

## Post-draft verification checklist (mandatory, before presenting)

- [ ] Every passage read is `approved` in the list, and each is now `done` or `blocked`.
- [ ] Every quoted word of the original matches the source file at the recorded line range, emphasis included.
- [ ] Every quotation has an English rendering, and every glossed term is glossed on first use in this file.
- [ ] The delete test is applied to each original-language word in the discussion.
- [ ] No reading restates its commentary block without adding to it. Cut any sentence the block already says.
- [ ] Each reading names its understanding in the opening paragraph, and every later paragraph advances that understanding. Cut any paragraph that does not.
- [ ] The reading places the passage between what comes before and after it, and says what it contributes to the argument there.
- [ ] Every connection to another part of the work or another work is cited by § and page, and every connection to another work was read in a corpus file, not supplied from memory.
- [ ] Every point about wording is tied to the argument, and every point about the argument cites the wording that carries it.
- [ ] Each disagreement with the main commentary is logged under "Corrections to the commentary".
- [ ] No claim rests on emphasis or wording the "Source integrity" checks marked unreliable.

## Workflow per turn

1. Read the key-passage list. Take the next approved passages in the order of the work.
2. Run the source-integrity checks for the source file, once per run, and record any caveat in the list header.
3. For each passage, read the commentary's block for it, then the source by line range, including the paragraphs on either side.
4. Name the understanding the reading will follow. Grep the source for where its key words return later in the work, and grep the author's other files in the corpus for earlier or later formulations. Read the hits by line range.
5. Draft the reading in the order the Task section sets: the understanding, the quotation, the language, the context, the whole work, other works.
6. Append to the close-readings file, creating it with its frontmatter and foreword on first use.
7. Run the verification checklist. Update each row's status and line pointer, and log any corrections.
8. Present the updated close-readings file and list. If the turn stopped short of the approved list, say where, then await "continue".
