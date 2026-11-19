# Holdings: genetic phenomenology in Hua XI

Written 2026-11-15, after survey.md. One row per work the study may use.
Paths are under `../sources/sources/`. "Markers" means page markers
(`<!-- … -->`) from which a page can be taken. Dates give their source; a
date marked *memory* is a lead, not a fact.

## Primary texts

| Work | File chosen, and why | Lang. | Markers | Paired translation held | Composed (source) | Published (source) | Known damage |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Husserl, *Analysen zur passiven Synthesis* (Hua XI) | `husserl/husserl-hua-11-analysen-zur-passiven-synthesis.md`; the only conversion held | German | yes (523) | **none** (Steinbock's English is not in the archive) | 1918–1926 (title page, `:22`); layers below | 1966, ed. M. Fleischer (`:26`, `:40`) | see "Hua XI: layers and damage" |
| Husserl, Hua XIV, Beilage I, "Statische und genetische Phänomenologie" | `husserl/husserl-hua-14-…-zweiter-teil.md:1172`–`:1302`; only conversion | German | yes; some of the form `<!-- p. 40 … -->`, which `study_prep.py check` does not read | none | June 1921 (heading `:1178`; apparatus `:12576`: first leaf dated June 1921, last three leaves "aller Wahrscheinlichkeit nach" 1921) | 1973, ed. I. Kern (`:23`) | "verogenes" for *verborgenes* (`:1212`), "Scheidin" (`:1269`); otherwise clean in the range read |
| Hua XIV, editor's introduction and apparatus | same file, `:471`–`:723`, `:12494`–`:12579` | German | yes | none | 1973 (Kern) | 1973 | not checked beyond the lines read |
| Husserl, Hua XIII, Beilagen XLV–XLVI ("Die phänomenologischen Ursprungsprobleme"; "Problem der Apperzeption") | `husserl/husserl-hua-13-…-ersterteil-1905-1920.md:7530`–`:7750`; only conversion | German | yes (693 in file) | none | "(<1916>/1917)" (heading `:7533`) | Hua XIII is 1973 (*memory*; the file has no front matter, corpus map) | file opens at Text Nr. 1; no front matter |
| Husserl, *Die Bernauer Manuskripte* (Hua XXXIII) | `husserl/husserl-hua-33-…-1917-18.md`; only conversion | German | yes (627) | none | 1917/18 (title, `:4`) | 2001, ed. Bernet and Lohmar (`:40`) | not yet assessed |
| Husserl, *Cartesianische Meditationen* (Hua I) §§ 34–39, 58–61 | `husserl/husserl-hua-1-…-pariser-vortrage.md`; only conversion | German | yes (340) | none (Cairns is not held) | 1929 (*memory*; no date read in the file yet) | French 1931 (Moran and Cohen, `moran/…:544`); German 1950 (`:50`) | "Einheitsformdes", "Gesetzmäßigkeiteineruniversalen" (`:2303`): bold spans run together; an editorial footnote is fused into the text at `:2336` |
| Husserl, *Formale und transzendentale Logik* (Hua XVII) §§ 85–86, Beilage II, Ergänzender Text IV | `husserl/husserl-hua-17-…-logischen-vernunft.md`; only conversion | German | yes (640) | none (Cairns is not held) | FTL 1929 (corpus map); Ergänzender Text IV is the "Vorbereitende Betrachtungen zur Vorlesung über Transzendentale Logik" (`:470`), i.e. the opening of the course Hua XI prints: date to be taken from the file when read | 1974, ed. P. Janssen (`:44`) | **machine-converted, not reviewed**; 11 pages owed (corpus map). Any quotation needs a second check; there is no second conversion, so damage becomes a declared limit |
| Husserl, *Phänomenologische Psychologie* (Hua IX) | `husserl/husserl-hua-9-phaanomenologische-…-1925.md` | German | yes (868) | `husserl-hua-9-phenomenological-psychology-lectures.md` (Scanlon; main text only) | SS 1925 (title `:15`): between the second and third versions of the logic course | 1962 (`:40`) | not assessed for the ranges needed |
| Husserl, Hua XV (*Intersubjektivität* III) | `husserl/husserl-hua-15-…-1929-1935.md` | German | yes | none | 1929–1935 (title) | 1973 (*memory*) | not assessed; outside the study's dates (see reading log) |
| Husserl, *Logische Untersuchungen* II/1 (Hua XIX/1) | `husserl/husserl-hua-19-1-…-erster-teil.md` | German | A/B markers | `husserl-logical-investigations-1.md` / `-2.md` (Findlay/Moran; no shared pagination) | 1901; 2nd ed. 1913 | Hua XIX/1 | only for the early, psychological sense of "genetisch" |
| Brentano, descriptive against genetic psychology | `brentano/Brentano - Psychologie descriptive 1950 Editions Gallimard.md` | French | none | — | lectures (dates to take from the file) | French edition | filename unnormalized; a translation, so wording is not Brentano's German |

## Hua XI: layers and damage

**What the file lacks.** The table of contents lists an "Einleitung des
Herausgebers" (p. XIII, `:53`) and a "Textkritischer Anhang" (pp. 441–532,
`:306`–`:317`). Neither is in the file: the text runs from the title pages to
p. 437 (Beilage XXVIII) and stops. So the edition's own account of which
manuscript and which year each stretch of the main text comes from is not
held. This is the main limit on dating.

**Layers that can be dated from what is held.**

| Layer | Pages | Lines | Date | Source of the date |
| --- | --- | --- | --- | --- |
| The course | — | — | WS 1920/21 "Logik"; repeated in new versions SS 1923 ("Ausgewählte phänomenologische Probleme") and WS 1925/26 ("Grundprobleme der Logik") | Kern, Hua XIV introduction, `husserl-hua-14-…:514` (n. 7) and `:593` (n. 39) |
| Main text, § 16 onward | 65 ff. | `:1208` ff. | after Christmas 1925, so the third version | editor's note `:1266` |
| Main text, §§ 1–15 and §§ 40–48 | 3–64, 184–222 | `:319`–`:1199`, `:2589`–`:2990` | **not determinable from the file**. The "first version" covers "§ 12 to § 40", which implies that outside that span the earlier text was kept or that no earlier text is printed; which, the missing apparatus would say | inference only; marked as a limit |
| Ergänzende Texte A, "Erste Fassung des Textzusammenhangs zwischen § 12 und § 40" | 225–290 | `:2996`–`:3992` | 1920/21 | heading `:2998`; "Weihnachtsferien 1920", `:3478` |
| B, "Wahrnehmung und ihre Selbstgebung" | 291–303 | `:3993`–`:4180` | "1923? und 1920/21" | editor's note `:4020` |
| B, "Bewußtsein und Sinn — Sinn und Noema" | 304–335 | `:4182`–`:4426` | "1920 ff." | editor's note `:4192` |
| B, "Statische und genetische phänomenologische Methode" | 336–345 | `:4427`–`:4523` | 1921 | Husserl's note `:4517`; Hua XIV apparatus `:12576` (convolute B III 10, leaves 22–30, cover "Genesis 1921") |
| C, Beilagen I–XXVIII | 346–437 | `:4524`–end | each dated in the table of contents (`:247`–`:304`) and in a first footnote; e.g. Beilage XVIII 4 June 1925 (`:5199`), Beilage XIX 12–14 Feb. 1926 (`:5338`), Beilage V 27 Aug. 1926 (`:4681`) | table of contents and notes |

**Damage seen in the ranges read.**
- OCR substitutions in terms the study will quote: "retional", "retionale",
  "protionale", "retotional", "retationale" for *retentional/protentional*
  (`:4431`, `:4437`, `:2383`–`:2395`); "korialen" (`:4459`); "E.ntweder",
  "H.yletische" (`:2301`, `:2341`); "Selbsobjektivierung", "Bereitschaftheiten"
  (`:2979`); "Zusammenschbetrachtung" (`:2012`). A quotation containing such a
  word is given in corrected spelling and logged.
- Print line numbers inside the running text (`:1960`, `:2393`–`:2395`,
  `:2423`, `:4470`–`:4483`).
- Footnote numbering is not the edition's: `[^49]` is used three times at
  `:4517`–`:4519` for different notes, `[^25]` three times at `:2036`–`:2038`.
- Several § headings are plain text, not `#` headings (§§ 1, 5, 16, 26, 33,
  39, 41, 42, 46), so `study_prep.py survey` assigns their hits to the
  previous heading.
- Page markers sometimes stand mid-line or after the first words of a page
  (`:374`, `:1212`); two stray markers `<!-- 372 -->` at `:2993`–`:2994` do not
  belong to p. 222.
- Not found in the file: § 5 heading text beyond the table of contents was
  not checked; §§ 39 and 41 not yet located.

## Secondary works held (second tier)

| Work | File | Lang. | Read level so far |
| --- | --- | --- | --- |
| Bégout, *La Généalogie de la logique* (Vrin; dépôt légal June 2000, `:15`) | `begout/begout-la-genealogie-de-la-logique.md`; no page markers | French | two sections in full; rest to read (reading log) |
| Bernet, Kern, Marbach, *An Introduction to Husserlian Phenomenology* (Northwestern 1993), ch. 7 | `bernet/bernet-an-introduction-…-bernet-kern-marbach.md`; breaks off in ch. 7; notes 125–130 empty | English | ch. 7 as far as held, in full |
| the same, German (*Edmund Husserl: Darstellung seines Denkens*, Meiner 1989; this copy the 1996 printing, `:16`) | `bernet/bernet-edmund-husserl-darstellung-seines-denkens.md:7399` ff.; no page markers | German | located; to read for the part the English lacks |
| Drummond, "On Welton on Husserl" (NYB III, 2003) | `new-yearbook-for-phenomenology/The new yearbook … Crowell, Steven, Hopkins, Burt & R_ Bruzina & A_ Mickunas &.md:3068` ff. | English | §§ I–III in full |
| Ni Liangkang, "Horizontal-Intention: Time, Genesis, History" (in *On Time*, ed. Lohmar and Yamaguchi) | `bernet/bernet-on-time-…:7526`–`:8488`; words run together by the conversion | English | abstract and hit lines |
| Pietrek, "A Reconstruction of Phenomenological Method for Metaethics" (NYB IV, 2004) | `new-yearbook-…/The New Yearbook … Hopkins, Burt; Crowell, Steven; Brainard, Marcus & R_.md:831` ff. | English | headings only |
| Luft, "A Hermeneutic Phenomenology of Subjective and Objective Spirit: Husserl, Natorp, and Cassirer" (NYB IV, 2004) | same file, `:2259` ff. | English | headings only |
| Lerner, "The Cartesian Meditations' Foundational Discourse" (NYB X, 2010) | `new-yearbook-…-hopkins-burt-drummond-john-r-bruzina-s-crowell.md:2007` ff. | English | headings only |
| Bruzina, "Husserl's 'Naturalism' and Genetic Phenomenology" (NYB X, 2010) | same file, `:1432` ff. | English | headings only |
| Derrida, "'Genesis and Structure' and Phenomenology" (in *Writing and Difference*, tr. 1978; French 1967) | `derrida/derrida-writing-and-difference.md:1381`–`:1461` | English | not yet read |
| Derrida, "Phenomenology and the Closure of Metaphysics" (NYB III, 2003, tr.) | NYB III file, `:1184` ff., § 3 at `:1264` | English | not yet read |
| Moran and Cohen, *The Husserl Dictionary* (2012) | `moran/moran-cohen-the-husserl-dictionary.md:372`, `:974`, `:1574` | English | entries located |
| *Edmund Husserl Bibliography* (Hua Dok IV) | `husserl/husserl-hua-dok-4-edmund-husserl-bibliography.md` | English | used to verify titles and years in acquisitions.md |

## Not held (searched 2026-11-15)

Searched: filenames under `../sources/sources/*/`; the corpus map; and the
text of the Husserl, Bernet and New Yearbook files for the titles. Result:
no English Hua XI; no Hua XXXI (*Aktive Synthesen*; named only in the series
list at `husserl-hua-33-…:5422`); no *Erfahrung und Urteil* in either
language; no Hua XVII or Hua I in English; no Holenstein, Steinbock, Welton,
Aguirre, de Almeida, Yamaguchi, Kern (*Husserl und Kant*) or Sokolowski
monograph. See acquisitions.md.

## Added after the gate (2026-11-16)

All six acquisitions received (user, 2026-11-15; "native text extraction so the quality may be an issue"). None has `<!-- N -->` page markers; pages are read off bare page lines; the study_prep checker warns on every row from these files, as expected.

| Work | File (under `../sources/sources/`) | Language | Pages / markers | Date | Damage |
| --- | --- | --- | --- | --- | --- |
| Hua XI, Einleitung des Herausgebers (Fleischer) | `husserl/husserl-hua-11-analysen-zur-passiven-synthesis-einleitung-des-herausgebers.md` | German | roman pages as bare lines (XIV … XXIV; "xXVI" for XVI) | written summer 1965, publ. 1966 (Einl. XXIV) | hyphenated breaks, quote marks garbled, footnote numerals misread ("17SsLOLT.") |
| Hua XI, Textkritischer Anhang | `husserl/husserl-hua-11-analysen-zur-passiven-synthesis-textkritischer-anhang.md` | German | bare page lines 442–529, some misread ("528" for 523, "518" twice) | 1966 | OCR ("dritien", "Ausden"); the dating table split one cell per line (p. 446) |
| Steinbock, *Analyses Concerning Passive and Active Synthesis* (CW IX, 2001) | `husserl/husserl-cw9-analyses-concerning-passive-and-active-synthesis.md` | English | English pages as bare lines (spaced digits), Hua pages in margin `[N]` | 2001 | margin marks damaged or lost (esp. §§ 16–18); print line numbers inside text; intro pages roman, mangled ("XXXÜ") |
| Hua XXXI, *Aktive Synthesen* (Breeur 2000) | `husserl/husserl-hua-31-…-passiven-synthesis.md` | German | bare page lines | lecture 1920/21, reworked; ed. 2000 | OCR ("Tei1", "tiber"); print line numbers inside sentences |
| *Erfahrung und Urteil* (Landgrebe 1939) | `husserl/husserl-erfahrung-und-urteil.md` | German | bare page lines | drafts 1928–30; Introduction after 1935 (Vorwort VIII–IX) | short lines, hyphenation; no English held |
| Holenstein, *Phänomenologie der Assoziation* (1972) | `holenstein/holenstein-…-husserl.md` | German | pages in running heads ("28 HUSSERLS …") | 1972 | umlauts lost; footnotes inline |
| Welton, *The Other Husserl* (2000) | `welton/welton-the-other-husserl-….md` | English | page numbers at top (even) / bottom (odd), checked pp. 220–254 | 2000 | library stamps at the start; otherwise clean |
