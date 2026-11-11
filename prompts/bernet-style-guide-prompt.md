# Task: a philosophical style guide drawn from Rudolf Bernet's writing

Written for: the Fable pass that builds the guide. Work in the
`commentaries` repo root. The corpus is `../sources/sources/bernet/`.

## What you are producing

A **philosophical style guide for writing scholarly articles in
phenomenology**, derived from how Rudolf Bernet writes and argues. It
will be loaded as working instructions by later passes that draft
articles, so it must be **operational**: a drafter who has never read
Bernet should be able to apply it, and a reviewer should be able to check
a draft against it.

It is a guide to **style and argumentative method**, not a summary of
Bernet's doctrines. Content enters only where it explains a move (for
example how a confrontation between two authors is staged).

Save it as `prompts/bernet-style-guide.md`, alongside the other prompts
in the `commentaries` repo, so that any drafting prompt can load it. Do
not add frontmatter. **The guide must stand alone**: it must not refer to
any other prompt, assume one will accompany it, or depend on a particular
article template. A drafter may load it with another prompt or with none.
Write it so it reads correctly either way.

## The corpus, and what stays out

**Evidence comes only from the files in `../sources/sources/bernet/`.**
Do not open `sources/notes/`, any other author's folder, `commentaries/`,
`articles/`, or the web. Do not bring in what you know about Bernet,
about phenomenological prose in general, or about house-style manuals.
If a guideline cannot be shown from these files, it does not go in.

One outside document sets constraints on how the guide is *applied*, not
on its evidence: the root `CLAUDE.md`, "Original-language wording". Read
it, make sure no guideline contradicts it, and restate its substance in
the guide's own words in a short closing section (write in English; no
non-English quotation unless a term of art or a turning point; the
original follows the English in parentheses), so the guide carries the
constraint with it.

The folder is about 12 MB and is not uniform. **Take inventory before
reading.** Make a working table, for your own use and **not for the
deliverable**, with, for each file:

- title; genre (research article, book-length study, introduction/
  handbook chapter, review, lecture or occasional piece, other);
- language of the text in hand; whether it is Bernet's original or a
  **translation** (and by whom, if stated);
- date, **only** as the file or the CV in the folder states it;
- authorship status: sole-authored by Bernet, co-authored, or an edited
  volume of which only some chapters are his;
- usable or not, and why.

Handle these cases explicitly:

- **Duplicates and near-duplicates** (several titles appear twice, or in
  two languages or two languages' versions). Use one copy; say which.
- **Stubs and non-prose** (a 189-byte and a 627-byte file; the CV; a
  review that may be of Bernet rather than by him). Exclude from style
  evidence. The CV may be used for dating only.
- **Co-authored and edited volumes** (the *Introduction to Husserlian
  Phenomenology*, the Husserl volume, the Derrida volume, the
  psychoanalysis volumes, *On Time*, and any other file that is not
  Bernet's alone). **Exclude them entirely.** Do not use even the
  chapters attributed to him; use his sole-authored articles and books
  instead. If a file's authorship is unclear, exclude it.
- **Translations.** A translated sentence shows the translator's habits
  as much as Bernet's. Derive claims about **Bernet's moves**
  (architecture, staging, stance) from all languages, and claims about
  **surface style** (sentence length, connectives, punctuation, register)
  only from texts in the language he wrote them in. Flag any surface claim
  resting on a translation and name the translator.

## How to read

The corpus is too large to read through. Do not pretend to have. Instead:

1. **Stratify.** Cover at least these axes, and say which texts you
   chose and why: early and late; German, French, English and Dutch where
   present; article, monograph, introduction/handbook, review, occasional
   piece; subject matter (Husserl on time, perception, reduction, truth;
   Heidegger and Husserl; Derrida; Levinas; Freud, drive and
   psychoanalysis; Bergson; other).
2. **Read whole**, in consecutive ranges, at least eight representative
   texts across those axes, including a short article, a long article,
   and an introduction or handbook piece.
3. **Read the load-bearing parts of the rest**: opening pages and closing
   pages of every other usable text, and the transitions between major
   sections (find them by headings).
4. **Test each emerging hypothesis at corpus scale** with search or a
   small throwaway script kept in the scratchpad, not the repo. Examples
   of the questions this is for: how often he opens with a question;
   whether he uses the first person singular or plural, and where; how
   long his paragraphs and sentences run; what connectives he prefers;
   how often he quotes whole passages and how long; whether he
   announces his plan. Report a number only with the method and the
   population, and as a count of your own, never as an estimate dressed as
   a count.
5. **Record what you did not read.** The "Limits" section of the guide
   says so, briefly.

## What the guide must cover

Each guideline gets an **ID**, a **one-sentence rule**, a **why** (what
it does for the argument), **evidence**, a **scope** (pervasive, common,
occasional, one text; and which periods, languages and genres), and
where useful a **how to apply** note. Organise by the headings below.
Cover what the corpus supports; drop a heading rather than fill it.

1. **Profile.** What the corpus is, the range of genres and periods, and
   the stable core against the variation. One page at most.
2. **Architecture of an article.** How he opens (problem, question,
   aporia, a received reading, a text); how the thesis is stated and
   where; how sections are ordered and titled; how a section ends and
   the next begins; how an article closes. Include how he stages a
   **confrontation between two authors or two readings**.
3. **Argumentative moves.** How he introduces a distinction, builds an
   objection, concedes, reverses, shows a tension without resolving it,
   moves from a text to a claim about the text, and from a claim to a
   consequence. Name each move so a drafter can use the name.
4. **Paragraph and sentence.** Paragraph length and function; sentence
   shape and rhythm; signposting and connectives; questions in the
   running text; parentheses, dashes, italics, scare quotes; nominal
   versus verbal style.
5. **Terms of art.** How a technical term is introduced, defined and held
   constant; how he flags a term that is contested or translation-
   dependent; how he treats the same word in two authors.
6. **Working with texts.** How he quotes (length, placement, lead-in and
   follow-up), paraphrases, cites editions and manuscripts, uses the
   history and genesis of a text, and distinguishes what a text says from
   his reading of it.
7. **Voice and stance.** The authorial person; hedging and commitment;
   evaluation, polemic and irony toward other readers; how he credits
   others; how he marks the limits of his claim.
8. **Apparatus.** What footnotes are for in his writing and how they are
   used; how references are given. Describe, do not prescribe a house
   format.
9. **Genre variants.** What changes between a research article, a
   handbook introduction, a review and an occasional piece.
10. **What he avoids.** Only with a search behind each claim, stated, and
    not resting on one text.
11. **Limits.** What was not read, the weak claims, where translation
    clouds the picture, and what a later pass should read next. Brief.
12. **Constraints on application.** The language rule from the root
    `CLAUDE.md`, restated in the guide's own words, and nothing else
    from outside the corpus.

## Application aids (required)

- **One-page summary at the top**: the ten or twelve rules that matter
  most, each pointing to its full entry by ID.
- **A drafting checklist** and a **review checklist** a second pass can
  run against a draft.
- **A short list of named moves** (from section 3) with a one-line
  definition each.
- **Worked contrasts**: for six to ten rules, a passage of Bernet beside a
  weaker version of the same move that you construct. Label the
  constructed version plainly as yours. Never label it Bernet's.
- **Cautions against imitation**: what in his prose is his idiom and
  should not be copied (for example features of a particular translator,
  or of a German academic register that does not carry into English
  articles). Anything here needs the same evidence as any rule.

## Evidence rules

- Every guideline cites its evidence **inline**, beside the rule: **file,
  section or heading, and line number**, with a quotation or a close
  description. Prefer quotation. There is **no separate evidence
  register, quotation index or inventory appendix**; the guide is the
  rules and their inline support.
- **Copy quotations out of the file. Never retype from memory.** After
  drafting, write a throwaway script that checks that each quotation
  appears in the file named (normalising whitespace and quote marks) and
  fix or delete every failure before you finish. Report the result.
- Quote the shortest span that shows the feature. A whole paragraph only
  where the feature is paragraph-level (architecture, a transition, the
  staging of an objection).
- Quote in English. Where the evidence is in another language, give the
  English first and the original in parentheses only when the stylistic
  point depends on the wording (a syntactic device, a pun, a coined
  term). Say whose English it is, and mark any English of your own as
  *(my translation)*.
- Separate three things visibly: **what the text does** (evidence),
  **what you infer** (marked as inference), **what you recommend**
  (the rule). A rule that rests on one text is labelled one-text.
- Do not claim a trait for Bernet because it is typical of the
  genre, the language or the period. Show it in his text.

## Form

- Plain, direct, imperative where it is a rule. No praise of the author,
  no biography, no mimicry of his voice.
- This is meant to be a **long, thorough guide**: target **10,000-15,000
  words** (all sections and the aids, with inline evidence), and go
  longer if the corpus supports more rules. Length comes from the number
  of well-evidenced rules and worked contrasts, not from padding or
  repetition. No appendix.
- Do not edit anything in `../sources/`. Keep scripts and scratch files in
  the scratchpad.

## Self-check before reporting

- [ ] Every rule has an ID, a scope and evidence with file and line.
- [ ] Every quotation was machine-checked against its file.
- [ ] No evidence from outside the Bernet folder; no claim from memory.
- [ ] Surface-style claims rest on originals; translator-dependent ones
      are flagged.
- [ ] Co-authored and edited volumes were excluded entirely.
- [ ] The guide refers to no other prompt and reads correctly alone.
- [ ] Duplicates were not counted twice.
- [ ] The guide does not contradict root `CLAUDE.md` on original-language
      wording.
- [ ] The limits section says what was not read.
