# commentaries/

AI-generated, paragraph-by-paragraph commentaries on phenomenological
texts. Published as a Jekyll site (GitHub Pages) — every `.md` file
here is built to a matching `.html` page.

## Structure

One subfolder per author, named as the author's lowercase last name
(`husserl/`, `heidegger/`, `derrida/`, ...). A subfolder can hold
several commentaries (e.g. `heidegger/` has separate commentaries for
the English *Being and Time* and the German *Sein und Zeit*, keyed to
different pagination systems).

## Always translate quotations

**Non-English text never appears without an English rendering — no
exceptions.** The primary texts are mostly German or French, so this
comes up constantly. It holds for commentary body text, for chat
responses discussing these files, and for commit messages.

**Ordering differs by context, and the difference is deliberate:**

- **In commentary body text, English leads.**
  [prompts/commentary-prompt](../prompts/commentary-prompt) §"Original-language
  terms and quotations" governs and is stricter than a bare
  translate-everything rule: cite the source word *in parentheses after*
  its English equivalent, never as the inline subject; retain the
  original only for a short fixed glossary of genuinely untranslatable
  terms of art, glossed on first use (e.g. Dasein — being-there); and
  **no bracketed original-language incipits anywhere**. Follow the
  prompt, not the sources-repo format below. These files publish live
  to WordPress and GitHub Pages on every push (see below), so an
  unglossed German block quotation goes straight to a public page.
- **In chat, notes and analysis, the original leads** — quote it first,
  then the English in square brackets, e.g. "Bewußtsein von etwas"
  [consciousness of something]. This matches
  [faultynode/sources](https://github.com/faultynode/sources) `CLAUDE.md`
  §"Always translate quotations", which is the mirror of this section.
  There the original is the evidence and the translation is the gloss;
  here the commentary *is* the English rendering, so the priority flips.

In both contexts:

- **Never replace the original with a translation** where the original
  is doing evidential work — a claim about what a text *says* needs the
  words it says it in.
- **Gloss terms of art on first use** per document; repeats within the
  same file don't need re-glossing.
- **Mark working renderings as such** rather than letting them read as
  a published translation. Note any recurring choice that could
  mislead.
- Sources already in English (e.g. the *Being and Time* translation,
  as against *Sein und Zeit*) need no gloss — but keep the two keyed
  separately, as the folder convention above already requires.

## Filename convention

`<author-last-name>-<title-slug>-commentary.md`, using the same
lowercase/hyphen slug rules as [prompts/filename-prompt.md](../prompts/filename-prompt.md)
(the source-file naming prompt, originally written for this repo's
now-removed `sources/` folder — that folder's content moved to the
separate [faultynode/sources](https://github.com/faultynode/sources)
repository, but the naming prompt still applies here) — transliterate
diacritics, strip punctuation, drop subtitles after a colon or dash.

One deviation from that prompt: Husserliana volumes here are slugged
`husserliana-<volume>-<title-slug>`, not `husserl-hua-<volume>-<title>`
as in the sources repo. This folder's commentary filenames don't need
to match the corresponding sources-repo filename — they're
independent, and existing ones may use an English title where the
source uses the German (e.g. `husserliana-3-ideas-i-commentary.md`
vs. `husserl-hua-3-1-ideen-i-...md` in faultynode/sources).

**Series volumes carry their number only when the file itself states
it.** Husserliana volumes are slugged
`husserliana-<volume>-<title-slug>-commentary.md`, Gesamtausgabe
volumes `heidegger-ga-<volume>-<title-slug>-commentary.md`. Per
[filename-prompt.md](../prompts/filename-prompt.md) §Process step 4,
never supply a volume number from outside knowledge — only from the
file's own text. Six Husserl commentaries therefore keep the plain
`husserl-<title>-commentary.md` form: `erfahrung-und-urteil` (not a
Husserliana volume at all), and `krisis`, `natur-und-geist`,
`prolegomena`, `formal-and-transcendental-logic`, `thing-and-space`,
which are Husserliana volumes that never cite their own volume
number. That split is deliberate; if one of those files later gains
an explicit volume citation, rename it then.

Title language follows the edition the commentary works from, not the
original — hence `husserl-thing-and-space-commentary.md` for a
commentary written against the English *Thing and Space*, even though
the volume is usually cited as *Ding und Raum*.

## Frontmatter

Every file opens with Jekyll frontmatter:

```yaml
---
layout: default
title: <human-readable page title, shown in the browser tab>
---
```

Don't set `wordpress_id` by hand — see below, it's written back
automatically.

## Raw-source conversion pipeline moved to sources repo

This repo used to have `pdf-input/`, `pdf-output/`, `ebook-input/`,
`ebook-output/` folders, a `tools/` folder of PDF/ebook-to-Markdown
conversion scripts, and two workflows
(`.github/workflows/pdf-to-markdown.yml`,
`.github/workflows/ebook-to-markdown.yml`) that ran them on push. All
of that moved (history preserved via `git subtree split`) to
[faultynode/sources](https://github.com/faultynode/sources), which
already held the `sources/` folder from an earlier move (see
"Filename convention" above). Nothing in this repo depends on that
pipeline; it only ever fed raw conversions into files that get
hand-reviewed and placed in the sources repo's `sources/` folder.

## Every push auto-publishes to WordPress and rebuilds index.html

`.github/workflows/wordpress-sync.yml` runs on every push that
touches a `.md` file. It:

1. Runs `scripts/sync_wordpress.py`, which globs
   `commentaries/*/*.md` — **exactly one directory level**, i.e.
   `<author>/<file>.md` — and publishes each one live to WordPress.
   A file with no `wordpress_id` in its frontmatter is treated as new
   and gets a fresh post created (and the resulting ID written back
   into the file); a file that already has one gets that post
   updated in place. There is no draft/staging step — every push
   goes live immediately.

   Every post is tagged with the author's last name, taken from the
   parent folder (`commentaries/husserl/...` → tag `Husserl`) and
   title-cased for display. The tag list is sent on updates as well
   as on creation, so the WordPress side is overwritten from the
   folder name each run — retagging a post by hand in WordPress
   won't stick. Where a folder holds a commentary *on* a secondary
   author (`mohanty/`, `bernet/`, `picht/`), the folder name is still
   what governs, so the tag is that author, not the philosopher they
   are writing about.
2. Runs `scripts/update_index.py`, which regenerates the
   `<div class="commentary-groups">` block in
   [../index.html](../index.html) from the same glob, grouping by
   parent-folder name into a `<details><summary>Author</summary><ul>`
   section per author. You do **not** need to hand-edit `index.html`
   for a normal commentary add/rename — the next push does it.
3. Commits both the updated files and `index.html` back to `main` as
   `github-actions[bot]`, tagged `[skip ci]`.

**The one-directory-level glob is deliberate, not incidental.** A
`.md` file placed directly in `commentaries/` (like this one) is
*not* a commentary and must **not** be picked up — earlier, before
the glob was narrowed from a recursive `**` to `*`, this very file
got auto-published as a live WordPress post titled "CLAUDE" (falling
back to the filename, since it has no `title` frontmatter), and the
`wordpress_id` write-back for it was silently lost by an unrelated
`git add` globbing quirk in the workflow — meaning every subsequent
push would have created *another* duplicate post. If you add any
other non-commentary `.md` file at the top level of `commentaries/`,
it's excluded from both scripts by construction; don't rely on this
by accident, but don't be surprised it's silent either.

Do add/rename `index.html` entries yourself only when doing manual
cleanup outside the normal flow (e.g. removing a stray auto-generated
entry) — otherwise leave it to the workflow.

When renaming a file with accented characters, double-check the link
still resolves after publish — iCloud Drive can silently re-encode
such filenames (NFD instead of NFC), which breaks the GitHub Pages
link even though the file looks identical locally.
