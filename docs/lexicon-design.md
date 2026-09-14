# Term lexicon — design

Why `synthesis/lexicon.json` exists and what it is not allowed to do. For
the pipeline it plugs into see [synthesis-design.md](synthesis-design.md);
for how to run it, [synthesis-operations.md](synthesis-operations.md) §L1–L4;
for what binds an agent editing it, [synthesis/CLAUDE.md](../synthesis/CLAUDE.md).

---

## 1. The problem

The retrieval layer is term search (synthesis-design.md D5), and term
search is only as good as its term list. Today that list is
`themes.json` `search_terms`: eight themes, nine to twenty-five terms
each, all typed by hand.

Two failures follow, and both are silent.

**A missing rendering loses a commentary, not a passage.** The corpus is
English by construction, so a German headword finds almost nothing on its
own — D5 says so. The English renderings are what actually match, and
different commentaries use different ones. `Wesensschau` is glossed
*essence-intuition* in the Derrida commentary, *intuition of essences* in
the *Sein und Zeit* commentary, and *essential intuition* in Hua IX. All
three are in the corpus; `themes.json` has none of them. A `wesen` search
finds the German and misses every place the term is discussed in English.

**A shared rendering merges two terms.** `Besorgen` and `Bekümmerung` are
both rendered *concern* here, one in *Sein und Zeit*, the other in GA 61 —
different terms, different decades, one English word. `Zeitlichkeit` and
`Temporalität` are separated in the corpus by a capital T, which the
matcher lowercases away. Nothing in `themes.json` can express either fact,
so nothing warns the pass that walks into it.

**And a term can be swamped by something that merely looks like it.** The
matcher is left-anchored by design (D5), so `Leib` matches `Leibniz` — and
this corpus has a Leibniz commentary. `synthesis_query.py --terms Leib`
ranks it first, on 93 hits, none of them the German word; in the `leib`
theme as registered it sits fifth, above four Husserl commentaries on the
body. That is a live defect in the retrieval layer, and nothing in
`themes.json` can express it.

There is a fourth problem the others hide: nobody has an inventory.
Eight themes exist because eight themes occurred to someone. `Dasein` has
no theme, and no file anywhere records that this is a choice rather than
an oversight.

## 2. The line

> The lexicon says what to look for and where a rendering was seen. It
> never says what a text claims.

The pipeline's invariant is that every claim about a text carries a
locator and a verbatim quote from a commentary. A lexicon entry is not
that and must never become that: it is compiled from reference works,
translators' habits and the registrar's own reading, which is exactly the
outside knowledge `synthesis/CLAUDE.md` rules 3 and 6 keep out of the
evidence.

So the lexicon sits on the retrieval side of the pipeline, upstream of
the candidate list and nowhere else:

```mermaid
flowchart LR
    L["lexicon.json<br/>headwords · forms · renderings"]
    L -->|--expand, by hand| T["themes.json<br/>search_terms"]
    T --> Q["synthesis_query.py<br/>candidate sections"]
    Q -.->|which sections to read| E["Stage 1 · extraction<br/>locator + verbatim quote"]
    E --> V{"synthesis_validate.py"}
    C["commentaries/*/*.md"] --> E
    C --> L
    L -.->|--check: does the corpus<br/>say what the entry claims?| C
    L -.->|--candidates| G["gaps.json · themes.json<br/>the reading queue"]
    L x-.-x|never| V
```

The dotted line back to the commentaries is the part worth noticing. A
rendering can be *attested* — a commentary glossed the term itself, in a
named section, and the entry records where. That is the same move as the
quote check, applied to a dictionary entry, and it is why the file
carries 112 attested renderings out of 676.

## 3. Data model

    lexicon.json
      sources[]   {id, kind, citation, note?}
      entries[]   {id, headword, language, forms[], renderings[],
                   authors?, theme?, contrast_with?, unsearchable?,
                   gloss?, note?}
        renderings[]  {english, source, translator?, locator?, note?}

One entry per **headword**, not per theme and not per author. Themes are
coarse (eight of them) and are about what a synthesis is *about*;
headwords are what a dictionary indexes and what a search actually needs.
A term several authors use is one entry listing them in `authors`, not
three entries drifting apart.

`theme` is optional, and its absence is the point: an entry with no theme
is a candidate, and `--candidates` ranks those by how much corpus they
touch.

**An `en` entry has no original-language anchor, and says so.** Some
headwords in both dictionaries are English concepts with no German behind
them — *Apophantics*, *Signitive act*, *Philosophical anthropology*. They
are registered with `language: "en"`, and their single form equals their
single rendering, which looks circular and is not: it records that the
headword travels under itself. What such an entry cannot do is the thing
a German entry does best. There is no second spelling to disambiguate a
hit, so every ambiguity has to be settled by `absent_terms` at extraction
time (CLAUDE.md rule 5) rather than by the term list. Eighteen of the 535
entries are of this kind.

## 4. Design decisions

### L1 · Retrieval, never evidence

Stated above; enforced by construction rather than by instruction. No
script copies lexicon text into an extraction record, `gloss` is capped at
240 characters and documented as non-citable, and the schema gives an
entry nowhere to put a claim. The validator never reads this file, which
is the structural version of the same rule: nothing downstream of
`synthesis_validate.py` can depend on it.

### L2 · Every rendering names a source, and one kind of source is checkable

Four `kind`s, in descending order of what a machine can do with them:

| kind | what it is | verifiable |
|---|---|---|
| `commentary-corpus` | a commentary in this corpus states the pairing | yes — carries a locator, `--check` resolves it |
| `translation` | a named translator's standing rendering | no |
| `dictionary` | a published reference work | no |
| `registry` | a term this repo already asserted elsewhere | no |

For `commentary-corpus` the check has teeth: `--check` resolves the
locator against `corpus.json` and confirms that the section contains
**both** the English and one of the entry's original-language forms. The
second half matters more than the first. Without it an entry could claim
the *Sophist* commentary renders `Sorge` as "care" by pointing at a
section where "care" appears in its ordinary English sense and `Sorge`
never appears at all — which is precisely the confusion gap-004 is about.

The other three kinds are unverifiable by construction. They are marked
rather than blended in, for the reason D4 gives about dates: a corpus that
quietly imports facts from outside has no way to say which facts those
were.

### L3 · `--expand` prints a diff; it does not edit `themes.json`

Widening a theme's search terms is not a merge. Over-inclusion is safe for
a candidate list — a false positive costs a glance — but `absent_terms`
defaults to the theme's search terms, so the same edit changes what a
recorded absence *means*, and D3 makes absences evidence. That is a
judgement, and `themes.json` stays authored (CLAUDE.md rule 8).

So `--expand` reports both directions and stops. Terms the lexicon has and
the theme lacks are commentaries the theme is currently missing. Search
terms with no entry behind them are the reverse question: `leib` searches
for `corps propre`, which fires twice in the whole corpus, and nobody had
a way to notice.

### L4 · Glosses are short, original, and not the dictionary's

`gloss` is capped at 240 characters and is written by the registrar, in
their own words. A reference work's definition text is not copied into
this repo — not into a gloss, not into a note.

This is not squeamishness. The dictionaries are third-party copyrighted
works, and `sync_wordpress.py` globs `commentaries/*/*.md` and publishes on
every push with no draft step (D10). A file in `synthesis/` is one `git mv`
away from a live public page. What belongs here is the part that is not
the book: headwords, forms, renderings, cross-references — with the book
cited in `sources[]` so a reader knows where the compilation came from.

### L5 · Attestation is computed, never stored

Whether a term actually occurs in the corpus is a `--attest` report, not
a field. A stored hit count would go stale against the corpus the moment a
commentary was edited, and this repo already has one staleness mechanism
(D6) whose whole value is that it means something. Same reasoning as D8:
generated facts stay generated.

### L6 · Collisions are warnings, not errors

Two entries sharing an English rendering is a fact about this corpus, not
a mistake — `Besorgen` and `Bekümmerung` really are both "concern" here.
What must not happen is that it goes unrecorded, because a search on the
shared English cannot separate them and an absence claim over it says
nothing about which term is absent. So `--check` warns when two entries
share a rendering and are *not* linked by `contrast_with`: the fix is to
write the collision down, not to delete one of them.

The same applies within an entry: two forms differing only in case search
as one term, because the matcher lowercases. That is worth saying once and
then removing.

### L7 · The corpus is a dictionary too

Every attested rendering in the seed file was mined out of the
commentaries themselves — from their own `English (Original)` glosses —
not typed from a reference work. That was partly discipline and partly
discovery: the mining is what turned up the three renderings of
`Wesensschau` and the `Besorgen`/`Bekümmerung` collision, neither of which
a Heidegger dictionary would have flagged, because both are facts about
*these* commentaries rather than about Heidegger.

A dictionary tells you what renderings exist. The corpus tells you which
ones are in play. Both belong in the file; only the second can be checked.

### L8 · Some forms are recorded and never searched

`unsearchable` lists forms whose hits in this corpus are mostly something
else, and `--expand` will not propose them. Three mechanisms:

- **Homographs.** `Not` is German for distress and English for *not*:
  26,852 whole-word hits here, none of them Heidegger's word.
  `Interpretation`, `Situation`, `Tradition` and `Negation` are spelled
  identically in both languages.
- **Prefixes.** The matcher is left-anchored (D5), so `Natur` fires
  inside *nature* and *natural* — 5,445 hits, of which 13 are the German
  — `Stil` inside *still*, `Typ` inside *type*, `Tod` inside *today*,
  `Wort` inside *worth*, Husserl's `ratio` inside *rational*.
- **Another word the corpus happens to contain,** which need not be
  English. `Leib` fires inside `Leibniz` 265 times against 44
  occurrences of the German word, because this corpus has a Leibniz
  commentary. This is the cause that named the field: it was
  `ordinary_english` until the Husserl import found a case that was
  neither ordinary nor English.

A form the registrar creates is as exposed as one the book prints.
Article-led headwords get an article-less form as well, because a
commentary writing *natürliche Einstellung* should still be found — but
the same rule turned `das Man` into `Man`, which fires 7,536 times inside
*manner*, *manifold* and *manifestation* and a further 1,072 times as the
English word. The article was the whole of what made that headword
searchable. Derived forms go through the same reading as printed ones.

The forms stay in `forms`, because they are the term's real forms and an
`--attest` report should still count them. What they must not do is reach
`themes.json`, where `absent_terms` defaults to the theme's search terms
and one such entry makes every absence claim in the theme vacuous. This
is the German-side counterpart of `synthesis/CLAUDE.md` rule 5.

**The field is authored, not computed, and the imports are why.** The
obvious rule — flag a form whose left-anchored count far exceeds its
whole-word count — produced 25 flags on the Heidegger import of which 12
were wrong, and 28 candidates on the Husserl one of which 22 were. It
cannot tell contamination from German compounding, and by count they are
identical: `Wissen` exceeds its whole-word total because of
*Wissenschaft*, `Geist` because of *Geisteswissenschaften*, `Leben`
because of *Lebenswelt*. That over-inclusion is not a defect, it is what
the left-anchored matcher is *for*. Only reading the words a form
actually fires inside separates the cases, so `--attest` prints both
counts and flags the divergence neutrally — "fires mostly inside longer
words" — and a person decides which kind it is.

## 5. What the machine cannot check

| Checked | Not checked |
|---|---|
| An attested rendering's section contains both the English and the form | That the rendering is a *good* one |
| Locators resolve; entry ids are unique; themes exist | That the entry's `theme` is the right theme |
| Sources resolve; corpus-sourced renderings carry a locator | That a `dictionary` rendering is really in that dictionary |
| Shared renderings are declared as contrasts | That the contrast is the significant one |
| `unsearchable` names real forms of the entry | That the forms needing the flag all have it |
| Which registered terms occur in the corpus, and where | Which *unregistered* terms should have been |

The last row is the important one, and it is where the lexicon narrows a
hole rather than closing it. `--attest` names renderings that fire nowhere;
`--expand` names search terms nobody accounted for. Neither can find a
commentary that renders a term of art into ordinary English and never
glosses it — no scan over English text can, and that is exactly what
gap-004 asks about. What the lexicon does is make the answerable part
cheap enough to actually run.

## 6. The reference works

### What is registered

| Source | Kind | Contributes |
|---|---|---|
| `corpus` | the commentaries themselves | 112 renderings, each with a locator, each checked |
| `repo-registry` | `themes.json`, `synthesis_query.py`, `commentaries/CLAUDE.md` | 45, the pre-lexicon seed |
| `dahlstrom-2013` | Dahlstrom, *The Heidegger Dictionary* (Bloomsbury, 2013) | 242 |
| `moran-cohen-2012` | Moran and Cohen, *The Husserl Dictionary* (Continuum, 2012) | 277 |

535 entries — 498 German, 18 English, 12 Greek, 6 Latin, 1 French. Only forms,
renderings and cross-references are taken. No definition text is
reproduced — not in an entry, not in a note, not in a gloss. The books
stay in [faultynode/sources](https://github.com/faultynode/sources) or
outside git; see L4, and note that `synthesis/` is one `git mv` from a
live public page.

### The two are shaped differently

Dahlstrom's A–Z headings are `English (German)` and his glossary is a
plain German→English list. Moran and Cohen key the other way round — the
headword is the English, the German follows in italics, often several at
once (`Adumbration, profile (Abschattung, Aspekt, Profil)`) — so their
entry titles are the renderings and their italics are the forms. Two
entries pointing at one German word is how the redirects work:
*Accomplishment* and *Achievement* are both `Leistung`, and merge into one
entry with two renderings.

Neither shape is the lexicon's; both flatten into it, which is the point
of keying entries on the headword rather than on a book's layout.

### What the imports taught

1. **A glossary can carry translator divergences.** Dahlstrom flags
   where his rendering differs from the standard translations of *Sein
   und Zeit* — `MR` for Macquarrie-Robinson (1962), `S` for Stambaugh
   (2011). `Befindlichkeit` is his *disposedness*, MR's *state of mind*,
   S's *attunement*. Fifteen renderings carry a `translator`, which is
   what the `vorhandenheit` theme note has been asking for since it was
   written. Moran and Cohen mark no translator divergences, so the field
   stays empty for the Husserl half.
2. **A dictionary poisons a term list if imported naively.** See L8.
   Twenty-one forms cannot be searched here at all, and the worst of them
   was invisible until the second import: `Leib` is 86% Leibniz.
3. **Collisions arrive in bulk, and the second import collides with the
   first.** 26 pairs from Dahlstrom (`Auslegung`/`Interpretation` both
   *interpretation*, `Grund`/`Vernunft` both *reason*), then 20 more once
   Husserl's vocabulary landed beside Heidegger's — `Einklammerung` and
   `Epoché` both *bracketing*, `Gegenständlichkeit` and `Objektivität`
   both *objectivity*, `Erkennen` and `Wissen` both *knowing*. 60 entries
   now carry a `contrast_with`. The lexicon says the collision exists and
   says nothing about which term a passage means.
4. **Most of a dictionary is not about this corpus.** 208 of the 535
   headwords occur in no commentary here. They are kept — a term registry
   for an author is a coherent object, and a partial import invites a
   confused second one — and they rank last in `--candidates`, which is
   where an unregistered headword goes to be noticed.

### A book can be extracted twice and differ

The Husserl dictionary arrived a second time as a cleaner ebook export —
the same text with its HTML link markup flattened. The term pairs were
byte-identical, 303 either way, but the diff exposed a defect in the
first extraction rather than in the book: Moran and Cohen sometimes run
an entry's body text on to the heading line, and a heading regex that
required the line to end after the bold skipped those entries outright.
Seven terms were missing — `Grundlagenkrise`, `der uninteressierte
Zuschauer`, `erste Philosophie`, `Sinnzusammenhang`, `Rückfragen`,
`Teleologie`, `Thesis` — along with *intropathy*, the second half of the
headword "Empathy or intropathy".

Two things follow. A layout assumption is worth testing against the lines
it rejects, not only the ones it accepts: counting the bold-initial lines
a heading pattern *fails* on is a two-minute check and it is what found
these. And the failure is per-book, not general — the same check over
Dahlstrom matched all 171 of his headings, because his layout puts every
heading on a line of its own.

A heading can also carry more than one parenthetical, and a pattern that
takes the span between the first `(` and the last `)` swallows the
English in between: Moran's `Judgement (Urteil), judging (Urteilen)`
became a form spelled `Urteil)` beside one spelled `judging (Urteilen`.
Three entries were built that way. Stray brackets in a form or rendering
are the signature, they are one `grep` away, and finding none afterwards
is what says the file is clean.

Reading the rejected lines a second time, for the headwords with no
German parenthetical, found three more groups. Entries whose German the
export's stray asterisks had hidden (`Erscheinung, Apparenz` behind
`*Apparenz***`); entries whose headword is Latin or Greek rather than
German (`Cogito`, `Epistēmē`, and on Dahlstrom's side `Aletheia`,
`Logos`, `Moira`); and entries that are English concepts with nothing
behind them, which is what `language: "en"` is for. Three Dahlstrom
entries had also been lost to headings the export split across two lines
— `Seyn`, `Überwindung der Metaphysik`, and a second rendering for `die
Zukünftigen`. Moran's eleven pure redirects (*Animate body* **See** *lived
body*) are not entries at all: they are renderings of the entry they point
at, and six resolved to exactly one target.

### Adding the next one

1. Keep the book out of the repo (as above).
2. Add it to `sources[]` with `kind: "dictionary"` and a full citation.
3. Extract headwords, forms and renderings. Nothing else. Work out which
   way round the book is keyed first, then count the lines your heading
   pattern rejects and read them — that is where the entries a layout
   assumption loses will be.
4. Mine the corpus for the same headwords — `English (Headword)` glosses
   are attested renderings, and they carry locators `--check` can verify.
   This is what makes an entry worth more than the dictionary page it
   came from (L7).
5. Run `--check`, work the collision warnings into `contrast_with`, and
   run `--attest` over the new entries to decide `unsearchable` by
   reading what each form fires inside (L8).
6. `--expand` per theme the batch touches, then `--candidates`.

A dictionary for an author with no commentary in the corpus is still
worth registering. Merleau-Ponty is the live case — named 146 times
across these files and the subject of none of them — and his entries
would rank in `--candidates` on hits from the commentaries that discuss
him, which is the coverage map for the commentary nobody has written.

## 7. Performance

Whole lexicon, 535 entries, against 53 commentaries and 2.9 million words:

| Mode | Time |
|---|---|
| `--expand` | instant (no corpus scan) |
| `--check` | 1.2 s |
| `--candidates` | 9.3 s |
| `--attest`, one theme | under a second |
| `--attest`, everything | 19.5 s |

`--attest` over the whole file counts every registered term against every
document: 69,801 term-document pairs, and 42 s written the obvious way at
a twelfth of the current size. The matcher's pattern is a literal with a
left-hand word boundary, so the occurrences can be found with `str.find`
and filtered on the preceding character instead of scanned for with a
regex; cost then tracks how often a term occurs rather than how long the
corpus is, and both boundary tests share one traversal. The result is
identical — checked against `lib.count_terms` over every pair — and the
same trick is available to `synthesis_status.py` if that report ever
outgrows its budget.
