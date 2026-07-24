#!/usr/bin/env python3
"""Sync this repo's markdown commentary files to WordPress.com posts.

Each file's front matter gains a `wordpress_id` field once it's first
published; subsequent runs update that same post instead of creating a
new one. Run with WP_URL, WP_USERNAME, and WP_APP_PASSWORD set in the
environment.
"""

import glob
import os
import sys

import frontmatter
import markdown
import requests

EXCLUDED = {"README.md"}


def wp_request(method, url, auth, **kwargs):
    resp = requests.request(method, url, auth=auth, timeout=30, **kwargs)
    if not resp.ok:
        print(f"WordPress API error {resp.status_code} for {method} {url}: {resp.text}", file=sys.stderr)
        resp.raise_for_status()
    return resp.json()


def main():
    wp_url = os.environ["WP_URL"].rstrip("/")
    username = os.environ["WP_USERNAME"]
    app_password = os.environ["WP_APP_PASSWORD"]
    auth = (username, app_password)
    posts_endpoint = f"{wp_url}/wp-json/wp/v2/posts"

    for path in sorted(glob.glob("*.md")):
        if path in EXCLUDED:
            continue

        post = frontmatter.load(path)
        title = post.get("title", os.path.splitext(path)[0])
        html = markdown.markdown(
            post.content,
            extensions=["extra", "sane_lists", "fenced_code", "footnotes", "toc"],
        )

        payload = {"title": title, "content": html, "status": "publish"}
        wp_id = post.get("wordpress_id")

        if wp_id:
            wp_request("POST", f"{posts_endpoint}/{wp_id}", auth, json=payload)
            print(f"Updated post {wp_id} from {path}")
        else:
            result = wp_request("POST", posts_endpoint, auth, json=payload)
            post["wordpress_id"] = result["id"]
            frontmatter.dump(post, path)
            print(f"Created post {result['id']} from {path}")


if __name__ == "__main__":
    main()
