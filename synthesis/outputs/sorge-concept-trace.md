# Sorge — concept trace

Stage 4 output type 1, over `synthesis/ledgers/sorge-ledger.md`. Every row
restates a unit already in that ledger; nothing here is drawn from the
commentaries directly.

**Scope.** Two commentaries carry extraction records for this theme: GA 19
(complete pass) and GA 20 (partial — Chapter Four, §§ 27–32). Twenty-five
further commentaries carry the theme's terms and have never been scanned,
including the two on *Sein und Zeit* and the one on GA 18. Nothing below
is a claim about those files. Where a row says a term is absent, that is
a checked negative recorded by an extraction pass and re-verified by
`scripts/synthesis_validate.py`; where this trace is silent, it is silent.

Locators are given as unit ids in the table and resolved in full at the
foot. Citations in the *Cite* column are the primary-text citations the
commentary itself supplies; GA 19's units carry none.

## Occurrences, in date order

| Unit | Date | Cite | Term | Status | What is claimed there |
|---|---|---|---|---|---|
| `sorge/ga19/001` | WS 1924/25 | — | *Sorge* | presupposed | Sorge is listed among the terms the commentary holds in German throughout, glossed as care, alongside ἀλήθεια, λόγος, οὐσία and Dasein. |
| `sorge/ga20/001` | SS 1925 | GA 20 § 27 | *Sorge* | introduced | The being-structure of in-being that the analysis has been driving at is named care, and the explication is ordered into four phenomena with care last. |
| `sorge/ga20/002` | SS 1925 | GA 20 § 28a | *care* | presupposed | Disposedness is derived from care: the world is experienced as threatening or unthreatening only because Dasein is itself care, and not because a caring Dasein apprehends it so. |
| `sorge/ga20/003` | SS 1925 | GA 20 § 31a | *Sorge* | introduced | Care is the term for the being of Dasein as such, with the formal structure: a being to which, in its being-in-the-world, this being itself is at issue. |
| `sorge/ga20/004` | SS 1925 | GA 20 § 31a | *Urstruktur* | introduced | Care is marked a pre-structure and explicitly the penultimate phenomenon, with time named as the last nexus of the being of Dasein. |
| `sorge/ga20/005` | SS 1925 | GA 20 § 31a | *Besorgen* | revised | Concern, which carried the earlier analysis of everyday commerce with the world, is subordinated to care as one of its being-modes. |
| `sorge/ga20/006` | SS 1925 | GA 20 § 31a | *Sich-vorweg-sein* | introduced | The total formal structure of care is given in two moments: being-ahead-of-itself, and always-already-being-alongside something. |
| `sorge/ga20/007` | SS 1925 | GA 20 § 31a | *Darben* | introduced | The not-yet-having belonging to being-out-for is named want or privation and distinguished from a sheer objective not-having. |
| `sorge/ga20/008` | SS 1925 | GA 20 § 31b | *Drang* | revised | Urge and hang are founded modifications of care in which one moment predominates and covers the rest; care is the condition of their possibility and is not composed out of them. |
| `sorge/ga20/009` | SS 1925 | GA 20 § 31, Cura fable | *Sorge* | presupposed | Heidegger dates his first striking on the phenomenon of care to seven years before the course, in work on the ontological foundations of Augustinian anthropology. |
| `sorge/ga20/010` | SS 1925 | GA 20 § 32 | *Sorge* | presupposed | Care is the primary wholeness of Dasein's being-constitution; the equiprimordial structures belong to it rather than composing it. |

By status: introduced 5, presupposed 4, revised 2, criticized 0.

By work: GA 19 (WS 1924/25), 1 unit. GA 20 (SS 1925), 10 units, all but one
of them in § 31.

## Checked absences, in date order

| Locator | Terms checked | Expected because |
|---|---|---|
| GA 19, § 8a (φρόνησις: Dasein itself) | Sorge, Besorgen, Fürsorge, Bekümmerung | The τέλος of φρόνησις is fixed as Dasein itself, and Dasein as the οὗ ἕνεκα for the sake of which it acts — a being for which its own being is at issue, which is the structure the commentary's glossary reserves the word Sorge for. |
| GA 19, § 8b (φρόνησις as ἀ-ληθεύειν) | Sorge, Besorgen, Fürsorge, Bekümmerung | Dasein is described as constantly in danger of being concealed from itself by itself; the analysis proceeds in the vocabulary of ἀληθεύειν and πρᾶξις throughout. |
| GA 19, § 25a (εὐδαιμονία) | Sorge, Besorgen, Fürsorge, Bekümmerung | εὐδαιμονία is given an ontological sense as the completed being of the ψυχή, i.e. as what human Dasein is out for. |
| GA 20, § 12 (neglect of the being of the intentional) | all registered terms | The section states that neglect as the decisive omission of the phenomenology being criticized — the question § 31 answers with care. |
| GA 20, § 35 (wanting-to-have-conscience, being-guilty) | all registered terms | Conscience and being-guilty are treated as Dasein-phenomena of the same rank as the death analysis of § 34, which does work in the vocabulary of care. |

The GA 19 absences check the German family only: the commentary uses the
English "care" non-technically in each of those three sections, which the
extraction records note. The GA 20 § 35 record notes that the section runs
to 358 words and that the absence may belong to the commentary's
compression rather than to the course.

## Gaps flagged

`gap-004`, `gap-005`, `gap-006` in `synthesis/gaps.json`. Each marks a
claim this trace could have made and cannot support.

## Locators

    sorge/ga19/001  heidegger-ga-19-platon-sophistes-commentary#h2-orientation-the-traps-this-course-sets
    sorge/ga20/001  heidegger-ga-20-prolegomena-zur-geschichte-des-zeitbegriffs-commentary#h4-s-27-in-being-and-care-outline
    sorge/ga20/002  heidegger-ga-20-prolegomena-zur-geschichte-des-zeitbegriffs-commentary#h4-s-28-the-phenomenon-of-uncoveredness-entdecktheit
    sorge/ga20/003  heidegger-ga-20-prolegomena-zur-geschichte-des-zeitbegriffs-commentary#h4-s-31-care-as-the-being-of-dasein
    sorge/ga20/004  heidegger-ga-20-prolegomena-zur-geschichte-des-zeitbegriffs-commentary#h4-s-31-care-as-the-being-of-dasein
    sorge/ga20/005  heidegger-ga-20-prolegomena-zur-geschichte-des-zeitbegriffs-commentary#h4-s-31-care-as-the-being-of-dasein
    sorge/ga20/006  heidegger-ga-20-prolegomena-zur-geschichte-des-zeitbegriffs-commentary#h4-s-31-care-as-the-being-of-dasein
    sorge/ga20/007  heidegger-ga-20-prolegomena-zur-geschichte-des-zeitbegriffs-commentary#h4-s-31-care-as-the-being-of-dasein
    sorge/ga20/008  heidegger-ga-20-prolegomena-zur-geschichte-des-zeitbegriffs-commentary#h4-s-31-care-as-the-being-of-dasein
    sorge/ga20/009  heidegger-ga-20-prolegomena-zur-geschichte-des-zeitbegriffs-commentary#h4-s-31-care-as-the-being-of-dasein
    sorge/ga20/010  heidegger-ga-20-prolegomena-zur-geschichte-des-zeitbegriffs-commentary#h4-s-32-the-result-and-the-task-of-the-fundamental-dasein-analysis-the-working-out

    absences
    GA 19 § 8a      heidegger-ga-19-platon-sophistes-commentary#h5-a-the-object-of-phronesis-dasein-itself-the-determination-of-the-telos-of-phrone
    GA 19 § 8b      heidegger-ga-19-platon-sophistes-commentary#h5-b-phronesis-as-a-letheyein-edone-and-lype-sophrosyne-phronesis-as-struggle-again
    GA 19 § 25a     heidegger-ga-19-platon-sophistes-commentary#h5-a-the-idea-of-eydaimonia-nic-eth-x-6-the-ontological-sense-of-eydaimonia-as-the
    GA 20 § 12      heidegger-ga-20-prolegomena-zur-geschichte-des-zeitbegriffs-commentary#h4-s-12-exhibiting-the-neglect-of-the-question-of-the-being-of-the-intentional
    GA 20 § 35      heidegger-ga-20-prolegomena-zur-geschichte-des-zeitbegriffs-commentary#h4-s-35-the-phenomenon-of-wanting-to-have-conscience-and-of-being-guilty
