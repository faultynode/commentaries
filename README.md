# Commentaria
AI generated commentaries on philosophical texts

https://faultynode.github.io/commentaries/

`synthesis/` holds the machinery for reading across the commentaries:
extraction records that pin every claim to a section of a commentary with
a verbatim quote, chronological ledgers built from them, and a synthesis
stage that may write only from the ledgers. Quotes are re-checked against
their sources in CI.

- [docs/synthesis-design.md](docs/synthesis-design.md) — architecture and the decisions behind it
- [docs/synthesis-operations.md](docs/synthesis-operations.md) — runbook, CI, troubleshooting
- [synthesis/CLAUDE.md](synthesis/CLAUDE.md) — conventions for working in
  `synthesis/`

## External services

- **GitHub Pages** — hosts the site straight from this repo via Jekyll
  (`_config.yml`), publishing to
  [faultynode.github.io/commentaries](https://faultynode.github.io/commentaries/)
  on every push to `main`.
- **WordPress.com** — `scripts/sync_wordpress.py`, run by
  [`.github/workflows/wordpress-sync.yml`](.github/workflows/wordpress-sync.yml)
  on every markdown push, mirrors commentaries to a WordPress.com blog via
  the legacy REST API v1.1 (works on every plan tier, unlike `wp/v2`).
  Needs `WP_URL` and `WP_ACCESS_TOKEN` (OAuth2) repository secrets.
- **GitHub Actions** — CI
  ([`.github/workflows/synthesis.yml`](.github/workflows/synthesis.yml))
  re-checks every synthesis quote against its source commentary and
  rebuilds the derived artifacts (index, ledgers, status) on push/PR.
