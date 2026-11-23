"""Which demos CI runs the Bruno collection of, as a JSON list for a job matrix.

    python scripts/bruno_plan.py --changed-since <git ref>
    python scripts/bruno_plan.py --all

A demo's collection runs on every pull request, unless its compose.yaml says otherwise:

    x-mithridates:
      bruno-in-ci: on-change
      reason: every run downloads about 2 GB of models and answers on CPU

`on-change` runs it only when the change touches the demo, or how the collections run
(.github/workflows/bruno.yml and this file). `--all`, the weekly and the manual run,
runs every demo. check_repo.py checks the field; .github/workflows/bruno.yml reads the
plan. A demo without a `bruno/` folder is left out; check_repo.py fails it anyway.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
EVERY_PR, ON_CHANGE = "every-pr", "on-change"
BRUNO_IN_CI = (EVERY_PR, ON_CHANGE)
# A change to how the collections run is tried on every demo.
SHARED = (".github/workflows/bruno.yml", "scripts/bruno_plan.py")


def bruno_in_ci(compose: Path) -> str:
    """The demo's `x-mithridates.bruno-in-ci`, or `every-pr` when it sets none."""
    config = yaml.safe_load(compose.read_text(encoding="utf-8")) or {}
    meta = config.get("x-mithridates") or {}
    return meta.get("bruno-in-ci", EVERY_PR) if isinstance(meta, dict) else EVERY_PR


def changed_files(since: str) -> list[str]:
    """The paths the commits after `since` change."""
    result = subprocess.run(["git", "diff", "--name-only", f"{since}...HEAD"], cwd=ROOT,
                            capture_output=True, text=True, check=True)
    return result.stdout.splitlines()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    which = parser.add_mutually_exclusive_group(required=True)
    which.add_argument("--all", action="store_true", help="every demo, whatever its compose.yaml says")
    which.add_argument("--changed-since", metavar="REF", help="the commit the change starts from")
    args = parser.parse_args()

    files = [] if args.all else changed_files(args.changed_since)
    everything = args.all or any(path in SHARED for path in files)
    plan = []
    for demo in sorted(p for p in (ROOT / "demos").glob("*-demo") if (p / "bruno").is_dir()):
        when = bruno_in_ci(demo / "compose.yaml")
        if when not in BRUNO_IN_CI:
            sys.exit(f"demos/{demo.name}/compose.yaml: x-mithridates.bruno-in-ci is {when!r}, "
                     f"not one of {', '.join(BRUNO_IN_CI)}")
        touched = any(path.startswith(f"demos/{demo.name}/") for path in files)
        runs = everything or when == EVERY_PR or touched
        print(f"{demo.name}: {when}, {'runs' if runs else 'not touched, skipped'}", file=sys.stderr)
        if runs:
            plan.append(demo.name)
    print(json.dumps(plan))
    return 0


if __name__ == "__main__":
    sys.exit(main())
