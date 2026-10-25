---
name: key-passage-close-reading
description: "Writes close readings of selected key passages of a primary text, working from an existing paragraph-by-paragraph commentary and checked against the source. Use when asked to close-read, expand on, or examine the language and argument of particular paragraphs or passages of a work already commented on."
---

# Close Reading of Key Passages

## Core rules (read this block before every drafting pass, not just once)

1. **Only approved passages.** Read only the passages marked `approved` in the run's key-passage list (see "The key-passage list" below), or named by the user in the request. Never add one on your own; propose it in the list instead.
2. **The source is the evidence.** Quote from the source file and check every quoted word against it. Never quote the source through the commentary, and never repair a damaged passage from memory (see "Source integrity").
3. **Wording and argument together.** A close reading shows how the wording carries the argument. A paragraph on vocabulary with no bearing on the argument fails, and so does a paragraph of argument that never touches the wording.
4. **Build on the commentary; don't restate it.** The unit's block in the main commentary already reconstructs the argument. Start from it, and add only what a close reading finds. Where the reading contradicts the block, say so and log the discrepancy (rule 6).
5. **Depth follows the passage.** No set length and no equal depth. A passage gets as much as its wording and argument support, and no more. The house style's ban on padding still applies.
6. **Never edit the main commentary in this run.** Log each error found in it under "Corrections to the commentary" in the key-passage list. Fixing it is a separate task.

## When to use this skill

Use this skill when asked to close-read, expand on, or "look closely at" particular paragraphs, block quotations or passages of a work that has a commentary under `commentaries/<author>/`. If the work has no commentary yet, say so and stop. The selection needs a commentary to come from, and so does the reading. For a paragraph-by-paragraph run, use [commentary-prompt](commentary-prompt.md).

## Inputs to confirm at the start of a run

Confirm these only if not already clear from the request, the commentary or the list:

- **The commentary** (`commentaries/<author>/<file>`) and its citation system. The close readings use the same system.
- **The source file** in `faultynode/sources` that the commentary was keyed to. Confirm it is the same file and language version (see "Source integrity").
- **The passages**: the approved rows of `runs/<commentary-slug>-key-passages.md`, or the list given in the request. Add any given in the request to the list as `approved`, with criterion and reason.
- **The extent of each passage**: by default, the commentary's unit. A passage may run across two or three adjacent units when one step of the argument spans them, or narrow to a sentence or a block quotation within a unit. Record the extent in the list.

## The key-passage list

One file per commentary: `runs/<commentary-slug>-key-passages.md`. The commentary run creates it while nominating (see [commentary-prompt](commentary-prompt.md) §"Key-passage nominations"); this run reads it and updates it. It is a working file and is not published as a commentary, so tables are fine in it.

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

## Task

For each approved passage, in the order of the work:

1. **Quote the passage in full**, in English, with the original (see "Quotation layout").
2. **Read the wording.** Attend to whatever does work in this passage, and only that:
   - choice of word: which of the author's available terms appears, and which is avoided; a term used in a sense different from its sense elsewhere in the work;
   - morphology and coinage: hyphenation, nominalized infinitives, prefixes, etymology the author exploits or imposes;
   - syntax: what is subject and what is predicate, active against passive, reflexives, modal verbs, the scope of a negation, a conditional the main commentary read as an assertion;
   - emphasis and punctuation: italics, spaced type, quotation marks that distance a term, dashes and parentheses that hold a thought in suspension;
   - particles and connectives: what "therefore", "but", "already", "precisely" claim, where the commentary prompt's translation rules dropped them;
   - borrowed wording: the phrase from another author, and what the context does to it.
3. **Read the argument.** State the step the passage makes, what it takes as given, what it rules out, and what it makes possible later in the work. Mark where the inference is weaker than the wording suggests.
4. **Join the two.** Say how the wording does the argumentative work: where a word choice makes the step look necessary, or where a syntactic choice hides an assumption.
5. **Place the passage.** Name its forward and backward connections inside the work, using the commentary's cross-references, and to the author's other works where a commentary in this repo covers them. Cite those by their commentary's citation system.
6. **Compare translations** only when a published translation is in the corpus and departs from the original in a way that changes the argument. Name the translation and its file. Never cite a translation from memory.

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
- **One H2 per passage.** Its heading is the citation and a short English title of what the passage does: "§7, GA 20 110–11: the matter itself as a question of being". These headings are the file's own, unlike the commentary, which reproduces only the author's divisions. Under each heading, the first line links to the commentary unit it reads.
- **Prose only** inside a reading, with no bullets or lists. The house style of [commentary-prompt](commentary-prompt.md) applies in full. Lead with the insight, prefer finite verbs, and avoid meta-scaffolding ("What is striking here is…", "Let us look closely at…"). A close reading invites narrating the reading. Write what the wording does, not that you are looking at it.

## Post-draft verification checklist (mandatory, before presenting)

- [ ] Every passage read is `approved` in the list, and each is now `done` or `blocked`.
- [ ] Every quoted word of the original matches the source file at the recorded line range, emphasis included.
- [ ] Every quotation has an English rendering, and every glossed term is glossed on first use in this file.
- [ ] The delete test is applied to each original-language word in the discussion.
- [ ] No reading restates its commentary block without adding to it. Cut any sentence the block already says.
- [ ] Every point about wording is tied to the argument, and every point about the argument cites the wording that carries it.
- [ ] Each disagreement with the main commentary is logged under "Corrections to the commentary".
- [ ] No claim rests on emphasis or wording the "Source integrity" checks marked unreliable.

## Workflow per turn

1. Read the key-passage list. Take the next approved passages in the order of the work.
2. Run the source-integrity checks for the source file, once per run, and record any caveat in the list header.
3. For each passage, read the commentary's block for it, then the source by line range, including enough context on either side to see the step.
4. Draft the reading: quotation, wording, argument, how the two join, placement.
5. Append to the close-readings file, creating it with its frontmatter and foreword on first use.
6. Run the verification checklist. Update each row's status and line pointer, and log any corrections.
7. Present the updated close-readings file and list. If the turn stopped short of the approved list, say where, then await "continue".
