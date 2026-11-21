"""See and clean up what the lab leaves in Docker.

    python scripts/lab.py status
    python scripts/lab.py clean [--all] [--models] [--build-cache] [--dry-run]

`status` lists the lab's containers, images and model volumes, and marks what is left over.

`clean` stops every demo started from this repository, from its own folder or from the
root, and removes leftover images:

- images of demos whose folder no longer exists, such as a demo tried with the generator;
- images under the old `security-lab/` name;
- images tagged by CI (`:ci`).

`--all` also removes the images of the existing demos (the next `up` rebuilds them),
`--models` the downloaded model volumes (gigabytes, downloaded again on the next start),
and `--build-cache` Docker's build cache, which is shared with every other project on the
machine. `--dry-run` prints the commands without running them.

Only resources started from this repository are touched: containers are matched by the
folder Compose records on them, images by the `mithridates/` and `security-lab/` names.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LAB_REPOSITORIES = ("mithridates/", "security-lab/")
WORKING_DIR = "com.docker.compose.project.working_dir"
PROJECT = "com.docker.compose.project"


def docker(*args: str) -> list[dict]:
    """Runs a docker listing with `--format json` and returns one dict per line."""
    result = subprocess.run(["docker", *args, "--format", "json"], capture_output=True, text=True)
    if result.returncode != 0:
        sys.exit(f"docker {' '.join(args)} failed: {result.stderr.strip()}")
    return [json.loads(line) for line in result.stdout.splitlines() if line.strip()]


def labels(item: dict) -> dict[str, str]:
    """Parses the comma-separated `Labels` field of a docker listing."""
    pairs = (part.split("=", 1) for part in item.get("Labels", "").split(",") if "=" in part)
    return dict(pairs)


def inside_repository(path: str) -> bool:
    """Whether a folder recorded by Compose is this repository or a folder inside it."""
    folder = os.path.normcase(os.path.abspath(path))
    root = os.path.normcase(str(ROOT))
    return folder == root or folder.startswith(root + os.sep)


def lab_projects() -> dict[str, list[dict]]:
    """Returns the lab's Compose projects and their containers, by project name."""
    projects: dict[str, list[dict]] = {}
    for container in docker("ps", "--all"):
        tags = labels(container)
        if tags.get(PROJECT) and inside_repository(tags.get(WORKING_DIR, "")):
            projects.setdefault(tags[PROJECT], []).append(container)
    return projects


def lab_images() -> list[dict]:
    """Returns the images built by the lab, each with `leftover` set when it can go."""
    demos = {p.name for p in (ROOT / "demos").glob("*-demo") if p.is_dir()}
    images = []
    for image in docker("image", "ls"):
        repository = image["Repository"]
        if not repository.startswith(LAB_REPOSITORIES):
            continue
        demo = repository.split("/", 1)[1]
        image["leftover"] = (repository.startswith("security-lab/") or image["Tag"] != "local"
                             or demo not in demos)
        images.append(image)
    return images


def model_volumes() -> list[dict]:
    """Returns the volumes that hold downloaded models."""
    return [v for v in docker("volume", "ls") if "ollama" in v["Name"]]


def status() -> int:
    """Prints the lab's containers, images and model volumes."""
    projects = lab_projects()
    print("Containers")
    for project, containers in sorted(projects.items()) or [("", [])]:
        for c in containers:
            print(f"  {c['Names']:<34} {c['State']:<9} {project}")
    if not projects:
        print("  none")

    print("\nImages")
    images = lab_images()
    for image in images:
        mark = "  leftover" if image["leftover"] else ""
        print(f"  {image['Repository'] + ':' + image['Tag']:<40} {image['Size']:>8}{mark}")
    if not images:
        print("  none")

    print("\nModel volumes")
    for volume in model_volumes():
        print(f"  {volume['Name']}")
    if not model_volumes():
        print("  none")

    leftovers = sum(i["leftover"] for i in images)
    if projects or leftovers:
        print(f"\n`python scripts/lab.py clean` stops {len(projects)} project(s) "
              f"and removes {leftovers} leftover image(s).")
    return 0


def run(command: list[str], dry_run: bool) -> None:
    """Prints a command, and runs it unless this is a dry run."""
    print("  $ " + " ".join(command))
    if not dry_run:
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"    failed: {result.stderr.strip()}")


def clean(args: argparse.Namespace) -> int:
    """Stops the lab's projects and removes the images, volumes and cache asked for."""
    commands: list[list[str]] = []
    for project in sorted(lab_projects()):
        down = ["docker", "compose", "-p", project, "down", "--remove-orphans"]
        commands.append(down + (["--volumes"] if args.models else []))

    images = [i for i in lab_images() if args.all or i["leftover"]]
    if images:
        commands.append(["docker", "image", "rm", *(f"{i['Repository']}:{i['Tag']}" for i in images)])

    if args.models:
        volumes = [v["Name"] for v in model_volumes()]
        if volumes:
            commands.append(["docker", "volume", "rm", *volumes])

    if args.build_cache:
        commands.append(["docker", "builder", "prune", "--force"])

    if not commands:
        print("Nothing to clean.")
        return 0
    print("Dry run, nothing is changed:" if args.dry_run else "Cleaning:")
    for command in commands:
        run(command, args.dry_run)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status", help="list the lab's containers, images and model volumes")
    cleaner = sub.add_parser("clean", help="stop the demos and remove leftover images")
    cleaner.add_argument("--all", action="store_true", help="also remove the images of the existing demos")
    cleaner.add_argument("--models", action="store_true", help="also remove the downloaded model volumes")
    cleaner.add_argument("--build-cache", action="store_true", help="also prune Docker's build cache (shared)")
    cleaner.add_argument("--dry-run", action="store_true", help="print the commands without running them")
    args = parser.parse_args()

    if not shutil.which("docker"):
        sys.exit("docker is not on the PATH.")
    return status() if args.command == "status" else clean(args)


if __name__ == "__main__":
    sys.exit(main())
