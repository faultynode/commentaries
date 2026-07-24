#!/usr/bin/env python3
"""One-off diagnostic: check whether this WordPress.com account can read
and write the site's Additional CSS (the `custom_css` post type) via the
legacy REST API v1.1. Run with WP_URL and WP_ACCESS_TOKEN set."""

import json
import os
import sys
from urllib.parse import urlparse

import requests

wp_url = os.environ["WP_URL"].rstrip("/")
token = os.environ["WP_ACCESS_TOKEN"]
site = urlparse(wp_url).netloc or wp_url
headers = {"Authorization": f"Bearer {token}"}
base = f"https://public-api.wordpress.com/rest/v1.1/sites/{site}/posts"

print("--- GET existing custom_css posts ---")
resp = requests.get(f"{base}/", headers=headers, params={"type": "custom_css", "number": 5}, timeout=30)
print(resp.status_code)
print(json.dumps(resp.json(), indent=2)[:2000])

print("\n--- Attempt to create a harmless test custom_css post ---")
resp = requests.post(
    f"{base}/new",
    headers=headers,
    data={"type": "custom_css", "title": "diagnostic-check", "content": "/* diagnostic check, safe to ignore/delete */", "status": "draft"},
    timeout=30,
)
print(resp.status_code)
print(json.dumps(resp.json(), indent=2)[:2000])

if resp.status_code >= 400:
    sys.exit(1)
