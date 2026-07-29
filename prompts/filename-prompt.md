Rename the files in <DIRECTORY> to follow the naming convention below.
Do not modify file contents. Preserve (and lowercase) the extension.

## Target format

Default:  <author-last-name>-<title>.<ext>
          e.g. bernet-la-vie-du-sujet.pdf

Two series override the default:

1. Husserliana volumes → husserl-hua-<volume>
   - Roman numerals become Arabic: Hua IV → husserl-hua-4
   - Slash-separated part-volumes become hyphens:
     Hua XLIII/2 → husserl-hua-43-2
   - Sub-series keep their abbreviation:
     Hua Mat VIII → husserl-hua-mat-8
     Hua Dok III/4 → husserl-hua-dok-3-4
   - Husserl works NOT in Husserliana use the default format
     (husserl-erfahrung-und-urteil.pdf)

2. Heidegger Gesamtausgabe volumes → heidegger-ga-<volume>
   - GA 19 → heidegger-ga-19
   - Heidegger works not from the GA (single editions, translations,
     correspondence outside the GA) use the default format
     (heidegger-sein-und-zeit.pdf)

## Normalization

- Lowercase throughout.
- Allowed characters: a-z, 0-9, hyphen. Nothing else.
- Spaces → hyphens.
- Transliterate diacritics and ligatures: ä→a, ö→o, ü→u, ß→ss,
  é/è/ê→e, ç→c, œ→oe. Greek in titles → Latin transliteration.
- Delete all other punctuation (apostrophes, commas, colons,
  periods, parentheses, quotation marks) rather than replacing it
  with a hyphen: "l'être" → letre, "Husserl's" → husserls.
- Collapse repeated hyphens; strip leading/trailing hyphens.
- Titles: use the main title only; drop the subtitle after a colon
  or dash. Keep leading articles (der/die/das/le/la/the).
- Title language follows the edition, not the original: a French
  translation is slugged from its French title.

## Author names

- Last name only, no first name or initials.
- Two authors: both last names, hyphenated, in title-page order
  (bernet-marbach-kern-an-introduction-to-husserlian-phenomenology).
- Three or more, or an edited collection: use the editor's last
  name and append -ed (mohanty-ed-readings-on-husserl).
- Compound and particled names keep their parts:
  van-breda, merleau-ponty, de-boer.

## Collisions

If two files would produce the same name, append the publication
year (heidegger-sein-und-zeit-1927, heidegger-sein-und-zeit-2006).
If still identical, append -a, -b.

## Process

1. Where the current filename is uninformative (scanner output,
   ISBN strings, "document (3).pdf"), open the file and read the
   title page or embedded metadata to identify author, title,
   series, and volume.
2. Print a dry-run table of old name → new name for every file,
   plus a separate list of any file you could not confidently
   identify. Do not rename anything yet.
3. Wait for my approval, then execute the renames.
4. Never guess a Hua or GA volume number. If it isn't stated in
   the file, leave the file untouched and list it.