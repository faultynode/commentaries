#!/usr/bin/env python3
"""Block personal-info and secret leaks in outgoing commits.

Scans a range of commits (as passed to `git rev-list`) for:
  - author/committer name or email matching a real-identity denylist
  - commit messages mentioning the real identity
  - added diff lines matching personal machine paths or secret-shaped strings

Used by .githooks/pre-push (blocks locally, before a push leaves the
machine) and .github/workflows/pii-check.yml (server-side backstop).

Usage: check_pii.py <git-rev-list-args...>
Exit 0 if clean, 1 if violations were found, 2 on usage error.
"""
import re
import subprocess
import sys

# This file's own diff is excluded from content scanning (see EXCLUDE_PATHSPEC
# below) specifically so these patterns can be spelled out here without
# tripping the check on themselves.
REAL_NAME_PATTERNS = [r"Michael\s+Brockman", r"\bBrockman\b"]
REAL_EMAIL_PATTERNS = [r"mbrockman@live\.com"]

PATH_PATTERNS = [
    r"[A-Za-z]:\\{1,2}Users\\{1,2}[A-Za-z0-9_.\-]+",  # C:\Users\<name>
    r"/(?:home|Users)/[A-Za-z0-9_.\-]+",  # /home/<name> or macOS /Users/<name>
    r"\bmbroc\b",
]
SECRET_PATTERNS = [
    r"-----BEGIN (RSA|OPENSSH|PGP|EC|DSA) PRIVATE KEY-----",
    r"\bAKIA[0-9A-Z]{16}\b",  # AWS access key id
    r"\bgh[pousr]_[A-Za-z0-9]{20,}\b",  # GitHub tokens
    r"\bsk-[A-Za-z0-9]{20,}\b",  # OpenAI/Anthropic-style API keys
    r"(?i)\b(api[_-]?key|secret|password|access[_-]?token)\b\s*[:=]\s*['\"][^'\"\s]{8,}['\"]",
]

CONTENT_PATTERNS = (
    [(p, "personal path") for p in PATH_PATTERNS]
    + [(p, "possible secret") for p in SECRET_PATTERNS]
    + [(p, "real name") for p in REAL_NAME_PATTERNS]
    + [(p, "real email") for p in REAL_EMAIL_PATTERNS]
)

EXCLUDE_PATHSPEC = ":(exclude)scripts/check_pii.py"


def run(cmd):
    return subprocess.run(
        cmd, capture_output=True, text=True, encoding="utf-8", errors="replace"
    )


def get_commits(rev_list_args):
    r = run(["git", "rev-list"] + rev_list_args)
    if r.returncode != 0:
        print(r.stderr, file=sys.stderr)
        sys.exit(2)
    return [c for c in r.stdout.splitlines() if c]


def check_commit(sha):
    violations = []

    fmt = run(["git", "show", "-s", "--format=%an%x00%ae%x00%cn%x00%ce%x00%B", sha])
    an, ae, cn, ce, body = fmt.stdout.split("\x00", 4)
    for label, name, email in (("author", an, ae), ("committer", cn, ce)):
        for pat in REAL_NAME_PATTERNS:
            if re.search(pat, name, re.I):
                violations.append(f"{sha[:10]}: {label} name matches denylist ({name!r})")
        for pat in REAL_EMAIL_PATTERNS:
            if re.search(pat, email, re.I):
                violations.append(f"{sha[:10]}: {label} email matches denylist ({email!r})")
    for pat in REAL_NAME_PATTERNS + REAL_EMAIL_PATTERNS:
        if re.search(pat, body, re.I):
            violations.append(f"{sha[:10]}: commit message mentions denylisted identity")
            break

    diff = run(["git", "show", "--format=", "-U0", sha, "--", ".", EXCLUDE_PATHSPEC])
    for line in diff.stdout.splitlines():
        if not line.startswith("+") or line.startswith("+++"):
            continue
        content = line[1:]
        for pat, kind in CONTENT_PATTERNS:
            if re.search(pat, content):
                snippet = content.strip()[:120]
                violations.append(f"{sha[:10]}: {kind} in added line: {snippet}")
                break  # one hit per line is enough

    return violations


def main():
    rev_list_args = sys.argv[1:]
    if not rev_list_args:
        print("usage: check_pii.py <git-rev-list-args...>", file=sys.stderr)
        sys.exit(2)

    commits = get_commits(rev_list_args)
    violations = []
    for sha in commits:
        violations.extend(check_commit(sha))

    if violations:
        print("PII/secret check FAILED:\n")
        for v in violations:
            print(" -", v)
        print(f"\n{len(violations)} issue(s) across {len(commits)} commit(s) scanned.")
        print("False positive? Adjust the patterns in scripts/check_pii.py.")
        sys.exit(1)

    print(f"PII/secret check passed ({len(commits)} commit(s) scanned).")


if __name__ == "__main__":
    main()
