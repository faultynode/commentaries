#!/usr/bin/env python3
"""Regenerate synthesis/corpus.json from the commentary files.

The index is the pipeline's map of what exists and where: one entry per
commentary, with its heading tree, per-section line spans and word
counts, and a sha256 of the file. Extraction records address sections by
the ids minted here, and record the digest they were extracted against -
which is how staleness is detected later.

Run from anywhere; paths are resolved against the repo root.

    python3 scripts/synthesis_index.py [--check]

--check exits 1 if the committed index is out of date, without writing.
"""

import sys

import synthesislib as lib


def main(argv):
    check = "--check" in argv[1:]
    corpus = lib.build_corpus()

    if check:
        try:
            current = lib.load_json(lib.CORPUS_PATH)
        except (OSError, ValueError):
            current = None
        if current != corpus:
            print("corpus.json is stale - run python3 scripts/synthesis_index.py")
            return 1
        print("corpus.json is up to date")
        return 0

    lib.write_json(lib.CORPUS_PATH, corpus)
    docs = corpus["documents"]
    print("indexed %d commentaries, %d sections, %s words"
          % (len(docs),
             sum(len(d["sections"]) for d in docs),
             format(sum(d["words"] for d in docs), ",")))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
