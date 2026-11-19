# -*- coding: utf-8 -*-
"""Rewrite the English openings in (Hua/English) citations from the Hua page,
then assemble the study. Prints every citation whose English part changed."""
import io
import os
import re
import sys
import build_evidence as be

sys.stdout.reconfigure(encoding="utf-8")
D = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(D, "..", "..", "..", "articles", "constitution-husserl-ideas-ii-study.md")
emap = be.english_map()


def eng(lo, hi):
    a = be.english_for(emap, lo)[1].split(" ")[0]
    b = be.english_for(emap, hi)[1].split(" ")[0]
    if a == "—" or b == "—":
        return None
    nums = [int(x) for x in re.findall(r"\d+", a + "–" + b)]
    return "%d–%d" % (min(nums), max(nums)) if min(nums) != max(nums) else str(min(nums))


PAT = re.compile(r"(?<![\w/])(\d{1,3})(?:–(\d{1,3}))?( n\.)?/(\d{1,3}(?:–\d{1,3})?)(?=[\);,])")


def fix(m):
    lo = int(m.group(1))
    hi = lo
    if m.group(2):
        t = m.group(2)
        hi = int(str(lo)[:len(str(lo)) - len(t)] + t) if len(t) < len(str(lo)) else int(t)
    e = eng(lo, hi)
    if e is None:
        print("NO ENGLISH for", m.group(0))
        return m.group(0)
    new = "%s%s%s/%s" % (m.group(1), "–" + m.group(2) if m.group(2) else "",
                         m.group(3) or "", e)
    if new != m.group(0):
        print("%s -> %s" % (m.group(0), new))
    return new


parts = []
for n in range(0, 8):
    p = os.path.join(D, "part%d.md" % n)
    if not os.path.exists(p):
        continue
    s = io.open(p, encoding="utf-8").read()
    s2 = PAT.sub(fix, s)
    if s2 != s:
        io.open(p, "w", encoding="utf-8", newline="\n").write(s2)
    parts.append(s2.rstrip("\n") + "\n")
io.open(OUT, "w", encoding="utf-8", newline="\n").write("\n".join(parts))
print("assembled", len(parts), "parts")
