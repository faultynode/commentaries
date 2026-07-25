#!/usr/bin/env python3
"""Regenerate the commentary list in index.html from each markdown
file's front-matter title. Run from the repo root."""

import glob
import html
import os
import re

import frontmatter

COMMENTARIES_DIR = "commentaries"
INDEX_PATH = "index.html"


def build_list():
    items = []
    for path in sorted(glob.glob(os.path.join(COMMENTARIES_DIR, "*.md"))):
        post = frontmatter.load(path)
        title = post.get("title", os.path.splitext(os.path.basename(path))[0])
        href = os.path.splitext(path)[0].replace(" ", "%20") + ".html"
        items.append(f'  <li><a href="{html.escape(href)}">{html.escape(title)}</a></li>')
    return "<ul>\n" + "\n".join(items) + "\n</ul>"


def main():
    with open(INDEX_PATH, encoding="utf-8") as f:
        text = f.read()

    updated = re.sub(r"<ul>.*?</ul>", build_list(), text, count=1, flags=re.DOTALL)

    if updated != text:
        with open(INDEX_PATH, "w", encoding="utf-8", newline="\n") as f:
            f.write(updated)
        print("index.html updated")
    else:
        print("index.html already up to date")


if __name__ == "__main__":
    main()
