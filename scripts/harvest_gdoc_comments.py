#!/usr/bin/env python3
"""Turn a Google Docs comment export into a repo note.

Input: the JSON saved by the Drive connector's read_file_content call made with
includeComments=true (keys: title, viewUrl, fileContent, commentThreads).
fileContent carries <comment_start id=X> ... <comment_end id=X> tags around the
highlighted text; commentThreads carries the posts.

For each thread the script records:
  - the comment, its status and any replies,
  - the highlighted passage (verbatim from the Doc text),
  - where it sits in the source Markdown (file:line and nearest numbered heading).

Usage:
  harvest_gdoc_comments.py EXPORT.json SOURCE.md [--doc-url URL] \
      > research/doc-comments/<name>.md
"""
import argparse, json, re, datetime

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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("export"); ap.add_argument("source")
    ap.add_argument("--doc-url", default="")
    a = ap.parse_args()
    d = json.load(open(a.export, encoding="utf8"))
    lines = open(a.source, encoding="utf8").read().split("\n")
    anc = anchors(d["fileContent"])
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
            print("**Location**: not found in source.\n")
        else:
            print(f"**Location**: `{a.source}:{i+1}`, {heading_for(lines, i)}\n")


if __name__ == "__main__":
    main()
