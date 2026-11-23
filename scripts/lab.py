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
import re
import shutil
import subprocess
import sys
from pathlib import Path

from terminal import GRAY, GREEN, YELLOW, Terminal

ROOT = Path(__file__).resolve().parent.parent
LAB_REPOSITORIES = ("mithridates/", "security-lab/")
WORKING_DIR = "com.docker.compose.project.working_dir"
PROJECT = "com.docker.compose.project"
RECLAIMED = re.compile(r"Total(?: reclaimed space)?:\s*(\S+)")


def docker(*args: str) -> list[dict]:
    """Runs a docker listing with `--format json` and returns one dict per line."""
    result = subprocess.run(["docker", *args, "--format", "json"], capture_output=True, text=True)
    if result.returncode != 0:
        if "daemon" in result.stderr or "connect" in result.stderr:
            sys.exit("Docker is not running: start Docker Desktop, or dockerd, and try again.")
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


def plural(count: int, word: str) -> str:
    """Returns `count` with `word`, in the plural unless the count is one."""
    return f"{count} {word}{'' if count == 1 else 's'}"


def section(ui: Terminal, title: str, rows: list[str]) -> None:
    """Prints a titled list, or `none` under the title when the list is empty."""
    ui.line(f"  {ui.paint(title, bold=True)}")
    for row in rows or [ui.paint("none", dim=True)]:
        ui.line(f"    {row}")
    ui.line()


def status(ui: Terminal) -> int:
    """Prints the lab's containers, images and model volumes."""
    projects, images, volumes = lab_projects(), lab_images(), model_volumes()
    ui.line(f"  {ui.paint('Lab status', bold=True)}  {ui.paint(str(ROOT), dim=True)}")
    ui.line()

    rows = []
    for project, containers in sorted(projects.items()):
        for container in containers:
            running = container["State"] == "running"
            mark = ui.paint(ui.glyph["on" if running else "off"], GREEN if running else GRAY)
            state = ui.paint(f"{container['State']:<9}", dim=not running)
            rows.append(f"{mark} {container['Names']:<34} {state} {ui.paint(project, dim=True)}")
    section(ui, "Containers", rows)

    rows = []
    for image in images:
        name = f"{image['Repository']}:{image['Tag']}"
        flag = ui.paint(f"  {ui.glyph['warn']} leftover", YELLOW) if image["leftover"] else ""
        rows.append(f"{name:<40} {image['Size']:>8}{flag}")
    section(ui, "Images", rows)

    section(ui, "Model volumes", [volume["Name"] for volume in volumes])

    leftovers = sum(image["leftover"] for image in images)
    if not projects and not leftovers:
        ui.line(f"  {ui.paint(ui.glyph['ok'], GREEN, bold=True)} Nothing left over.")
    else:
        work = [f"stops {plural(len(projects), 'project')}"] if projects else []
        work += [f"removes {plural(leftovers, 'leftover image')}"] if leftovers else []
        command = ui.paint("python scripts/lab.py clean", bold=True)
        ui.line(f"  {ui.paint(ui.glyph['arrow'], dim=True)} {command} {' and '.join(work)}.")
    ui.line()
    return 0


def clean(ui: Terminal, args: argparse.Namespace) -> int:
    """Stops the lab's projects and removes the images, volumes and cache asked for."""
    tasks: list[tuple[str, str, list[str], str]] = []
    for project in sorted(lab_projects()):
        down = ["docker", "compose", "-p", project, "down", "--remove-orphans"]
        tasks.append((f"Stopping {project}", f"Stopped {project}",
                      down + (["--volumes"] if args.models else []), ""))
    for image in (i for i in lab_images() if args.all or i["leftover"]):
        name = f"{image['Repository']}:{image['Tag']}"
        tasks.append((f"Removing {name}", f"Removed {name}", ["docker", "image", "rm", name],
                      image["Size"]))
    if args.models:
        for volume in model_volumes():
            tasks.append((f"Removing {volume['Name']}", f"Removed {volume['Name']}",
                          ["docker", "volume", "rm", volume["Name"]], ""))
    if args.build_cache:
        tasks.append(("Pruning the build cache", "Pruned the build cache",
                      ["docker", "builder", "prune", "--force"], ""))

    note = ui.paint("  dry run, nothing is changed", dim=True) if args.dry_run else ""
    ui.line(f"  {ui.paint('Cleaning up', bold=True)}{note}")
    ui.line()
    if not tasks:
        ui.line(f"  {ui.paint(ui.glyph['ok'], GREEN, bold=True)} Nothing to clean.")
        ui.line()
        return 0

    ui.width = max(len(finished) for _, finished, _, _ in tasks) + 3
    for running, finished, command, detail in tasks:
        if args.dry_run:
            ui.line(f"    {ui.paint('$', dim=True)} {' '.join(command)}")
            continue
        with ui.step(running, finished) as step:
            result = subprocess.run(command, capture_output=True, text=True)
            if result.returncode != 0:
                step.warn(result.stderr.strip())
            elif reclaimed := RECLAIMED.search(result.stdout):
                step.done(f"{reclaimed.group(1)} freed")
            else:
                step.done(detail)
    ui.line()
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
    ui = Terminal()
    ui.banner()
    return status(ui) if args.command == "status" else clean(ui, args)


if __name__ == "__main__":
    sys.exit(main())
