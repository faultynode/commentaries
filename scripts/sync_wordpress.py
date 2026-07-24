#!/usr/bin/env python3
"""Sync this repo's markdown commentary files to WordPress.com posts.

Each file's front matter gains a `wordpress_id` field once it's first
published; subsequent runs update that same post instead of creating a
new one. Run with WP_URL and WP_ACCESS_TOKEN set in the environment.

WP_ACCESS_TOKEN is an OAuth2 token for the legacy WordPress.com REST
API v1.1, which (unlike the wp/v2 proxy) works on every plan tier.
"""

import glob
import os
import sys
from urllib.parse import urlparse

import frontmatter
import markdown
import requests
from bs4 import BeautifulSoup

EXCLUDED = {"README.md"}

MARKDOWN_EXTENSIONS = ["extra", "sane_lists", "fenced_code", "footnotes", "toc"]


def to_gutenberg_html(markdown_text):
    """Convert markdown to HTML wrapped in Gutenberg block comments.

    Block-based features (like WordPress's Table of Contents block)
    scan the post's parsed block structure for heading blocks - plain
    <h2> tags with no block markup are invisible to them. Headings get
    wrapped as real wp:heading blocks; everything else is wrapped as a
    generic wp:html block, which WordPress renders as-is.
    """
    raw_html = markdown.markdown(markdown_text, extensions=MARKDOWN_EXTENSIONS)
    soup = BeautifulSoup(raw_html, "html.parser")

    blocks = []
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

    for path in sorted(glob.glob("*.md")):
        if path in EXCLUDED:
            continue

        post = frontmatter.load(path)
        title = post.get("title", os.path.splitext(path)[0])
        html = to_gutenberg_html(post.content)

        payload = {"title": title, "content": html, "status": "publish"}
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
