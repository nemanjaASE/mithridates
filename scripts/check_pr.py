"""Check a pull request's title and description.

    python scripts/check_pr.py "feat(sqli-demo): a second-order injection on the profile page"
    python scripts/check_pr.py "fix(sqli-demo): ..." --body description.md

CI runs it on every pull request with the title, description and author in the
environment (`TITLE`, `BODY`, `AUTHOR`). Run locally, it checks the title it is given and
the description only when `--body` names a file.

The title follows Conventional Commits (https://www.conventionalcommits.org): a pull
request is squash-merged, so its title becomes the commit message on `main`.

Exit status is 0 when everything passes, 1 otherwise.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# The commit types, as CONTRIBUTING.md explains them.
TYPES = ("feat", "fix", "docs", "test", "refactor", "style", "perf",
         "build", "ci", "chore", "revert")

# A scope names what the change is about: a demo by its folder name, or one of these.
OTHER_SCOPES = ("deps", "scripts", "house-style")

MAX_TITLE = 72          # GitHub appends " (#123)" on merge; this keeps `git log` on one line

TITLE = re.compile(r"^(?P<type>[^(!:\s]+)(?:\((?P<scope>[^)]*)\))?(?P<breaking>!)?: (?P<subject>.*)$")
# The title GitHub's own "Revert" button writes; it is accepted as it is.
GITHUB_REVERT = re.compile(r'^Revert ".+"$')

COMMENT = re.compile(r"<!--.*?-->", re.S)
SECTION = "## What this changes"
UNTICKED = re.compile(r"^\s*[-*] \[ \]\s*(.*(?:\n[ \t]+\S.*)*)", re.M)  # with wrapped lines
MIN_DESCRIPTION = 20    # characters of your own under "What this changes"

# Automated pull requests have a fixed description of their own; only the title is theirs.
BOTS = ("dependabot[bot]",)

EXAMPLE = "feat(xss-demo): reflected XSS on the search page"


def demos() -> list[str]:
    return sorted(p.name for p in (ROOT / "demos").iterdir()
                  if p.is_dir() and p.name.endswith("-demo"))


def check_title(title: str) -> list[str]:
    if GITHUB_REVERT.match(title):
        return []
    m = TITLE.match(title)
    if not m:
        if re.match(r"^[a-z]+(\([^)]*\))?!?:\S", title):
            return ["Put one space after the colon."]
        return [f"The title is not `type(scope): description`. For example: {EXAMPLE}"]

    errors = []
    kind, scope, subject = m["type"], m["scope"], m["subject"]
    if kind not in TYPES:
        errors.append(f"`{kind}` is not a type. Use one of: {', '.join(TYPES)}.")
    if scope is not None:
        scopes = (*demos(), *OTHER_SCOPES)
        if scope not in scopes:
            errors.append(f"`({scope})` is not a scope. Use one of: {', '.join(scopes)} "
                          "or leave the scope out.")
    if not subject.strip():
        errors.append("The description after the colon is empty.")
    elif subject != subject.strip() or "  " in subject:
        errors.append("The description has extra spaces.")
    elif re.match(r"[A-Z][a-z]", subject):
        errors.append("Start the description in lowercase: "
                      f"`{subject[0].lower()}{subject[1:].rstrip('.')}`")
    if subject.endswith("."):
        errors.append("Drop the full stop at the end of the description.")
    if len(title) > MAX_TITLE:
        errors.append(f"The title is {len(title)} characters; keep it to {MAX_TITLE}.")
    return errors


def check_body(body: str) -> list[str]:
    text = COMMENT.sub("", body.replace("\r\n", "\n"))
    errors = []

    if SECTION not in text:
        errors.append(f"The description has no `{SECTION}` section. Keep the one the "
                      "template starts with.")
    else:
        own = text.split(SECTION, 1)[1].split("\n## ", 1)[0]
        if len("".join(own.split())) < MIN_DESCRIPTION:
            errors.append(f"`{SECTION}` is empty or too short. Say in a few sentences what "
                          "this changes and why.")

    for item in UNTICKED.findall(text):
        errors.append(f"Unticked: \"{' '.join(item.split())}\". Tick it, or delete it if it does not "
                      "apply to this change.")
    return errors


def report(errors: list[str]) -> None:
    in_ci = os.environ.get("GITHUB_ACTIONS") == "true"
    for error in errors:
        if in_ci:
            # A workflow command ends at a newline; escape what would end it early.
            error = error.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
            print(f"::error::{error}")
        else:
            print(f"  FAIL  {error}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("title", nargs="?", default=os.environ.get("TITLE"))
    parser.add_argument("--body", type=Path, help="a file with the description")
    args = parser.parse_args()
    if args.title is None:
        parser.error("give a title, or set TITLE")

    errors = check_title(args.title)

    author = os.environ.get("AUTHOR", "")
    if args.body is not None:
        errors += check_body(args.body.read_text(encoding="utf-8"))
    elif "BODY" in os.environ and author not in BOTS:
        errors += check_body(os.environ["BODY"])

    report(errors)
    if errors:
        return 1
    print(f"ok: {args.title}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
