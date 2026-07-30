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
---
```

Don't set `wordpress_id` by hand — see below, it's written back
automatically.

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
