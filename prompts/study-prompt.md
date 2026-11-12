ROLE
You are writing a long scholarly study on [TOPIC] for a specialist
readership in phenomenology. It is the longer and more thorough
counterpart of the article (see prompts/article-prompt.md): several
connected parts, one governing thesis, and a fuller treatment of the
texts, of the opposing readings and of the evidence's limits. The
attached notes and the primary texts named below are your working
materials. Produce a finished study, not an outline, not a survey, and
not a summary of the notes.

GOVERNING DOCUMENTS (read before outlining)
1. prompts/bernet-style-guide.md governs how the study is built and
   how it reads. Read all of it, in consecutive ranges. Apply it
   without exception; where this prompt seems to differ from it on form,
   quotation, language or closing, follow the guide. Cite guide rules by
   ID in the Register, never in the study. It is a guide to the
   research article; for a long work apply its rules part by part (each
   part opens, turns and closes as an article would, A1-A3, A11-A13),
   and apply A1-A3 and A12-A13 once more to the whole.
2. A methodological guide, where the study analyses a concept in one
   author's manner: [prompts/husserl-methodological-guide.md |
   prompts/heidegger-methodological-guide.md]. For a study that
   compares authors' methods, prompts/phenomenologists-comparative-
   methodological-guide.md. These govern the analysis; the style guide
   governs the prose. Say in the study which method of analysis is in
   use at each stage and do not mix stages (a descriptive step is not a
   historical one).
3. The root CLAUDE.md, "Original-language wording": write in English,
   translate every quotation, keep an original only for a term of art
   or where the argument turns on the wording, and put it in
   parentheses after the English. Test: delete the original.

SOURCE DISCIPLINE (overrides everything below)
- The primary texts and the notes named under CORPUS are a closed
  corpus. Every textual claim must be traceable to a passage actually
  read in them.
- Never supply a citation or a quotation from memory. If you know a
  relevant passage exists but it is not in the corpus, do not cite it;
  log it in the Research Register and in the acquisition queue.
- Open each pointer, read around it, and confirm that the passage says
  what the note says. If it does not, search the file and record the
  corrected location; if it cannot be found, treat it as not-found and
  do not quote.
- Copy every quotation out of the file; never retype from memory.
  Afterwards confirm each by searching the file for the quoted words.
- Keep three tiers distinct in the sentence: (a) what the text says,
  (b) what the notes' commentary says, (c) what you are arguing. (c)
  never borrows the authority of (a). A note's translation is a working
  rendering, not an edition; never quote it as the author.
- If a step needs a text you do not have, write the step and mark it
  [UNSUPPORTED - needs X]. Do not paper over it.
- A claim of absence ("never", "nowhere") needs a stated search over a
  stated set of files. The silence of an index is not absence.
- Infer no influence from resemblance. A text can anticipate only what
  it predates; state the dates the argument depends on and where each
  comes from.
- Quote from the original-language file and cite the translation
  beside it. Never quote from a recheck or variant file when a reviewed
  conversion of the same work is held. Where the wording you need sits
  in a damaged range, check it against a second conversion or the
  translation and say so in the note.
- Secondary literature is a second tier. It may supply positions
  ("Alweiss argues that ..."), never evidence for what a primary text
  says, and only at the level at which it was read (in full, abstract,
  title).

CORPUS
- Primary texts: [LIST, with the folder under ../sources/sources/ and
  the edition or language of each file].
- Notes: [LIST of ../sources/sources/notes/ files; read all of each, in
  consecutive ranges].
- Consult ../sources/docs/corpus-map.md and CLAUDE.md of the sources
  repo for duplicates, version traps and files unsafe to quote.
- Hazards to honour: [LIST: shared words with different senses, file
  damage, layers of a text, chronology limits, what is unmined].

PREPARATION (do this before drafting, and save it)
Work in research/<slug>/ (not in the published folders). Write the
files in this order; each is read before the next is begun. The notes
are a map of pointers, not the corpus: the corpus comes from the
archive.

1. survey.md. Run
     python scripts/study_prep.py survey --terms <the topic's words in
       every language of the corpus> --notes <the notes> --authors
       <folders> --out research/<slug>/survey.md
   Choose terms that do not fire inside other words (see the script's
   header). The survey lists the files and sections where the words are
   dense, and the dense sections no note points to.
2. holdings.md. One row per work the study may use: the file chosen
   and why (prefer a reviewed conversion to a recheck or variant file;
   check ../sources/docs/corpus-map.md), language, whether it has page
   markers, the paired translation held, its date of composition and of
   publication with the source of each date, and known damage. Where a
   work has layers (lectures and appendices, drafts and a published
   text), date each layer.
3. reading-log.md. Every file the survey ranks high, and every dense
   section no note points to, is either read (ranges and a two-line
   finding) or excluded with a reason ("the study's dates", "a
   secondary book", "duplicate of X"). No file may simply be left
   unmentioned. Write the passage notes here, before any thesis is
   chosen: what each key passage says, in a sentence, and what surprised
   you in it.
4. literature.md. Run
     python scripts/study_prep.py lit '<FTS5 query>' --out
       research/<slug>/literature-candidates.md
   and check the held secondary works (Bernet, Moran and others in
   ../sources/sources/). Then write: who holds the received view (named
   authors, not "it is commonly held"); who has argued for something
   near each candidate thesis; and, for each, whether it was read in full,
   known from an abstract only, or known by title only. Secondary works
   supply positions, never textual evidence, and are cited only at the
   level at which they were read.
5. acquisitions.md. The key texts the study needs and the archive does
   not hold. Draw candidates from:
   - works the read passages cite or answer (Heidegger's footnote to
     *Ideen II*, a lecture course a letter mentions);
   - works named in the notes' Open threads, in research/agenda.md, and
     in the abstracts gathered for literature.md;
   - the indexes repo's works and editions records for the authors;
   - your own knowledge of the literature. Mark these "from memory";
     they are leads to verify, never facts about what a text says.
   Before you list a work as missing, search the filenames under
   ../sources/sources/, the corpus map and, for anthologies and
   collected volumes, the text of the files (an essay can sit inside a
   volume with another title). Record what was searched.
   Rank each entry:
   - decisive: the thesis, or a part of it, could be refuted or
     confirmed by this text, and without it the study must be narrowed;
   - significant: a load-bearing claim would otherwise rest on one
     passage, on a note, on a translation alone, or on a date that cannot
     be checked;
   - useful: it would add a confirmation or close a gap in the citations.
   For each entry give: author, title, and the edition wanted (original,
   and the English translation if one exists), with the year; whether a
   part suffices (sections or pages) or the whole is needed; the question
   or part of the study it bears on, and what it could settle in either
   direction; what the study will do without it (narrow, mark
   [UNSUPPORTED], state a limit); and whether the work is held in another
   language or edition only. List the decisive and significant entries
   first, at most fifteen in all; put the rest in the agenda.
6. GATE: adequacy and acquisition. Using 1-5, say whether the corpus can
   carry the question: proceed, proceed with declared limits (name them),
   narrow the question (to what), or acquire. If acquisitions.md has any
   decisive or significant entry, stop and report it to the user as a
   short list: rank, work, edition, the part needed, and one line on
   what it would settle. Do not plan until the user replies. The user
   adds the missing sources as markdown files to the sources repo and
   says where they are; do not convert, rename or move them. Re-run the
   survey on them, add them to holdings.md (with their damage and page
   markers, as for any file) and the reading log, and mark each
   acquisition received, declined or still wanted. A work the user cannot supply becomes a declared limit, and
   the plan is built on the narrower question.
7. plan.md:
   a. The one question the study asks, and the received view it starts
      from, with its holders from literature.md.
   b. The anomalies: sentences in the corpus that the received view
      leaves unexplained. List them before any thesis.
   c. Two or three candidate theses, each in one sentence, each
      something the corpus makes possible but does not state. Say which
      anomalies each explains and which it does not, how each stands to
      the precedents in literature.md, and choose one. If the strongest
      thesis is that the notes' synthesis is underdetermined or wrong,
      say that.
   d. A consequence: which passage or standard claim reads differently
      if the thesis holds, and what a specialist would have to stop
      saying.
   e. A prediction: one relevant text in the holdings not yet read,
      and what the thesis predicts it will say. Read it after the plan
      is fixed and report the result in the study or the Register,
      whatever it is.
   f. The strongest opposing reading, and the passages it rests on.
   g. The parts (see FORM), each with its question, its passages and
      its result, and the order of the argument.
   h. The tensions the texts leave open, which the study will show and
      not resolve (guide M9).
8. evidence.md. A table with the columns ID | File | Lines | Section |
   Page | Original | English file | English lines | English page, one
   row per quotation planned. Original holds the wording copied from the
   file (use … between fragments). Collate the English edition for every
   row where one is held; where it has no page markers, give its line
   span and section and log the gap. Reuse and extend any concordance
   already kept in ../sources/sources/notes/. Run
     python scripts/study_prep.py check research/<slug>/evidence.md
   and resolve every FAIL and MOVED before drafting. Run it again before
   reporting.

Then draft from the plan, one part at a time. After each part, check
its quotations, its connectives to the next part (A11) and its length.
If a part runs short, read more of the reading log's candidates before
logging a length deviation.

REVIEW (after the whole is assembled)
Give the study and the files, and nothing else, to a reviewer in a
fresh context (a subagent). The reviewer (1) argues the opposing reading
against the study as hard as the texts allow, (2) re-checks ten
quotations chosen by the reviewer against the files, and (3) names the
claim it finds weakest. Revise from the report and record what changed
in the Register.

WRITE-BACK (after the Register)
Findings outlive the study only if they leave it. Update the notes
named under CORPUS with each corrected pointer, each error found and
each newly read passage (Register 5-7), as file:line pointers with the
§. Record file damage in ../sources/docs/corpus-map.md. Add the
desiderata, the directions not taken and the acquisition queue
(Register 2, 4, 9) to research/agenda.md, dated and with the study's
slug, and read that file before planning the next study. Collated
concordances go into the notes for the next study to reuse.

ARGUMENT
- Advance a thesis the notes do not already state, and say where it
  stands to the nearest published precedent in literature.md: what it
  adds, corrects or grounds in texts the precedent did not use. Name
  the holders of the received view in the opening. Reconstruct the
  strongest opposing reading at full strength before rejecting it, and
  give it its own stretch of the study (guide A10, V3).
- Date doctrinal shifts across the corpus; do not resolve a tension the
  texts leave open.
- Test the thesis against its hardest case in the corpus, not only the
  convenient ones, and say what the thesis cannot explain.
- Where authors are compared, stage the confrontation around one
  shared question: parallels, then differences, then the root of the
  differences, each author explained in terms the other could accept
  (guide A7-A9). A shared word is not a shared concept (guide T4).
- State the limits of the evidence where they bear on a claim, and
  once in a consolidated place (guide A3, V6).

FORM
- Length: [N] words of your own prose, excluding quotations, notes,
  citations and the Register. A working range is 20,000-40,000 words.
- Structure: a title, an opening that does what guide A1-A3 direct
  (received view turned; thesis as something to be shown; textual basis
  and omissions declared with reasons), then numbered parts with
  noun-phrase titles, each of 3,000-7,000 words, each divided by
  numbered sub-sections only where the argument turns. No part called
  "Introduction" or "Conclusion" (guide A6, X3). A part may have its own
  short opening and close, but no part ends with a summary of itself.
- Order the parts by the matter: exposition first, interpretation
  after (guide A5). A typical shape for a study of this size: the
  question and the received view; each author's concept or method in
  date order; the confrontation; the strongest objection and the reply;
  what remains open.
- The close follows guide A12-A13: no section-by-section summary; the
  thesis in its sharpest form with at least one limit, open question
  or credit to the author criticised; the title's question answered,
  even by "no".
- Prose per guide sections 4-7. Continuous prose; no bullet lists in
  the argument. Tables only where the guide's method calls for a
  comparison and the table carries what prose cannot (say what each
  column means).
- Citation convention: [YOUR CONVENTION]. Cite both the English edition
  and the original edition for every quotation of a primary text (guide
  W7), state the convention once in the first note, and give archive
  line pointers in that note with a warning that they are not
  pagination. Take pages only from page markers in the files; if a page
  cannot be determined write [page not located]. Never guess a page.
  Where only the original is held, translate the whole paragraph
  yourself and label it (my translation).
- Quote terms and short phrases woven into your sentences; quote whole
  sentences rarely, with a lead-in and a follow-up (guide W2-W3).
- Notes carry what guide N1-N4 assign them. Check the format of
  existing files in articles/ for format only, never for content.
- Cross-references inside the study ("as shown in part 2") must be
  true. Every "we will return to this" has a return (guide M3).

OUTPUT FILE
- Save the finished study to articles/<slug>-study.md (the top-level
  articles/ folder, not under commentaries/). Because of its size, draft
  into the file part by part rather than in one write, and re-read the
  assembled file once for consistency of terms, dates and citations.
- Slug: <topic>-study, using the repository's slugging rules
  (lowercase, hyphens, transliterated diacritics, punctuation dropped,
  subtitle dropped after a colon or dash).
- Frontmatter, before the title heading:
  ---
  layout: default
  title: <human-readable title>
  ---
  Quote the title in YAML (single quotes, doubling any internal
  apostrophe) if it contains a colon.

RESEARCH REGISTER (append after the study; plain prose or lists; the
style guide does not govern it)
1. Works and passages actually used, grouped by text, with both-edition
   citations.
2. Desiderata: what is missing, and what each would settle.
3. Load-bearing points resting on the notes' commentary with no primary
   text behind them.
4. Directions opened but not taken.
5. Places the notes appear wrong or internally in tension.
6. What the primary texts changed: each place a paragraph narrowed,
   widened or embarrassed a claim of the notes, with both wordings.
7. Pointers that failed, with the corrected line if found.
8. Citation gaps: every [page not located], (my translation) and
   English edition not in corpus.
9. Acquisition queue: texts needed to support each [UNSUPPORTED] step,
   and the fate of each entry in acquisitions.md (received and used,
   declined, still wanted).
10. Style-guide deviations, by rule ID, and why. There should be none by
    design.
11. Part-by-part word counts against the plan.
12. The prediction (plan e): the text, what was predicted, what it
    said, and what that does to the thesis.
13. The review: what the reviewer argued, which quotations it checked,
    and what was revised.
14. Write-back: each note, map and agenda entry updated, by file.

SELF-CHECK BEFORE REPORTING
- [ ] Every quotation of a primary text is copied from a file and
      confirmed by search; none comes from a note's own translation.
- [ ] `study_prep.py check` passes on evidence.md with no FAIL or MOVED,
      and evidence.md holds every quotation in the study.
- [ ] Every high-ranked file and dense unpointed section in survey.md
      is read or excluded with a reason in reading-log.md.
- [ ] The received view has named holders, and the thesis is placed
      against its nearest precedent.
- [ ] Every quotation has both-edition citations or the explicit marker.
- [ ] All non-English is translated; any original kept passes the
      deletion test.
- [ ] No claim of absence rests on an index's silence; no influence is
      inferred from resemblance; anticipation respects the dates.
- [ ] The strongest opposing reading has its own stretch and is not a
      straw figure.
- [ ] Each part opens from what precedes it and ends on what the next
      must supply; the whole closes per A12-A13 without summary.
- [ ] Tensions the texts leave open are shown and left standing.
- [ ] The style guide's Review checklist (section 14) was run on each
      part and on the whole, and deviations are logged.
