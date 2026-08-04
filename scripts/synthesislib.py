#!/usr/bin/env python3
"""Shared helpers for the commentary synthesis pipeline.

Standard library only. The synthesis scripts run in CI and on a laptop
with nothing installed, so nothing here may import a third-party
package - not even `frontmatter`, which the WordPress sync uses.

Two ideas do most of the work:

`section_id`  Every commentary heading gets a deterministic, stable id.
              A locator is `<commentary-slug>#<section-id>`, and that is
              the only address the extraction records are allowed to
              use. `kramdown_id` computes the *other* id - the anchor
              GitHub Pages actually renders - for building links.

`corpus.json` A generated index of the whole commentary corpus:
              heading tree, line spans, word counts, file digests. The
              validator resolves locators against it, so no script has
              to re-parse 26,000 lines of markdown to check one claim.
"""

import hashlib
import json
import os
import re
import unicodedata

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMMENTARIES_DIR = os.path.join(REPO_ROOT, "commentaries")
SYNTHESIS_DIR = os.path.join(REPO_ROOT, "synthesis")
CORPUS_PATH = os.path.join(SYNTHESIS_DIR, "corpus.json")
SITE_BASE = "https://faultynode.github.io/commentaries"

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
FENCE_RE = re.compile(r"^\s*(```|~~~)")

# Half the headings in this corpus are Greek (φρόνησις, ἀληθεύειν, οὐσία).
# Dropping them to hyphens would leave locators like `h5-a-the-of-in-contrast-
# to-the-of`, which name a section without saying which. Transliterated, the
# id stays readable and stays greppable. Accents are gone by then: NFKD
# decomposes them and the combining marks are stripped before this runs.
GREEK = {
    "α": "a", "β": "b", "γ": "g", "δ": "d", "ε": "e", "ζ": "z", "η": "e",
    "θ": "th", "ι": "i", "κ": "k", "λ": "l", "μ": "m", "ν": "n", "ξ": "x",
    "ο": "o", "π": "p", "ρ": "r", "σ": "s", "ς": "s", "τ": "t", "υ": "y",
    "φ": "ph", "χ": "ch", "ψ": "ps", "ω": "o",
}


# --------------------------------------------------------------------- ids


def section_id(text, level):
    """Canonical, locator-grade id for a heading.

    Deliberately not kramdown's algorithm. Kramdown strips every leading
    non-letter, so `## § 1. Necessity` and `## Necessity` collapse to the
    same anchor - fine for a URL, useless for a locator that has to name
    one section unambiguously. This keeps the section number, which in a
    commentary keyed to sections is the most stable part of the heading:
    an editor may reword a title, but `§ 44` stays `§ 44`.
    """
    t = unicodedata.normalize("NFKD", text)
    t = t.replace("§", "s").replace("&", " and ")
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = t.lower()
    t = "".join(GREEK.get(c, c) for c in t)
    t = re.sub(r"[^a-z0-9]+", "-", t).strip("-")
    t = re.sub(r"-{2,}", "-", t)
    if not t:
        t = "section"
    return "h%d-%s" % (level, t[:80].rstrip("-"))


def kramdown_id(text):
    """Best-effort reproduction of the anchor Jekyll/kramdown emits.

    Link-building only - never a locator. WordPress renders the same
    files through python-markdown's `toc` extension, which slugifies
    differently again, so a locator keyed to either dialect would break
    on one of the two published surfaces.
    """
    t = unicodedata.normalize("NFKD", text)
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = t.lower()
    t = re.sub(r"^[^a-z]*", "", t)
    t = re.sub(r"[^a-z0-9\s-]", "", t)
    t = t.strip().replace(" ", "-")
    return t or "section"


def normalize_quote(s):
    """Collapse the differences that should never fail a quote check.

    Smart quotes, non-breaking spaces and line wrapping vary between the
    file and anything that has been through a model's context. Wording
    does not, and that is what the check is for.
    """
    s = unicodedata.normalize("NFKC", s)
    for a, b in (
        ("‘", "'"), ("’", "'"), ("“", '"'), ("”", '"'),
        ("–", "-"), ("—", "-"), ("−", "-"), (" ", " "),
        ("…", "..."),
    ):
        s = s.replace(a, b)
    s = re.sub(r"[*_`]", "", s)
    return re.sub(r"\s+", " ", s).strip().lower()


# ------------------------------------------------------------------ files


def read_text(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def split_frontmatter(text):
    """Return (dict, body, body_offset_in_lines).

    A deliberately small YAML subset: flat `key: value` pairs, which is
    all these files carry. Quoted values are unquoted; everything else
    is left as a string.
    """
    if not text.startswith("---"):
        return {}, text, 0
    lines = text.split("\n")
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return {}, text, 0
    meta = {}
    for line in lines[1:end]:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, sep, value = line.partition(":")
        if not sep:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1].replace("''", "'")
        meta[key.strip()] = value
    return meta, "\n".join(lines[end + 1:]), end + 1


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, sort_keys=False)
        f.write("\n")


def write_text(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


# ----------------------------------------------------------------- corpus


def parse_sections(body, line_offset):
    """Split a commentary body into a flat list of sections.

    Line numbers are 1-based against the whole file, so a locator can be
    followed with an editor jump. Fenced code blocks are skipped: a `#`
    inside one is not a heading. (No commentary uses fences today. The
    guard costs four lines and removes a class of silent mis-indexing.)
    """
    sections = []
    stack = []
    in_fence = False
    lines = body.split("\n")

    for i, line in enumerate(lines):
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = HEADING_RE.match(line)
        if not m:
            continue
        level = len(m.group(1))
        title = re.sub(r"[*_`]", "", m.group(2)).strip()
        while stack and stack[-1]["level"] >= level:
            stack.pop()
        sections.append({
            "id": None,
            "level": level,
            "title": title,
            "path": [s["title"] for s in stack] + [title],
            "anchor": kramdown_id(title),
            "line_start": line_offset + i + 1,
            "line_end": None,
        })
        stack.append(sections[-1])

    for n, sec in enumerate(sections):
        sec["line_end"] = (
            sections[n + 1]["line_start"] - 1 if n + 1 < len(sections)
            else line_offset + len(lines)
        )

    seen = {}
    for sec in sections:
        base = section_id(sec["title"], sec["level"])
        seen[base] = seen.get(base, 0) + 1
        sec["id"] = base if seen[base] == 1 else "%s-%d" % (base, seen[base])

    # Kramdown suffixes a repeated anchor -1, -2, ... Greek headings collapse
    # to near-nothing under its rules, so repeats are common here and an
    # unsuffixed link would land on the wrong section.
    seen = {}
    for sec in sections:
        base = sec["anchor"]
        seen[base] = seen.get(base, 0) + 1
        if seen[base] > 1:
            sec["anchor"] = "%s-%d" % (base, seen[base] - 1)
    return sections


def index_commentary(path):
    rel = os.path.relpath(path, REPO_ROOT).replace(os.sep, "/")
    text = read_text(path)
    meta, body, offset = split_frontmatter(text)
    sections = parse_sections(body, offset)
    lines = text.split("\n")

    for sec in sections:
        chunk = "\n".join(lines[sec["line_start"]:sec["line_end"]])
        sec["words"] = len(chunk.split())

    slug = os.path.splitext(os.path.basename(path))[0]
    author = os.path.basename(os.path.dirname(path))
    h1 = next((s["title"] for s in sections if s["level"] == 1), None)
    return {
        "slug": slug,
        "path": rel,
        "author": author,
        # Not every commentary carries a frontmatter title; those that don't
        # still open with an H1, which is a better name than the slug.
        "title": meta.get("title") or h1 or slug,
        "wordpress_id": meta.get("wordpress_id"),
        "sha256": sha256_of(path),
        "lines": len(lines),
        "words": len(text.split()),
        "url": "%s/%s.html" % (SITE_BASE, os.path.splitext(rel)[0]),
        "sections": sections,
    }


def build_corpus():
    docs = []
    for author in sorted(os.listdir(COMMENTARIES_DIR)):
        adir = os.path.join(COMMENTARIES_DIR, author)
        if not os.path.isdir(adir):
            continue
        for name in sorted(os.listdir(adir)):
            if name.endswith(".md"):
                docs.append(index_commentary(os.path.join(adir, name)))
    return {"schema_version": 1, "documents": docs}


def load_corpus():
    if not os.path.exists(CORPUS_PATH):
        raise SystemExit(
            "synthesis/corpus.json is missing - run "
            "`python3 scripts/synthesis_index.py` first."
        )
    return load_json(CORPUS_PATH)


def corpus_map(corpus):
    return {d["slug"]: d for d in corpus["documents"]}


def section_map(doc):
    return {s["id"]: s for s in doc["sections"]}


def parse_locator(locator):
    """`slug#section-id` -> (slug, section_id). Raises on anything else."""
    if "#" not in locator:
        raise ValueError("locator must be '<commentary-slug>#<section-id>'")
    slug, _, sec = locator.partition("#")
    if not slug or not sec:
        raise ValueError("locator must be '<commentary-slug>#<section-id>'")
    return slug, sec


def section_text(doc, sec):
    """The raw markdown of one section, headings included."""
    lines = read_text(os.path.join(REPO_ROOT, doc["path"])).split("\n")
    return "\n".join(lines[sec["line_start"] - 1:sec["line_end"]])


def section_url(doc, sec):
    return "%s#%s" % (doc["url"], sec["anchor"])


# -------------------------------------------------------------- registries

EXTRACTIONS_DIR = os.path.join(SYNTHESIS_DIR, "extractions")
INHERITANCE_DIR = os.path.join(SYNTHESIS_DIR, "inheritance")
LEDGERS_DIR = os.path.join(SYNTHESIS_DIR, "ledgers")
UNDATED = 9999


def registry(name):
    path = os.path.join(SYNTHESIS_DIR, name + ".json")
    if not os.path.exists(path):
        return None
    return load_json(path)


def themes():
    data = registry("themes") or {"themes": []}
    return {t["id"]: t for t in data["themes"]}


def chronology():
    data = registry("chronology") or {"entries": []}
    return {e["commentary"]: e for e in data["entries"]}


def entry_year(entry):
    """Earliest dated stratum, or UNDATED. Never falls back to volume order."""
    years = [s["year_start"] for s in entry["strata"] if s["year_start"] is not None]
    return min(years) if years else UNDATED


def stratum_year(stratum):
    return stratum["year_start"] if stratum["year_start"] is not None else UNDATED


def stratum_label(entry, stratum_id):
    for s in entry["strata"]:
        if s["id"] == stratum_id:
            return s["label"]
    return stratum_id


def iter_records(root):
    if not os.path.isdir(root):
        return
    for dirpath, _, names in os.walk(root):
        for name in sorted(names):
            if name.endswith(".json"):
                path = os.path.join(dirpath, name)
                yield os.path.relpath(path, REPO_ROOT).replace(os.sep, "/"), \
                    load_json(path)


def load_extractions(theme=None):
    out = []
    for rel, rec in iter_records(EXTRACTIONS_DIR):
        if theme is None or rec.get("theme") == theme:
            out.append((rel, rec))
    return out


def load_inheritance():
    return list(iter_records(INHERITANCE_DIR))


_NORMALIZED = {}


def normalized_document(doc):
    """Whole-file normalized text, memoized for the process.

    The status report scans every document once per registered theme.
    Normalizing 1.3 million words six times over is the difference between
    a 25-second run and a 5-second one, and the text does not change
    underneath a single run.
    """
    slug = doc["slug"]
    if slug not in _NORMALIZED:
        _NORMALIZED[slug] = normalize_quote(
            read_text(os.path.join(REPO_ROOT, doc["path"])))
    return _NORMALIZED[slug]


_TERM_RE = {}


def term_regex(terms):
    """One alternation for a term list, compiled once.

    A pass per term meant six themes x twelve terms x twenty-nine
    documents - two thousand scans of the corpus to build one status
    report. One alternation per theme is a single scan.
    """
    key = tuple(terms)
    if key not in _TERM_RE:
        alts = "|".join(re.escape(normalize_quote(t)) for t in terms)
        _TERM_RE[key] = re.compile(r"(?<!\w)(?:%s)" % alts)
    return _TERM_RE[key]


def count_terms(text, terms):
    """Word-boundary hit count over already-normalized text."""
    return len(term_regex(terms).findall(text))


# ----------------------------------------------------------------- schema

_TYPES = {
    "object": dict, "array": list, "string": str, "boolean": bool,
    "integer": int, "number": (int, float), "null": type(None),
}


def _resolve(ref, root):
    node = root
    for part in ref.lstrip("#/").split("/"):
        node = node[part]
    return node


def check_schema(instance, schema, root=None, path="$"):
    """A JSON Schema subset checker, in the standard library.

    Supports the keywords the synthesis schemas actually use: type,
    const, enum, pattern, minLength, maxLength, minItems, required,
    properties, additionalProperties, items, and local $ref into $defs.
    Anything else in a schema is ignored rather than guessed at.

    Vendoring this - rather than depending on `jsonschema` - keeps
    validation runnable with a bare `python3` on any machine, and keeps
    the schema files the single statement of the format instead of
    duplicating the rules in Python.
    """
    root = schema if root is None else root
    errors = []

    if "$ref" in schema:
        return check_schema(instance, _resolve(schema["$ref"], root), root, path)

    if "const" in schema and instance != schema["const"]:
        errors.append("%s: must be %r" % (path, schema["const"]))

    if "type" in schema:
        names = schema["type"]
        names = [names] if isinstance(names, str) else names
        allowed = tuple(_TYPES[n] for n in names)
        ok = isinstance(instance, allowed)
        # bool is an int in Python; JSON Schema does not agree.
        if isinstance(instance, bool) and "boolean" not in names:
            ok = False
        if not ok:
            errors.append("%s: expected %s, got %s"
                          % (path, "/".join(names), type(instance).__name__))
            return errors

    if "enum" in schema and instance not in schema["enum"]:
        errors.append("%s: %r not one of %s" % (path, instance, schema["enum"]))

    if isinstance(instance, str):
        if "pattern" in schema and not re.search(schema["pattern"], instance):
            errors.append("%s: %r does not match %s"
                          % (path, instance[:60], schema["pattern"]))
        if "minLength" in schema and len(instance) < schema["minLength"]:
            errors.append("%s: shorter than %d characters" % (path, schema["minLength"]))
        if "maxLength" in schema and len(instance) > schema["maxLength"]:
            errors.append("%s: longer than %d characters (%d)"
                          % (path, schema["maxLength"], len(instance)))

    if isinstance(instance, list):
        if "minItems" in schema and len(instance) < schema["minItems"]:
            errors.append("%s: needs at least %d items" % (path, schema["minItems"]))
        if "items" in schema:
            for i, item in enumerate(instance):
                errors += check_schema(item, schema["items"], root, "%s[%d]" % (path, i))

    if isinstance(instance, dict):
        for key in schema.get("required", []):
            if key not in instance:
                errors.append("%s: missing required property %r" % (path, key))
        props = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            for key in instance:
                if key not in props and not key.startswith("_"):
                    errors.append("%s: unexpected property %r" % (path, key))
        for key, sub in props.items():
            if key in instance:
                errors += check_schema(instance[key], sub, root, "%s.%s" % (path, key))

    return errors
