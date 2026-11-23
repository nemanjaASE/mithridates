"""See and clean up what the lab leaves in Docker.

    python scripts/lab.py status
    python scripts/lab.py clean [--all] [--models] [--build-cache] [--dry-run]
    python scripts/lab.py check [--title "<pull request title>"] [--all]

`check` runs what CI checks before a pull request can be merged, except building the
images: the repository conventions, ruff in `scripts/` and `docs/` and in every demo the
branch changes (`--all`: every demo), and, with `--title`, the pull request title. It
needs uv, not Docker.

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

`status` and `clean` touch only resources started from this repository: containers are matched by the
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

from terminal import GRAY, GREEN, RED, YELLOW, Terminal

ROOT = Path(__file__).resolve().parent.parent
LAB_REPOSITORIES = ("mithridates/", "security-lab/")
WORKING_DIR = "com.docker.compose.project.working_dir"
PROJECT = "com.docker.compose.project"
RECLAIMED = re.compile(r"Total(?: reclaimed space)?:\s*(\S+)")
CONVENTIONS = ["uv", "run", "--no-project", "--with", "pyyaml", "python", "scripts/check_repo.py"]
RUFF = ["uvx", "--from", "ruff>=0.14,<0.15", "ruff", "check", "scripts", "docs"]
# Only the dev group: ruff needs none of the demo's own dependencies.
DEMO_RUFF = ["uv", "run", "--frozen", "--only-group", "dev", "ruff", "check", "."]
SHOWN = 25  # the lines of a failed check printed under it


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


def git(*args: str) -> str | None:
    """Runs git in the repository and returns its output, or None when git cannot answer."""
    if not shutil.which("git"):
        return None
    result = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)
    return result.stdout if result.returncode == 0 else None


def changed_demos() -> list[str] | None:
    """The demos this branch adds or changes, compared with `main`; None when git cannot tell."""
    status = git("status", "--porcelain")
    if status is None:
        return None
    paths = [line[3:].split(" -> ")[-1] for line in status.splitlines()]
    base = next((ref for ref in ("upstream/main", "origin/main", "main")
                 if git("rev-parse", "--verify", "--quiet", ref) is not None), None)
    fork_point = git("merge-base", base, "HEAD") if base else None
    if fork_point:
        paths += (git("diff", "--name-only", fork_point.strip()) or "").splitlines()
    names = {Path(p).parts[1] for p in paths if p.startswith("demos/") and len(Path(p).parts) > 1}
    return sorted(name for name in names if (ROOT / "demos" / name).is_dir())


def outcome(command: list[str], cwd: Path = ROOT) -> tuple[bool, str]:
    """Runs one check with colors off, and returns whether it passed and what it printed."""
    env = {k: v for k, v in os.environ.items() if k != "FORCE_COLOR"}
    env |= {"NO_COLOR": "1", "PYTHONIOENCODING": "utf-8"}
    result = subprocess.run(command, cwd=cwd, env=env, capture_output=True)
    return result.returncode == 0, (result.stdout + result.stderr).decode("utf-8", "replace")


def shorten(text: str) -> str:
    """The first lines of `text`, and how many more there are."""
    lines = [line.rstrip() for line in text.strip().splitlines() if line.strip()]
    if len(lines) > SHOWN:
        lines = [*lines[:SHOWN], f"... and {len(lines) - SHOWN} more lines"]
    return chr(10).join(lines)


def check(ui: Terminal, args: argparse.Namespace) -> int:
    """Runs the checks CI runs, except the image builds, and says whether the branch is ready."""
    ui.line(f"  {ui.paint('Checks', bold=True)}  "
            f"{ui.paint('what CI checks, except building the images', dim=True)}")
    ui.line()
    if not shutil.which("uv"):
        ui.line(f"  {ui.paint(ui.glyph['fail'], RED, bold=True)} uv is not installed: "
                "https://docs.astral.sh/uv/getting-started/installation/")
        ui.line()
        return 1
    demos = None if args.all else changed_demos()
    if demos is None:
        demos = sorted(p.name for p in (ROOT / "demos").glob("*-demo") if p.is_dir())
    linted = [d for d in demos if (ROOT / "demos" / d / "pyproject.toml").exists()]

    checks: list[tuple[str, str, list[str], Path]] = [
        ("Checking the conventions", "Repository conventions", CONVENTIONS, ROOT),
        ("Linting scripts/ and docs/", "Ruff in scripts/ and docs/", RUFF, ROOT),
        *((f"Linting demos/{d}", f"Ruff in demos/{d}", DEMO_RUFF, ROOT / "demos" / d) for d in linted),
    ]
    if args.title:
        checks.append(("Checking the pull request title", "Pull request title",
                       [sys.executable, "scripts/check_pr.py", args.title], ROOT))

    failed = 0
    for running, finished, command, cwd in checks:
        with ui.step(running, finished) as step:
            ok, out = outcome(command, cwd)
            if ok:
                total = re.findall(r"(\d+) checks", out) if command is CONVENTIONS else []
                step.done(f"{total[-1]} checks" if total else "")
                continue
            failed += 1
            if command is CONVENTIONS:  # keep the failing groups, without their mark, and their problems
                out = chr(10).join("  " + line.strip() if line.startswith("      ") else line.strip()[2:]
                                   for line in out.splitlines()
                                   if line.startswith("      ")
                                   or (line.strip()[:2] in ("✘ ", "x ") and "checks," not in line))
            step.fail(shorten(out))
    if not linted:
        ui.line(f"  {ui.paint(ui.glyph['dot'], dim=True)} "
                f"{ui.paint('No demo changed; --all lints every one.', dim=True)}")
    if not args.title:
        ui.line(f"  {ui.paint(ui.glyph['dot'], dim=True)} "
                f"{ui.paint('Add --title to check the pull request title as well.', dim=True)}")

    ui.line()
    if failed:
        ui.line(f"  {ui.paint(ui.glyph['fail'], RED, bold=True)} {plural(failed, 'check')} failed. "
                "Fix what is listed above, then run this again.")
    else:
        ui.line(f"  {ui.paint(ui.glyph['ok'], GREEN, bold=True)} Ready for a pull request. "
                "CI runs these again, and builds the images.")
    ui.line()
    return 1 if failed else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status", help="list the lab's containers, images and model volumes")
    cleaner = sub.add_parser("clean", help="stop the demos and remove leftover images")
    cleaner.add_argument("--all", action="store_true", help="also remove the images of the existing demos")
    cleaner.add_argument("--models", action="store_true", help="also remove the downloaded model volumes")
    cleaner.add_argument("--build-cache", action="store_true", help="also prune Docker's build cache (shared)")
    cleaner.add_argument("--dry-run", action="store_true", help="print the commands without running them")
    checker = sub.add_parser("check", help="run what CI checks, before you push")
    checker.add_argument("--title", help="also check this pull request title")
    checker.add_argument("--all", action="store_true", help="lint every demo, not only the changed ones")
    args = parser.parse_args()

    if args.command != "check" and not shutil.which("docker"):
        sys.exit("docker is not on the PATH.")
    ui = Terminal()
    ui.banner()
    if args.command == "check":
        return check(ui, args)
    return status(ui) if args.command == "status" else clean(ui, args)


if __name__ == "__main__":
    sys.exit(main())
