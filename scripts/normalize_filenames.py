#!/usr/bin/env python3
"""Rename commentaries to the filename convention, and carry every reference along.

The convention is commentaries/CLAUDE.md §"Filename convention":

    commentaries/<author>/<author>-<title-slug>-commentary.md

with the slug rules of faultynode/prompts repo-maintenance/filename-prompt.md
(lowercase; a-z, 0-9 and hyphen only; diacritics transliterated; other
punctuation deleted, not hyphenated) and this repo's one deviation:
Husserliana volumes are husserliana-<n>-..., not husserl-hua-<n>-....

    python3 scripts/normalize_filenames.py              # dry run: print the plan
    python3 scripts/normalize_filenames.py --check      # exit 1 if anything would change
    python3 scripts/normalize_filenames.py --apply      # rename, rewrite references
    python3 scripts/normalize_filenames.py --apply --rename-folder fanck=franck

What it does mechanically:

  - slugs the stem and the author folder (lowercase, transliterate, delete
    punctuation, spaces and underscores to hyphens, collapse hyphens);
  - husserl-hua-<n>- becomes husserliana-<n>-;
  - prepends the folder's author slug when the name lacks it, and appends
    -commentary when the name lacks it.

What it never does, because the filename prompt makes each a judgement:
drop a subtitle, supply a Hua or GA volume number, or identify a file from
an uninformative name. Those stay with the source-filename-normalizer skill.

What it refuses and reports for a human (exit 2 under --check, a warning
under --apply): a name whose author prefix looks like a misspelling of its
folder (franck-... in fanck/ - which one is wrong is not mechanical; settle
it with --rename-folder), a target that already exists, and characters with
no transliteration (Greek, Cyrillic).

Every rename carries its references, because a slug is an address
everywhere in this repo (synthesis records, chronology.json, the lexicon,
run files, outputs, index.html, links between commentaries):

  - the old path, slug and folder are rewritten in every tracked text file,
    in raw, NFD, %20-escaped and percent-encoded spellings - except
    corpus.json, the ledgers and the status files, which are generated and must be
    rebuilt (synthesis_index.py, synthesis_ledger.py --all,
    synthesis_status.py) after an --apply;
  - a file that was already committed under its old name gets a
    redirect_from entry, so its old GitHub Pages URL keeps resolving
    (jekyll-redirect-from, enabled in _config.yml);
  - where those edits change a commentary's bytes, a synthesis record whose
    source_sha256 matched the file before the edit is carried forward to the
    new digest. synthesis_validate.py still checks every quote.

Standard library only, like the synthesis scripts.
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import unicodedata
from urllib.parse import quote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CDIR = "commentaries"
# Rebuilt from the tree after a rename; rewriting them would only race the rebuild.
GENERATED = ("synthesis/corpus.json", "synthesis/STATUS.md", "synthesis/READINESS.md",
             "synthesis/GAPS.md", "synthesis/ledgers/")
RECORD_DIRS = ("synthesis/extractions/", "synthesis/inheritance/")
TRANSLIT = {"ß": "ss", "æ": "ae", "Æ": "ae", "œ": "oe", "Œ": "oe", "ø": "o", "Ø": "o",
            "ł": "l", "Ł": "l", "đ": "d", "Đ": "d", "ð": "d", "þ": "th", "Þ": "th"}
# Name prefixes allowed besides "<author>-" (commentaries/CLAUDE.md: Husserliana volumes).
EXTRA_PREFIXES = {"husserl": ("husserliana-",)}
SLUG_CHARS = re.compile(r"[A-Za-z0-9-]")


def nfc(s):
    return unicodedata.normalize("NFC", s)


def untransliterable(s):
    s = "".join(TRANSLIT.get(c, c) for c in nfc(s))
    s = "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))
    return sorted({c for c in s if ord(c) > 127 and unicodedata.category(c).startswith("L")})


def slugify(s):
    s = "".join(TRANSLIT.get(c, c) for c in nfc(s))
    s = "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c)).lower()
    s = re.sub(r"[\s_]+", "-", s)
    s = re.sub(r"[^a-z0-9-]", "", s)
    s = re.sub(r"-{2,}", "-", s).strip("-")
    # A French elision whose apostrophe became a space (the web uploader does this):
    # "Passions de l ame" -> passions-de-lame, as "l'âme" would give.
    return re.sub(r"(?:^|(?<=-))(l|d|j|qu)-(?=[aeiouyh])", r"\1", s)


def distance(a, b):
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def target_stem(stem, author):
    """Return (new_stem, problem). problem is None or a reason a human must decide."""
    bad = untransliterable(stem)
    if bad:
        return None, "no transliteration for %s" % " ".join(bad)
    s = slugify(stem)
    s = re.sub(r"^husserl-hua-(\d+(?:-\d+)?)-", r"husserliana-\1-", s)
    prefixes = (author + "-",) + EXTRA_PREFIXES.get(author, ())
    if not s.startswith(prefixes):
        first = s.split("-")[0]
        if first and distance(first, author) <= (1 if len(author) < 7 else 2):
            return None, ("author prefix '%s' looks like a misspelling of folder '%s' "
                          "(or the reverse); settle it with --rename-folder" % (first, author))
        s = "%s-%s" % (author, s)
    if not s.endswith("-commentary"):
        s = re.sub(r"-?commentary$", "", s) + "-commentary"
    return s, None


def git(*args, check=True):
    return subprocess.run(["git", *args], cwd=ROOT, check=check, capture_output=True,
                          text=True, encoding="utf-8")


def in_git():
    return git("rev-parse", "--is-inside-work-tree", check=False).returncode == 0


def tracked(rel):
    return git("ls-files", "--error-unmatch", "--", rel, check=False).returncode == 0


def committed(rel):
    return git("cat-file", "-e", "HEAD:" + nfc(rel), check=False).returncode == 0


def fingerprint(path):
    """(content digest ignoring line endings, first H1) - to catch a re-upload of a
    commentary that already exists under a conforming name."""
    with open(path, "rb") as f:
        data = f.read().replace(b"\r\n", b"\n")
    m = re.search(rb"(?m)^# +(.+?)\s*$", data)
    return hashlib.sha256(data).hexdigest(), (nfc(m.group(1).decode("utf-8", "replace")) if m else None)


def plan(folder_overrides):
    renames, problems = [], []
    base = os.path.join(ROOT, CDIR)
    targets = {}
    prints = {"%s/%s/%s" % (CDIR, d, n): fingerprint(os.path.join(base, d, n))
              for d in os.listdir(base) if os.path.isdir(os.path.join(base, d))
              for n in os.listdir(os.path.join(base, d)) if n.lower().endswith(".md")}
    for folder in sorted(os.listdir(base)):
        if not os.path.isdir(os.path.join(base, folder)):
            continue
        author = folder_overrides.get(nfc(folder)) or slugify(folder)
        for name in sorted(os.listdir(os.path.join(base, folder))):
            stem, ext = os.path.splitext(name)
            if ext.lower() != ".md" or not os.path.isfile(os.path.join(base, folder, name)):
                continue
            old = "%s/%s/%s" % (CDIR, folder, name)
            new_stem, problem = target_stem(stem, author)
            if problem:
                problems.append((old, problem))
                continue
            new = "%s/%s/%s.md" % (CDIR, author, new_stem)
            if nfc(old) != new:
                digest, title = prints[old]
                twin = next((p for p, (d, t) in sorted(prints.items()) if p != old and d == digest), None)
                if twin:
                    problems.append((old, "duplicate of %s (identical apart from line endings); "
                                          "delete one by hand" % twin))
                    continue
                twin = next((p for p, (d, t) in sorted(prints.items()) if p != old and title and t == title), None)
                if twin:
                    problems.append((old, "same title as %s - a revised upload? replace that file "
                                          "by hand, or retitle" % twin))
                    continue
            if new in targets:
                problems.append((old, "would collide with %s" % targets[new]))
                continue
            targets[new] = old
            if nfc(old) != new:
                renames.append((old, new))
    # A target that exists on disk and is not the file being renamed (case-insensitively,
    # so a case-only rename on Windows or macOS is not mistaken for a collision).
    sources = {nfc(o).lower() for o, _ in renames}
    for old, new in list(renames):
        if os.path.exists(os.path.join(ROOT, new)) and new.lower() not in sources | {nfc(old).lower()}:
            renames.remove((old, new))
            problems.append((old, "target %s already exists" % new))
    return renames, problems


def move(old, new):
    src, dst = os.path.join(ROOT, old), os.path.join(ROOT, new)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    use_git = in_git() and tracked(old)
    if nfc(old).lower() == new.lower():  # case-only: go through a temporary name
        tmp = new + ".renaming"
        git("mv", old, tmp) if use_git else os.rename(src, os.path.join(ROOT, tmp))
        old, src = tmp, os.path.join(ROOT, tmp)
    git("mv", old, new) if use_git else os.rename(src, dst)
    try:
        os.rmdir(os.path.dirname(os.path.join(ROOT, old)))
    except OSError:
        pass


def variants(s):
    out = {s, nfc(s), unicodedata.normalize("NFD", s)}
    for v in list(out):
        out.add(v.replace(" ", "%20"))
        out.add(quote(v))
    return out


def replacement_pairs(renames, folder_moves):
    pairs = {}
    for old, new in renames:
        old_noext, new_noext = os.path.splitext(old)[0], os.path.splitext(new)[0]
        for v in variants(old_noext):
            pairs[v] = new_noext
        old_slug, new_slug = os.path.basename(old_noext), os.path.basename(new_noext)
        if nfc(old_slug) != new_slug:
            for v in variants(old_slug):
                pairs[v] = new_slug
    for old, new in folder_moves:
        for v in variants("%s/%s/" % (CDIR, old)):
            pairs[v] = "%s/%s/" % (CDIR, new)
    return sorted(pairs.items(), key=lambda kv: -len(kv[0]))


def rewrite_references(pairs):
    files = git("ls-files", "-z").stdout.split("\0")
    patterns = [(re.compile(r"(?<![A-Za-z0-9-])%s(?![A-Za-z0-9-])" % re.escape(o)
                            if SLUG_CHARS.match(o[-1]) else
                            r"(?<![A-Za-z0-9-])%s" % re.escape(o)), n) for o, n in pairs]
    touched = []
    for rel in files:
        if not rel or rel.startswith(GENERATED) or not os.path.isfile(os.path.join(ROOT, rel)):
            continue
        path = os.path.join(ROOT, rel)
        try:
            with open(path, encoding="utf-8", newline="") as f:
                text = f.read()
        except (UnicodeDecodeError, OSError):
            continue
        new_text = text
        for pat, repl in patterns:
            new_text = pat.sub(lambda m: repl, new_text)
        if new_text != text:
            with open(path, "w", encoding="utf-8", newline="") as f:
                f.write(new_text)
            touched.append(rel)
    return touched


def add_redirect(path, url):
    with open(path, encoding="utf-8", newline="") as f:
        text = f.read()
    nl = "\r\n" if "\r\n" in text[:200] else "\n"
    item = "  - " + json.dumps(url, ensure_ascii=False)
    m = re.match(r"---\r?\n(.*?)(\r?\n)---[ \t]*(\r?\n|$)", text, re.S)
    if not m:
        text = "---" + nl + "redirect_from:" + nl + item + nl + "---" + nl + nl + text
    else:
        head = m.group(1)
        if json.dumps(url, ensure_ascii=False) in head:
            return False
        block = re.search(r"(?m)^redirect_from:[ \t]*(\S.*)?$", head)
        if block and block.group(1):  # scalar form: make it a list
            head = head[:block.start()] + "redirect_from:" + nl + "  - " + block.group(1) + nl + item + head[block.end():]
        elif block:
            head = head[:block.end()] + nl + item + head[block.end():]
        else:
            head = head + nl + "redirect_from:" + nl + item
        text = "---" + nl + head + text[m.end(1):]
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)
    return True


def digests(path):
    """(raw, LF-normalized) sha256. A record hashes the file as CI sees it; on a Windows
    checkout with core.autocrlf the working copy is CRLF while the committed blob is LF,
    so a record can match either form."""
    with open(path, "rb") as f:
        data = f.read()
    return hashlib.sha256(data).hexdigest(), hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()


def carry_digests(changed):
    """changed: {slug: (before, after)}, each a digests() pair. Only records that were
    current before the edit move, and they move to the same form they matched."""
    touched = []
    for d in RECORD_DIRS:
        for dirpath, _, names in os.walk(os.path.join(ROOT, d)):
            for name in names:
                if not name.endswith(".json"):
                    continue
                path = os.path.join(dirpath, name)
                with open(path, encoding="utf-8", newline="") as f:
                    text = f.read()
                try:
                    slug = json.loads(text).get("commentary")
                except ValueError:
                    continue
                if slug not in changed:
                    continue
                before, after = changed[slug]
                for old_sha, new_sha in zip(before, after):
                    if old_sha in text:
                        with open(path, "w", encoding="utf-8", newline="") as f:
                            f.write(text.replace(old_sha, new_sha))
                        touched.append(os.path.relpath(path, ROOT).replace(os.sep, "/"))
                        break
    return touched


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="exit 1 if a rename is due, 2 if a human must decide")
    mode.add_argument("--apply", action="store_true", help="rename and rewrite references")
    ap.add_argument("--rename-folder", action="append", default=[], metavar="OLD=NEW",
                    help="settle a folder name by hand (repeatable)")
    ap.add_argument("--touched", metavar="FILE", help="write the paths --apply changed, NUL-separated")
    args = ap.parse_args()

    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")
    overrides = {}
    for spec in args.rename_folder:
        old, _, new = spec.partition("=")
        if not new or slugify(new) != new:
            ap.error("--rename-folder wants OLD=NEW with NEW already a slug: %r" % spec)
        overrides[nfc(old)] = new

    renames, problems = plan(overrides)
    for old, new in renames:
        print("rename  %s\n     -> %s" % (old, new))
    annotate = os.environ.get("GITHUB_ACTIONS") == "true"
    for old, why in problems:
        print(("::warning file=%s::%s" if annotate else "HUMAN   %s: %s") % (old, why))
    if not renames and not problems:
        print("All commentary filenames conform.")

    if args.check:
        sys.exit(2 if problems else 1 if renames else 0)
    if not args.apply:
        if renames:
            print("\nDry run. --apply to rename.")
        return

    touched = []
    if renames:
        folder_moves = sorted({(o.split("/")[1], n.split("/")[1]) for o, n in renames
                               if nfc(o.split("/")[1]) != n.split("/")[1]})
        redirect = {new: "/" + nfc(os.path.splitext(old)[0]) + ".html"
                    for old, new in renames if in_git() and committed(old)}
        for old, new in renames:
            move(old, new)
        before = {new: digests(os.path.join(ROOT, new)) for _, new in renames}
        before.update({rel: digests(os.path.join(ROOT, rel))
                       for rel in git("ls-files", "--", CDIR).stdout.splitlines() if rel.endswith(".md")})
        touched += [new for _, new in renames]
        touched += rewrite_references(replacement_pairs(renames, folder_moves))
        for new, url in redirect.items():
            add_redirect(os.path.join(ROOT, new), url)
        changed = {}
        for rel, old in before.items():
            path = os.path.join(ROOT, rel)
            if os.path.isfile(path) and digests(path) != old:
                changed[os.path.splitext(os.path.basename(rel))[0]] = (old, digests(path))
        touched += carry_digests(changed)
        print("\n%d renamed, %d files rewritten. Rebuild: synthesis_index.py, "
              "synthesis_ledger.py --all, synthesis_status.py." % (len(renames), len(set(touched)) - len(renames)))
    if args.touched:
        with open(args.touched, "w", encoding="utf-8") as f:
            f.write("".join(p + "\0" for p in sorted(set(touched))))


if __name__ == "__main__":
    main()
