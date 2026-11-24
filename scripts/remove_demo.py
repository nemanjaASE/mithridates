"""Undo scripts/new_demo.py: remove a demo, its write-up and the rows that list it.

    python scripts/remove_demo.py <topic> [--yes]

Deletes `demos/<topic>-demo/` and the demo's write-up in `docs/writeups/`, and takes the
demo out of `docker-compose.yml`, `README.md` and `docs/README.md`. The README's
*your demo* row and demo badge are worked out again from the demos that are left, the way
the generator works them out, so after a trial run every file is back as it was before
`new_demo.py` ran.

It lists what it will remove and asks first; `--yes` removes without asking. A file git
has no committed copy of cannot be brought back, and the list says how many there are.

Docker is not touched: if the demo was started, `python scripts/lab.py clean` stops it and
removes its image once its folder is gone.
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
from collections.abc import Callable
from pathlib import Path

from lab import git, plural
from new_demo import ROOT, TOPIC, YOUR_DEMO_ROW, count_demos, next_number, next_port, your_demo_row
from terminal import GREEN, YELLOW, Terminal

COMPOSE = ROOT / "docker-compose.yml"
README = ROOT / "README.md"
INDEX = ROOT / "docs" / "README.md"
WRITEUPS = ROOT / "docs" / "writeups"
# The write-up as docs/README.md links it, and as the line the demo template's README links it on.
INDEXED = re.compile(r"\(writeups/(\d\d-[a-z0-9-]+\.md)\)")
STORY = re.compile(r"full story of the attack:.*?docs/writeups/(\d\d-[a-z0-9-]+\.md)")


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def listings(name: str) -> dict[Path, Callable[[str], bool]]:
    """The files new_demo.py lists a demo in, each with a test for the line that lists it."""
    return {
        COMPOSE: lambda line: line.strip() == f"- demos/{name}/compose.yaml",
        README: lambda line: line.startswith("| ") and f"](demos/{name}/README.md)" in line,
        INDEX: lambda line: line.startswith("| [") and f"`demos/{name}/`" in line,
    }


def listed_in(name: str) -> list[Path]:
    """The files that still list the demo."""
    return [path for path, lists in listings(name).items()
            if any(lists(line) for line in path.read_text(encoding="utf-8").splitlines())]


def find_writeup(name: str) -> Path | None:
    """The demo's write-up: the one its row in docs/README.md links, or else its README."""
    rows = [line for line in INDEX.read_text(encoding="utf-8").splitlines()
            if listings(name)[INDEX](line)]
    readme = ROOT / "demos" / name / "README.md"
    story = readme.read_text(encoding="utf-8") if readme.exists() else ""
    names = [m.group(1) for row in rows for m in INDEXED.finditer(row)]
    names += [m.group(1) for m in STORY.finditer(story)]
    return next((WRITEUPS / n for n in names if (WRITEUPS / n).is_file()), None)


def count_files(path: Path) -> tuple[int, int | None]:
    """How many files `path` holds, and how many of them git has no committed copy of.

    Files git ignores, such as a virtual environment, are not counted. Without git every
    file is counted, and the second number is None.
    """
    tracked = git("ls-files", "--cached", "--others", "--exclude-standard", "--", rel(path))
    changed = git("status", "--porcelain", "--untracked-files=all", "--", rel(path))
    if tracked is None or changed is None:
        files = [path] if path.is_file() else [p for p in path.rglob("*") if p.is_file()]
        return len(files), None
    return len(tracked.splitlines()), len(changed.splitlines())


def unlist(name: str) -> list[Path]:
    """Takes out the demo's rows, and works out the README's next-demo row and badge again.

    Runs after the demo's folder and write-up are deleted, because the next number, the next
    port and the demo count are read from what is left. Returns the files it changed.
    """
    changed = []
    row = your_demo_row(next_number(), next_port())
    for path, lists in listings(name).items():
        text = path.read_text(encoding="utf-8")
        kept = "".join(line for line in text.splitlines(keepends=True) if not lists(line))
        if path == README:
            kept = count_demos(YOUR_DEMO_ROW.sub(lambda _: row, kept, count=1))
        if kept != text:
            path.write_text(kept, encoding="utf-8", newline="\n")
            changed.append(path)
    return changed


def delete(ui: Terminal, running: str, finished: str, path: Path) -> bool:
    """Deletes a file or a folder as one step, and returns whether it is gone."""
    shown = rel(path) + ("/" if path.is_dir() else "")
    with ui.step(running, finished) as step:
        try:
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
        except OSError as error:
            step.fail(f"{error}\nClose whatever has a file open in it, then run this again.")
            return False
        step.done(shown)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("topic", help="the topic given to new_demo.py, e.g. xss; xss-demo works too")
    parser.add_argument("--yes", action="store_true", help="remove without asking")
    args = parser.parse_args()

    topic = args.topic.removesuffix("-demo")
    if not TOPIC.match(topic):
        parser.error("the topic is lowercase letters, digits and dashes: e.g. xss")
    name = f"{topic}-demo"
    target = ROOT / "demos" / name
    writeup = find_writeup(name)
    lists = listed_in(name)
    if not (target.exists() or writeup or lists):
        parser.error(f"demos/{name} does not exist, and nothing lists it")

    ui = Terminal()
    dot = ui.glyph["dot"]
    ui.banner(compact=True)
    ui.line(f"  {ui.paint('Remove demo', bold=True)}  {name}")
    rows: list[tuple[str, str]] = []
    lost = 0
    for key, path in (("folder", target), ("write-up", writeup)):
        if path is None or not path.exists():
            continue
        files, uncommitted = count_files(path)
        lost += uncommitted or 0
        if path.is_dir():
            shown, note = f"{rel(path)}/", plural(files, "file")
            if uncommitted is not None:
                note += ", " + ("all committed" if not uncommitted else
                                "none committed" if uncommitted == files else
                                f"{uncommitted} not committed")
        else:
            shown, note = rel(path), {None: "", 0: "committed"}.get(uncommitted, "not committed")
        rows.append((key, f"{shown}  {ui.paint(note, dim=True)}" if note else shown))
    if lists:
        rows.append(("listed in", f" {dot} ".join(rel(p) for p in lists)))
    for key, value in rows:
        ui.line(f"    {ui.paint(f'{key:<10}', dim=True)}{value}")
    ui.line()

    if not args.yes:
        if lost:
            ui.line("  " + ui.paint(f"Git has no copy of {plural(lost, 'file')}, "
                                    "so this cannot be undone.", YELLOW))
        try:
            answer = input("  Remove them? [y/N] ")
        except EOFError:  # no one to answer, as in CI
            answer = ""
            ui.line()
        ui.line()
        if answer.strip().lower() not in ("y", "yes"):
            ui.line(f"  Nothing removed. {ui.paint('--yes removes without asking.', dim=True)}")
            ui.line()
            return 1

    if target.exists() and not delete(ui, "Deleting the demo", "Deleted the demo", target):
        return 1
    if writeup and writeup.exists() and not delete(ui, "Deleting the write-up",
                                                   "Deleted the write-up", writeup):
        return 1
    with ui.step("Unlisting the demo", "Unlisted the demo") as step:
        step.done(f" {dot} ".join(rel(p) for p in unlist(name)) or "nothing listed it")

    ui.line()
    ui.line(f"  {ui.paint(ui.glyph['ok'], GREEN, bold=True)} Removed {name}.")
    command = ui.paint("python scripts/lab.py clean", bold=True)
    ui.line(f"  {ui.paint(ui.glyph['arrow'], dim=True)} If you started it, {command} "
            "stops it and removes its image.")
    ui.line()
    return 0


if __name__ == "__main__":
    sys.exit(main())
