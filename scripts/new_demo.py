"""Create a new demo that runs, and passes the repository checks, before the attack is written.

    python scripts/new_demo.py <topic> --title "<Attack name>" [--mitigated] [--postgres] [--port N]

Copies `scripts/demo_template/` to `demos/<topic>-demo/`, starts its write-up in
`docs/writeups/NN-<slug>.md`, draws placeholder C4 figures, locks the dependencies with uv,
and lists the demo in `docker-compose.yml`, `README.md` and `docs/README.md`.

The second variant is `safe`, or `mitigated` with `--mitigated`: `safe` when the defense
removes the cause, `mitigated` when it only limits the damage.

What is left is marked `TODO(attack)`: the vulnerable and the safe implementation, the
payloads in `bruno/02-attack` and `bruno/03-defense`, and the text of the README and the
write-up. `scripts/check_repo.py` fails while any marker is left.
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

from terminal import Terminal

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = Path(__file__).resolve().parent / "demo_template"
FIGURES = ROOT / ".claude" / "skills" / "house-style-figures" / "new_figures.py"

TOPIC = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
MARKER = re.compile(r"^(?:#|<!--)\s*\[(/?)([a-z-]+)\]\s*(?:-->)?$")
ONE_LINE_DOC = re.compile(r'(""".+)\n[ \t]*"""')
TEXT_SUFFIXES = {".py", ".md", ".yml", ".yaml", ".toml", ".example", ""}
POSTGRES_ONLY = {"app/seed.py", "app/infrastructure/database.py", "app/infrastructure/seed.py"}
SKIP = ("__pycache__", ".ruff_cache", ".mypy_cache")
PORT = re.compile(r"127\.0\.0\.1:(\d+):")
YOUR_DEMO_ROW = re.compile(r"^\| (\d\d) \| \*your demo\* \| `:(\d+)` \|.*$", re.M)


def keep_blocks(text: str, flags: set[str]) -> str:
    """Keeps the `[name]` ... `[/name]` blocks whose name is in `flags`, drops the others.

    Args:
        text: The template text.
        flags: The active block names, such as `postgres` or `no-postgres`.

    Returns:
        The text without the marker lines and without the inactive blocks.
    """
    out: list[str] = []
    stack: list[bool] = []
    for line in text.splitlines(keepends=True):
        marker = MARKER.match(line.strip())
        if marker:
            closing, name = marker.groups()
            if closing:
                stack.pop()
            else:
                stack.append(name in flags)
            continue
        if all(stack):
            out.append(line)
    if stack:
        raise ValueError("unclosed block marker")
    return "".join(out)


def render(text: str, values: dict[str, str], flags: set[str], python: bool) -> str:
    """Applies the blocks and the placeholders to one template file.

    Args:
        text: The template text.
        values: The placeholder values, by placeholder.
        flags: The active block names.
        python: Whether the file is Python, whose one-line docstrings are rejoined.

    Returns:
        The rendered text.
    """
    text = keep_blocks(text, flags)
    for placeholder, value in values.items():
        text = text.replace(placeholder, value)
    return ONE_LINE_DOC.sub(r'\1"""', text) if python else text


def next_number() -> str:
    """Returns the next write-up number, two digits."""
    numbers = [int(p.name[:2]) for p in (ROOT / "docs" / "writeups").glob("[0-9][0-9]-*.md")]
    return f"{max(numbers, default=0) + 1:02d}"


def next_port() -> int:
    """Returns the port after the highest one any demo publishes."""
    ports = [int(m) for compose in (ROOT / "demos").glob("*-demo/compose.yaml")
             for m in PORT.findall(compose.read_text(encoding="utf-8"))]
    return max(ports, default=8000) + 1


def copy_template(target: Path, values: dict[str, str], postgres: bool) -> int:
    """Copies the template to `target`, rendering every text file, and returns the file count."""
    flags = {"postgres"} if postgres else {"no-postgres"}
    count = 0
    for source in sorted(TEMPLATE.rglob("*")):
        rel = source.relative_to(TEMPLATE).as_posix()
        if source.is_dir() or any(part in rel for part in SKIP) or (rel in POSTGRES_ONLY and not postgres):
            continue
        destination = target / render(rel, values, set(), python=False)
        destination.parent.mkdir(parents=True, exist_ok=True)
        if source.suffix in TEXT_SUFFIXES or source.name.startswith("."):
            text = render(source.read_text(encoding="utf-8"), values, flags, source.suffix == ".py")
            destination.write_text(text, encoding="utf-8", newline="\n")
        else:
            shutil.copyfile(source, destination)
        count += 1
    return count


def start_writeup(path: Path, number: str, title: str) -> None:
    """Writes the write-up from the skeleton in `docs/templates/writeup.md`."""
    template = (ROOT / "docs" / "templates" / "writeup.md").read_text(encoding="utf-8")
    skeleton = template[template.index("# NN — <Attack name>"):]
    heading = f"# {number} — {title}\n\n<!-- TODO(attack): fill in every section, then delete the instructions. -->"
    path.write_text(skeleton.replace("# NN — <Attack name>", heading, 1), encoding="utf-8", newline="\n")


def register(name: str, number: str, slug: str, title: str, port: int) -> None:
    """Lists the demo in docker-compose.yml, README.md and docs/README.md."""
    compose = ROOT / "docker-compose.yml"
    lines = compose.read_text(encoding="utf-8").splitlines()
    last = max(i for i, line in enumerate(lines) if line.strip().startswith("- demos/"))
    lines.insert(last + 1, f"  - demos/{name}/compose.yaml")
    compose.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")

    readme = ROOT / "README.md"
    text = readme.read_text(encoding="utf-8")
    row = (f"| {number} | [**{name}**](demos/{name}/README.md) | `:{port}` "
           "| <!-- TODO(attack): the attack, in one line --> "
           "| <!-- TODO(attack): the fix or mitigation, in one line --> |")
    following = f"| {int(number) + 1:02d} | *your demo* | `:{port + 1}` | — | [Add one](CONTRIBUTING.md) |"
    text, found = YOUR_DEMO_ROW.subn(row + "\n" + following, text, count=1)
    if not found:
        text = text.replace("\n\n> **Not every attack", "\n" + row + "\n\n> **Not every attack", 1)
    demos = len(list((ROOT / "demos").glob("*-demo")))
    text = re.sub(r"badge/demos-\d+-", f"badge/demos-{demos}-", text)
    text = re.sub(r'alt="\d+ demos"', f'alt="{demos} demos"', text)
    readme.write_text(text, encoding="utf-8", newline="\n")

    index = ROOT / "docs" / "README.md"
    lines = index.read_text(encoding="utf-8").splitlines()
    last = max(i for i, line in enumerate(lines) if line.startswith("| [") and "writeups/" in line)
    lines.insert(last + 1, f"| [{number}](writeups/{number}-{slug}.md) | **{title}** "
                           f"| `demos/{name}/` (`:{port}`) "
                           f"| [`demos/{name}/README.md`](../demos/{name}/README.md) |")
    index.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def run(command: list[str], cwd: Path = ROOT) -> str:
    """Runs a command, and returns its error output if it failed, or an empty string."""
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
    if result.returncode == 0:
        return ""
    return f"`{' '.join(command)}` failed:\n{(result.stderr or result.stdout).strip()}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("topic", help="short lowercase name, e.g. xss; the folder becomes <topic>-demo")
    parser.add_argument("--title", required=True, help='the attack, e.g. "Cross-site scripting"')
    parser.add_argument("--mitigated", action="store_true",
                        help="name the second variant `mitigated`: the defense limits the damage, it does not remove the cause")
    parser.add_argument("--postgres", action="store_true", help="add a PostgreSQL database and a seed job")
    parser.add_argument("--port", type=int, help="the host port; defaults to the next free one")
    args = parser.parse_args()

    if not TOPIC.match(args.topic) or args.topic.endswith("demo"):
        parser.error("the topic is lowercase letters, digits and dashes, without -demo: e.g. xss")
    name = f"{args.topic}-demo"
    target = ROOT / "demos" / name
    number = next_number()
    slug = re.sub(r"[^a-z0-9]+", "-", args.title.lower()).strip("-")
    writeup = ROOT / "docs" / "writeups" / f"{number}-{slug}.md"
    port = args.port or next_port()
    if target.exists() or writeup.exists():
        parser.error(f"{target.relative_to(ROOT)} or {writeup.relative_to(ROOT)} already exists")

    values = {"__NAME__": name, "__TOPIC__": args.topic, "__PREFIX__": args.topic.upper().replace("-", "_"),
              "__PORT__": str(port), "__NN__": number, "__SLUG__": slug, "__TITLE__": args.title}
    second = "mitigated" if args.mitigated else "safe"
    values |= {"__safe__": second, "__Safe__": second.capitalize(), "__SAFE__": second.upper()}

    ui = Terminal()
    dot = ui.glyph["dot"]
    ui.banner()
    ui.line(f"  {ui.paint('New demo', bold=True)}  {name}")
    for key, value in (("write-up", f"{number} {dot} {args.title}"),
                       ("port", f"127.0.0.1:{port}"),
                       ("variants", f"vulnerable {dot} {second}"),
                       ("database", "PostgreSQL" if args.postgres else "none")):
        ui.line(f"    {ui.paint(f'{key:<10}', dim=True)}{value}")
    ui.line()

    with ui.step("Copying the template", "Copied the template") as step:
        step.done(f"{copy_template(target, values, args.postgres)} files")
    with ui.step("Starting the write-up", "Started the write-up") as step:
        start_writeup(writeup, number, args.title)
        step.done(writeup.relative_to(ROOT).as_posix())
    with ui.step("Listing the demo", "Listed the demo") as step:
        register(name, number, slug, args.title, port)
        step.done(f"compose file {dot} README {dot} docs index")
    with ui.step("Drawing the C4 figures", "Drew the placeholder C4 figures") as step:
        problem = (run([sys.executable, str(FIGURES), f"demos/{name}"])
                   or run([sys.executable, f"demos/{name}/docs/diagrams.py"]))
        if problem:
            step.warn(problem)
        else:
            step.done(f"{len(list((target / 'docs').rglob('*.svg')))} figures")
    with ui.step("Locking the dependencies", "Locked the dependencies") as step:
        if not shutil.which("uv"):
            step.warn(f"uv is not installed: run `uv lock` in demos/{name}, "
                      "the Dockerfile installs from uv.lock")
        elif problem := run(["uv", "lock", "--quiet"], cwd=target):
            step.warn(problem)
        else:
            step.done("uv.lock")

    todo = sorted({p.relative_to(ROOT).as_posix()
                   for p in [*target.rglob("*"), writeup, ROOT / "README.md", ROOT / "docs" / "README.md"]
                   if p.is_file() and "TODO(attack)" in p.read_text(encoding="utf-8", errors="ignore")})
    prefix = f"demos/{name}/"
    ui.line()
    ui.line(f"  {ui.paint('Left for you', bold=True)}  "
            f"{ui.paint(f'{len(todo)} files marked TODO(attack)', dim=True)}")
    for path in todo:
        inside = path.startswith(prefix)
        ui.line("    " + (ui.paint(prefix, dim=True) + path[len(prefix):] if inside else path))
    ui.line()
    ui.line(f"  {ui.paint('Run it', bold=True)}")
    ui.line(f"    cd demos/{name} && docker compose up --build")
    ui.line(f"    {ui.paint(ui.glyph['arrow'], dim=True)} http://127.0.0.1:{port}/docs")
    ui.line()
    return 0


if __name__ == "__main__":
    sys.exit(main())
