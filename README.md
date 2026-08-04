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
