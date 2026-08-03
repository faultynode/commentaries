#!/usr/bin/env python3
"""Sync this repo's markdown commentary files to WordPress.com posts.

Each file's front matter gains a `wordpress_id` field once it's first
published; subsequent runs update that same post instead of creating a
new one. Run with WP_URL and WP_ACCESS_TOKEN set in the environment.

WP_ACCESS_TOKEN is an OAuth2 token for the legacy WordPress.com REST
API v1.1, which (unlike the wp/v2 proxy) works on every plan tier.
"""

import glob
import html as html_module
import os
import sys
from urllib.parse import urlparse

import frontmatter
import markdown
import requests
from bs4 import BeautifulSoup

COMMENTARIES_DIR = "commentaries"

MARKDOWN_EXTENSIONS = ["extra", "sane_lists", "fenced_code", "footnotes", "toc"]


def build_toc_tree(headings):
    """Nest a flat (tag_name, id, text) heading list by heading level."""
    root = []
    stack = [{"level": 0, "items": root}]
    for name, hid, text in headings:
        level = int(name[1])
        while len(stack) > 1 and level < stack[-1]["level"]:
            stack.pop()
        top = stack[-1]
        item = {"id": hid, "text": text, "children": []}

        if level == top["level"]:
            top["items"].append(item)
        else:
            target = top["items"][-1]["children"] if top["items"] else top["items"]
            target.append(item)
            stack.append({"level": level, "items": target})
    return root


def render_toc_tree(items):
    if not items:
        return ""
    lis = "".join(
        f'<li><a href="#{html_module.escape(it["id"])}">{html_module.escape(it["text"])}</a>'
        f'{render_toc_tree(it["children"])}</li>'
        for it in items
    )
    return f"<ul>{lis}</ul>"


def to_gutenberg_html(markdown_text):
    """Convert markdown to HTML wrapped in Gutenberg block comments.

    Block-based features (like WordPress's Table of Contents block)
    scan the post's parsed block structure for heading blocks - plain
    <h2> tags with no block markup are invisible to them. Headings get
    wrapped as real wp:heading blocks; everything else is wrapped as a
    generic wp:html block, which WordPress renders as-is.

    A collapsible <details>/<summary> table of contents (native HTML,
    no CSS or JS required) is prepended when there's more than one
    heading, since WordPress.com's own Table of Contents block only
    works when manually added inside a post's content, not when
    synced programmatically or placed in a shared template.
    """
    raw_html = markdown.markdown(markdown_text, extensions=MARKDOWN_EXTENSIONS)
    soup = BeautifulSoup(raw_html, "html.parser")

    headings = [
        (el.name, el["id"], el.get_text())
        for el in soup.contents
        if getattr(el, "name", None) in ("h1", "h2", "h3", "h4", "h5", "h6") and el.get("id")
    ]

    blocks = []

    if len(headings) > 1:
        toc_list = render_toc_tree(build_toc_tree(headings))
        toc_html = f"<details><summary>Table of Contents</summary>{toc_list}</details>"
        blocks.append(f"<!-- wp:html -->\n{toc_html}\n<!-- /wp:html -->")

    for el in soup.contents:
        name = getattr(el, "name", None)
        if name is None:
            continue  # stray whitespace between top-level elements

        if name in ("h1", "h2", "h3", "h4", "h5", "h6"):
            level = int(name[1])
            classes = el.get("class", [])
            if "wp-block-heading" not in classes:
                el["class"] = classes + ["wp-block-heading"]
            blocks.append(f'<!-- wp:heading {{"level":{level}}} -->\n{el}\n<!-- /wp:heading -->')
        else:
            blocks.append(f"<!-- wp:html -->\n{el}\n<!-- /wp:html -->")

    return "\n\n".join(blocks)


def author_tag(path):
    """Derive the post's author tag from its parent folder name.

    `commentaries/<author>/<file>.md` folders are named as the author's
    lowercase last name (see commentaries/CLAUDE.md), so the folder is
    the tag. Title-cased for display, since WordPress shows tag names
    verbatim; the slug WordPress derives from it stays lowercase.
    """
    folder = os.path.basename(os.path.dirname(path))
    return "-".join(part.capitalize() for part in folder.split("-"))


def wp_request(url, token, **kwargs):
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.post(url, headers=headers, timeout=30, **kwargs)
    if not resp.ok:
        print(f"WordPress API error {resp.status_code} for POST {url}: {resp.text}", file=sys.stderr)
        resp.raise_for_status()
    return resp.json()


def main():
    wp_url = os.environ["WP_URL"].rstrip("/")
    token = os.environ["WP_ACCESS_TOKEN"]
    site = urlparse(wp_url).netloc or wp_url
    base = f"https://public-api.wordpress.com/rest/v1.1/sites/{site}/posts"

    for path in sorted(glob.glob(os.path.join(COMMENTARIES_DIR, "*", "*.md"))):
        post = frontmatter.load(path)
        title = post.get("title", os.path.splitext(os.path.basename(path))[0])
        html = to_gutenberg_html(post.content)

        payload = {
            "title": title,
            "content": html,
            "status": "publish",
            "tags": author_tag(path),
        }
        wp_id = post.get("wordpress_id")

        if wp_id:
            wp_request(f"{base}/{wp_id}", token, data=payload)
            print(f"Updated post {wp_id} from {path}")
        else:
            result = wp_request(f"{base}/new", token, data=payload)
            post["wordpress_id"] = result["ID"]
            frontmatter.dump(post, path)
            print(f"Created post {result['ID']} from {path}")


if __name__ == "__main__":
    main()
