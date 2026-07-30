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

Known inconsistency: `husserliana-1-cartesianische-meditationen.md`
is missing the `-commentary` suffix that every other file has. Match
new files to the `-commentary` suffix, not to that one.

## Frontmatter

Every file opens with Jekyll frontmatter:

```yaml
---
layout: default
title: <human-readable page title, shown in the browser tab>
wordpress_id: <only on posts migrated from the old WordPress site>
---
```

Omit `wordpress_id` on new commentaries — it's a migration artifact,
not a convention to continue.

## index.html must be updated manually

The site homepage ([../index.html](../index.html)) hand-lists every
commentary inside a `<details><summary>Author</summary><ul>` block,
one `<li><a href="commentaries/<author>/<file>.html">Title</a></li>`
per file (note: `.html`, not `.md` — Jekyll's build target). Adding,
renaming, or deleting a commentary file does **not** update this
list automatically — you must edit `index.html` in the same change,
or the page becomes unreachable from the homepage even though it
still builds and is live at its own URL.

When renaming a file with accented characters, double-check the link
still resolves after publish — iCloud Drive can silently re-encode
such filenames (NFD instead of NFC), which breaks the GitHub Pages
link even though the file looks identical locally.
