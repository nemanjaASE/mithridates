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


def copy_template(target: Path, values: dict[str, str], postgres: bool) -> None:
    """Copies the template to `target`, rendering every text file."""
    flags = {"postgres"} if postgres else {"no-postgres"}
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


def run(command: list[str], cwd: Path = ROOT) -> bool:
    """Runs a command, and reports whether it succeeded."""
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ! {' '.join(command)} failed:\n{result.stderr.strip()}")
    return result.returncode == 0


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
    copy_template(target, values, args.postgres)
    start_writeup(writeup, number, args.title)
    register(name, number, slug, args.title, port)
    print(f"created demos/{name} (:{port}) and docs/writeups/{writeup.name}")

    if run([sys.executable, str(FIGURES), f"demos/{name}"]) and run([sys.executable, f"demos/{name}/docs/diagrams.py"]):
        print("  drew the placeholder C4 figures")
    if shutil.which("uv") and run(["uv", "lock", "--quiet"], cwd=target):
        print("  locked the dependencies (uv.lock)")
    else:
        print("  ! run `uv lock` in the demo folder: the Dockerfile installs from uv.lock")

    todo = sorted({p.relative_to(ROOT).as_posix()
                   for p in [*target.rglob("*"), writeup, ROOT / "README.md", ROOT / "docs" / "README.md"]
                   if p.is_file() and "TODO(attack)" in p.read_text(encoding="utf-8", errors="ignore")})
    print("\nWhat is left is marked TODO(attack):")
    for path in todo:
        print(f"  {path}")
    print(f"\nRun it:  cd demos/{name} && docker compose up --build")
    return 0


if __name__ == "__main__":
    sys.exit(main())
