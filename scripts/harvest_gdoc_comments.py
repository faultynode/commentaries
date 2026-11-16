#!/usr/bin/env python3
"""Turn a Google Docs comment export into a repo note.

Input: the JSON saved by the Drive connector's read_file_content call made with
includeComments=true (keys: title, viewUrl, fileContent, commentThreads).
fileContent carries <comment_start id=X> ... <comment_end id=X> tags around the
highlighted text; commentThreads carries the posts.

For each thread the script records:
  - the highlighted passage (verbatim from the Doc text),
  - where it sits in the source Markdown (file:line and nearest heading),
  - the page citations in that paragraph (or, when the paragraph has none, in
    the preceding paragraph, flagged as inherited),
  - the rows of the study's evidence.md that match those German pages
    (ID, source file:line, section), when --evidence is given.

Usage:
  harvest_gdoc_comments.py EXPORT.json SOURCE.md [--evidence evidence.md]
      [--doc-url URL] > research/doc-comments/<name>.md
"""
import argparse, json, re, sys, datetime

CITE = re.compile(r"\((?:(Hua [IVX]+(?:/\d+)?|GA \d+), ?)?(\d+(?:[–-]\d+)?)(?:/(\d+(?:[–-]\d+)?))?\)")
# work label -> prefix of the source file name in evidence.md; a bare (n/m) citation
# inherits the last labelled work seen, as in the articles' own convention
WORKS = {"Hua IV": "husserl-hua-4", "Hua III/1": "husserl-hua-3-1", "GA 20": "heidegger-ga-20"}
FN = re.compile(r"\[\^[^\]]+\]")


def norm(s):
    s = FN.sub("", s)
    s = re.sub(r"\[\d+\]", "", s)
    return re.sub(r"\s+", " ", s).strip()


def anchors(text):
    out = {}
    for m in re.finditer(r"<comment_start id=(\S+?)>(.*?)<comment_end id=\1>", text, re.S):
        out[m.group(1)] = m.group(2)
    return out


def locate(lines, passage):
    key = norm(passage)[:80]
    for i, ln in enumerate(lines):
        if key and key in norm(ln):
            return i
    return None


def heading_for(lines, i):
    for j in range(i, -1, -1):
        if re.match(r"#{2,4} \d", lines[j]):
            return lines[j].lstrip("#").strip()
    return "Introduction (before § 1)"


def cites(line):
    out, work = [], "Hua IV"
    for m in CITE.finditer(line):
        work = m.group(1) or work
        out.append((m.group(0), work, m.group(2), m.group(3)))
    return out


def prev_paragraph(lines, i):
    for j in range(i - 1, -1, -1):
        s = lines[j].strip()
        if s and not s.startswith(("#", "[^", "---", "layout:", "title:")):
            return j
    return None


def evidence_rows(path):
    rows = []
    for ln in open(path, encoding="utf8"):
        c = [x.strip() for x in ln.strip().strip("|").split("|")]
        if len(c) >= 5 and re.fullmatch(r"[A-Z]+\d+", c[0]):
            rows.append(dict(id=c[0], file=c[1].strip("`"), line=c[2], section=c[3], page=c[4]))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("export"); ap.add_argument("source")
    ap.add_argument("--evidence"); ap.add_argument("--doc-url", default="")
    a = ap.parse_args()
    d = json.load(open(a.export, encoding="utf8"))
    lines = open(a.source, encoding="utf8").read().split("\n")
    anc = anchors(d["fileContent"])
    ev = evidence_rows(a.evidence) if a.evidence else []
    print(f"# Doc comments: {d['title']}\n")
    print(f"Source: `{a.source}`  \nDoc: {a.doc_url or d.get('viewUrl','')}  \n"
          f"Harvested: {datetime.date.today()}  \n"
          "Line numbers are those of the source file at harvest time and drift on any edit; "
          "the anchored passage is quoted so the comment can be re-found.\n")
    for t in d["commentThreads"]:
        cid = t["commentId"]; hp = t["headPost"]
        passage = anc.get(cid, "").strip()
        i = locate(lines, passage) if passage else None
        print(f"## {cid} ({t.get('status','?')})\n")
        print(f"**{hp['authorName']}**, {hp['modifiedTime']}: {hp['content']}\n")
        for r in t.get("replies", []) or []:
            print(f"- reply, **{r.get('authorName','?')}**, {r.get('modifiedTime','')}: {r.get('content','')}")
        print(f"\n**Highlighted passage**\n\n> {passage or '(anchor not found: comment is on the whole document or its text was deleted)'}\n")
        if i is None:
            print("**Location**: not found in source.\n"); continue
        print(f"**Location**: `{a.source}:{i+1}`, {heading_for(lines, i)}\n")
        cs, inherited = cites(lines[i]), False
        if not cs:
            j = prev_paragraph(lines, i)
            if j is not None:
                cs, inherited = cites(lines[j]), True
                src_line = j + 1
        if cs:
            tag = f"inherited from the preceding paragraph at `:{src_line}`; the highlighted paragraph cites none" if inherited else "in the highlighted paragraph"
            print(f"**Citations** ({tag})\n")
            for raw, work, de, en in cs:
                pg = re.split(r"[–-]", de)[0]
                pre = WORKS.get(work, "")
                hits = [r for r in ev if r["page"].split()[0] == pg and pre and r["file"].startswith(pre)]
                where = "; ".join(f"{h['id']} `{h['file'][:48]}…:{h['line']}` ({h['section']})" for h in hits) or "no evidence row"
                print(f"- {work} p. {de}" + (f" / English {en}" if en else "") + f": {where}")
            print()
        else:
            print("**Citations**: none found.\n")


if __name__ == "__main__":
    main()
