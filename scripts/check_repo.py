"""Check the conventions every demo in this repository shares.

    uv run --no-project --with pyyaml python scripts/check_repo.py [--allow-todo]

CONTRIBUTING.md describes what a demo has to provide. The part of that contract which can
be verified by reading the files is verified here, so a pull request does not depend on a
reviewer remembering the list. What this script cannot see — whether the attack really
works, whether the write-up is honest — stays a human review.

A demo started with `scripts/new_demo.py` fails here while a `TODO(attack)` marker is left;
`--allow-todo` skips that check, which is how CI tests the generator itself.

Every check names the file it is about. Exit status is 0 when all of them pass, 1 otherwise.
"""
from __future__ import annotations

import os
import re
import sys
import tomllib
from pathlib import Path

import yaml
from terminal import GREEN, RED, Terminal

ROOT = Path(__file__).resolve().parent.parent
# `demo_template` is not a document until scripts/new_demo.py renders it.
PRUNE = {".git", ".venv", "venv", "__pycache__", "node_modules", ".ruff_cache", ".mypy_cache",
         "demo_template"}

# The folders every Bruno collection has, whatever the demo is about. `02-` and `03-` are
# named after the demo's own features, so only their number is fixed.
FIXED_BRUNO = ("00-environments", "01-auth", "04-hardening")

# docs/templates/demo-readme.md: the headings every service README carries, in this order. A demo
# may add its own sections in between — `## The database` is one — but not drop these.
README_SECTIONS = ("What this service does", "Technology", "Running it",
                   "The attack, step by step",
                   "How it works", "Configuration", "Verification",
                   "Troubleshooting")

# docs/templates/writeup.md: the classification table every write-up opens with.
WRITEUP_ROWS = ("OWASP Top 10", "CWE", "CVSS v4.0", "CIA")

# The C4 model is the one requirement on figures: every README shows these four levels,
# in this order, each with a figure. How the figures look is up to the demo.
C4_LEVELS = ("Level 1", "Level 2", "Level 3", "Level 4")

# A secret read from the environment must have no fallback in code: a process that comes up
# with a credential published in this repository is the bug the lab is teaching about.
ENV_DEFAULT = re.compile(
    r"""os\.(?:environ\.get|getenv)\(\s*["']([A-Z0-9_]+)["']\s*,\s*["'][^"']+["']"""
)
SECRETISH = re.compile(r"SECRET|PASSWORD|TOKEN|KEY|CREDENTIAL")

# `${NAME:-default}` in compose.yaml, and `# NAME=value` (commented or not) in .env.example.
COMPOSE_VAR = re.compile(r"\$\{([A-Z][A-Z0-9_]*)")
EXAMPLE_VAR = re.compile(r"^#?\s*([A-Z][A-Z0-9_]*)=", re.M)

MD_LINK = re.compile(r"!?\[[^\]]*\]\(\s*([^)\s]+)")
IMG_SRC = re.compile(r'<img [^>]*?src="([^"]+)"')
# a heading may open with an icon: `## <img src="…" …>Running it`
HEADING = r"(?:<img [^>]*>\s*)?"
CODE_FENCE = re.compile(r"^```.*?^```", re.M | re.S)
# Latin text only: a Cyrillic lookalike of a Latin letter is invisible in a review diff.
CYRILLIC = re.compile(r"[\u0400-\u04ff]")
# What scripts/new_demo.py leaves for the author to fill in.
TODO_MARKER = "TODO(attack)"


class Report:
    """Failures grouped by the file or demo they belong to."""

    def __init__(self) -> None:
        self.failures: dict[str, list[str]] = {}
        self.counts: dict[str, int] = {}
        self.count = 0

    def check(self, subject: str, ok: object, message: str) -> bool:
        self.count += 1
        self.counts[subject] = self.counts.get(subject, 0) + 1
        if not ok:
            self.failures.setdefault(subject, []).append(message)
        return bool(ok)

    def print(self, ui: Terminal, subjects: list[str]) -> int:
        """Prints one line per subject, and every failure under its subject.

        Args:
            ui: Where to print.
            subjects: The subjects in the order to print them; a failing subject that is
                not listed is printed after them.

        Returns:
            The exit status: 0 when every check passed, 1 otherwise.
        """
        ok, fail = ui.paint(ui.glyph["ok"], GREEN, bold=True), ui.paint(ui.glyph["fail"], RED, bold=True)
        for subject in [*subjects, *(s for s in self.failures if s not in subjects)]:
            problems = self.failures.get(subject, [])
            count = self.counts.get(subject, 0)
            if problems:
                note = ui.paint(f"{len(problems)} of {count} failed", RED)
                ui.line(f"  {fail} {ui.paint(subject, RED)}{' ' * max(1, 20 - len(subject))}{note}")
                for problem in problems:
                    ui.line(f"      {problem}")
            else:
                ui.line(f"  {ok} {subject}{' ' * max(1, 20 - len(subject))}{ui.paint(f'{count} checks', dim=True)}")
        failed = sum(len(v) for v in self.failures.values())
        ui.line()
        if failed:
            ui.line(f"  {fail} {self.count} checks, {ui.paint(f'{failed} failed', RED, bold=True)}")
        else:
            ui.line(f"  {ok} {self.count} checks, all passed")
        ui.line()
        return 1 if failed else 0


def walk(suffixes: tuple[str, ...], base: Path = ROOT) -> list[Path]:
    """Every file of the given kind under `base` that belongs to the repository."""
    found: list[Path] = []
    for folder, dirnames, filenames in os.walk(base):
        dirnames[:] = sorted(d for d in dirnames if d not in PRUNE)
        for filename in sorted(filenames):
            if filename.endswith(suffixes):
                found.append(Path(folder) / filename)
    return found


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def published_ports(service: dict) -> list[tuple[str, str]]:
    """(host_ip, host_port) for every port the service publishes, in either syntax."""
    out = []
    for entry in service.get("ports", []) or []:
        if isinstance(entry, dict):
            out.append((str(entry.get("host_ip", "")), str(entry.get("published", ""))))
        else:
            parts = str(entry).split(":")
            out.append((parts[0], parts[1]) if len(parts) == 3 else ("", parts[0]))
    return out


def environment(service: dict) -> dict[str, str]:
    """A service's environment as a dict, from either compose syntax."""
    env = service.get("environment") or {}
    if isinstance(env, list):
        return dict(item.split("=", 1) for item in env if "=" in item)
    return {str(k): str(v) for k, v in env.items()}


def check_demo(demo: Path, report: Report) -> list[tuple[str, str]]:
    """Everything a single demo folder has to provide. Returns its published ports."""
    name = demo.name
    for required in ("compose.yaml", "Dockerfile", "README.md", "bruno/opencollection.yml"):
        report.check(name, (demo / required).exists(), f"missing {required}")

    for folder in FIXED_BRUNO:
        report.check(name, (demo / "bruno" / folder).is_dir(), f"missing bruno/{folder}/")
    for number in ("02", "03"):
        found = list((demo / "bruno").glob(f"{number}-*")) if (demo / "bruno").is_dir() else []
        report.check(name, found, f"missing a bruno/{number}-… folder (the attack and its defense)")

    check_env_example(demo, report)

    ports: list[tuple[str, str]] = []
    if (demo / "compose.yaml").exists():
        services = load_yaml(demo / "compose.yaml").get("services", {})
        report.check(name, name in services, f"compose.yaml has no service named {name}")
        for service, body in services.items():
            body = body or {}
            for host_ip, host_port in published_ports(body):
                ports.append((service, host_port))
                report.check(
                    name,
                    host_ip == "127.0.0.1",
                    f"{service} publishes {host_port} on '{host_ip or 'every interface'}'"
                    " — the lab binds to 127.0.0.1 only",
                )
                report.check(name, service == name,
                             f"only {name} may publish a port, not {service}")
                # the startup line prints PUBLIC_URL, so it has to name the published port
                url = str(environment(body).get("PUBLIC_URL", ""))
                report.check(name, not url or url.rstrip("/").endswith(f":{host_port}"),
                             f"{service}: PUBLIC_URL {url} does not use the published port {host_port}")
            if "build" in body:
                opts = body.get("security_opt") or []
                report.check(name, body.get("read_only") is True, f"{service} is not read_only")
                report.check(name, "ALL" in (body.get("cap_drop") or []),
                             f"{service} does not cap_drop ALL")
                report.check(name, "no-new-privileges:true" in opts,
                             f"{service} allows new privileges")

    if (demo / "README.md").exists():
        readme = (demo / "README.md").read_text(encoding="utf-8")
        writeups = re.findall(r"\.\./\.\./docs/writeups/(\d\d-[a-z0-9-]+\.md)", readme)
        report.check(name, writeups, "README.md does not link to a ../../docs/writeups/NN-….md write-up")
        for writeup in set(writeups):
            path = ROOT / "docs" / "writeups" / writeup
            if not report.check(name, path.exists(), f"docs/writeups/{writeup} does not exist"):
                continue
            text = path.read_text(encoding="utf-8")
            for row in WRITEUP_ROWS:
                report.check(name, re.search(rf"^\|\s*\*\*{re.escape(row)}\*\*\s*\|", text, re.M),
                             f"docs/writeups/{writeup} has no **{row}** row in its classification table")

        sections = re.findall(r"^## " + HEADING + r"(.+)$", readme, re.M)
        position = 0
        for wanted in README_SECTIONS:
            if wanted in sections[position:]:
                position = sections.index(wanted, position) + 1
            else:
                report.check(name, False,
                             f"README.md is missing '## {wanted}', or has it out of the order"
                             " docs/templates/demo-readme.md sets")
        report.check(name, readme.startswith("# " + name + chr(10)),
                     f"README.md does not open with the title '# {name}'")

    # the C4 model, in any tool and any style: four levels, in order, each with a figure
    if (demo / "README.md").exists():
        found = re.search(r"^## " + HEADING + "How it works", readme, re.M)
        start = found.start() if found else -1
        end = readme.find(chr(10) + "## ", start + 1)
        how = readme[start:end if end > 0 else None] if start >= 0 else ""
        at = 0
        for level, after in zip(C4_LEVELS, (*C4_LEVELS[1:], None), strict=True):
            i = how.find(level, at)
            j = how.find(after, i) if after and i >= 0 else -1
            part = how[i:j if j > 0 else None] if i >= 0 else ""
            report.check(name, i >= 0, f"README.md: '## How it works' has no C4 {level},"
                         " or has it out of order — the C4 model is required")
            report.check(name, "![" in part or "<img" in part,
                         f"README.md: C4 {level} has no figure")
            at = max(at, i)


    if (demo / "pyproject.toml").exists():
        config = tomllib.loads((demo / "pyproject.toml").read_text(encoding="utf-8"))
        tools = config.get("tool", {})
        report.check(name, "ruff" in tools, "pyproject.toml has no [tool.ruff] section")
        report.check(name, "mypy" in tools, "pyproject.toml has no [tool.mypy] section")
        dev = " ".join(config.get("dependency-groups", {}).get("dev", []))
        report.check(name, "ruff" in dev, "ruff is not in the dev dependency group")

    for index in (ROOT / "README.md", ROOT / "docs" / "README.md"):
        report.check(name, name in index.read_text(encoding="utf-8"), f"not listed in {rel(index)}")
    return ports


def check_env_example(demo: Path, report: Report) -> None:
    """`.env.example` names exactly the variables compose.yaml reads.

    Compose reads `.env` from the demo's own folder, whether the demo is started there or
    through the root `docker-compose.yml`, so the example sits next to compose.yaml. A
    variable missing from it cannot be found; one compose never reads does nothing.
    """
    name = demo.name
    compose = demo / "compose.yaml"
    read = set(COMPOSE_VAR.findall(compose.read_text(encoding="utf-8"))) if compose.exists() else set()
    if not read:
        return
    example = demo / ".env.example"
    if not report.check(name, example.exists(),
                        "compose.yaml reads variables, but there is no .env.example next to it"):
        return
    listed = set(EXAMPLE_VAR.findall(example.read_text(encoding="utf-8")))
    report.check(name, not read - listed,
                 f".env.example does not name {', '.join(sorted(read - listed))}, which compose.yaml reads")
    report.check(name, not listed - read,
                 f".env.example names {', '.join(sorted(listed - read))}, which compose.yaml never reads")


def check_repository(demos: list[Path], report: Report) -> None:
    subject = "repository"
    compose = load_yaml(ROOT / "docker-compose.yml")
    included = {
        (entry.get("path") if isinstance(entry, dict) else entry)
        for entry in compose.get("include", [])
    }
    for demo in demos:
        report.check(subject, f"demos/{demo.name}/compose.yaml" in included,
                     f"docker-compose.yml does not include demos/{demo.name}/compose.yaml")
    for entry in included:
        report.check(subject, (ROOT / str(entry)).exists(),
                     f"docker-compose.yml includes a missing {entry}")

    report.check(subject, (ROOT / ".gitignore").exists(), "no .gitignore")
    gitignore = ROOT / ".gitignore"
    ignored = gitignore.read_text(encoding="utf-8").split() if gitignore.exists() else []
    report.check(subject, ".env" in ignored, ".gitignore does not ignore .env")


def check_ports(ports: dict[str, list[tuple[str, str]]], report: Report) -> None:
    seen: dict[str, str] = {}
    for demo, entries in ports.items():
        for _, port in entries:
            if port in seen and seen[port] != demo:
                report.check("repository", False,
                             f"port {port} is claimed by both {seen[port]} and {demo}")
            seen[port] = demo


def check_text(report: Report) -> None:
    for path in walk((".md", ".py", ".yml", ".yaml", ".toml", ".bru")):
        body = path.read_text(encoding="utf-8", errors="replace")
        found = [f"{rel(path)}:{body[: m.start()].count(chr(10)) + 1} has a Cyrillic character"
                 f" (U+{ord(m.group()):04X})" for m in CYRILLIC.finditer(body)]
        for problem in found or [""]:  # one check per file, or one per problem in it
            report.check("text", not problem, problem)

    for path in walk((".md",)):
        body = CODE_FENCE.sub("", path.read_text(encoding="utf-8"))
        for target in MD_LINK.findall(body) + IMG_SRC.findall(body):
            if target.startswith(("http://", "https://", "mailto:", "#", "<")):
                continue
            resolved = (path.parent / target.split("#")[0]).resolve()
            report.check("links", resolved.exists(), f"{rel(path)} links to a missing {target}")

    for path in walk((".py",)):
        found = []
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            match = ENV_DEFAULT.search(line)
            if match and SECRETISH.search(match.group(1)):
                found.append(f"{rel(path)}:{number} gives {match.group(1)} a default value in code")
        for problem in found or [""]:  # one check per file, or one per problem in it
            report.check("secrets", not problem, problem)


def check_todo(demos: list[Path], report: Report) -> None:
    """No `TODO(attack)` marker is left in a demo, its write-up, or the two indexes."""
    texts = (".md", ".py", ".yml", ".yaml", ".toml", ".example")
    for demo in demos:
        paths = walk(texts, demo)
        readme = demo / "README.md"
        if readme.exists():
            linked = re.findall(r"\.\./\.\./docs/writeups/(\d\d-[a-z0-9-]+\.md)",
                                readme.read_text(encoding="utf-8"))
            paths += [ROOT / "docs" / "writeups" / name for name in linked]
        for path in sorted(set(paths)):
            if path.exists():
                count = path.read_text(encoding="utf-8").count(TODO_MARKER)
                report.check(demo.name, count == 0,
                             f"{rel(path)} still has {count} {TODO_MARKER} marker(s)")
    # The indexes may name the marker in prose; the generator leaves it as an HTML comment.
    for path in (ROOT / "README.md", ROOT / "docs" / "README.md"):
        count = path.read_text(encoding="utf-8").count("<!-- " + TODO_MARKER)
        report.check("repository", count == 0, f"{rel(path)} still has {count} {TODO_MARKER} marker(s)")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    allow_todo = "--allow-todo" in sys.argv[1:]
    demos = sorted(p for p in (ROOT / "demos").iterdir() if p.is_dir() and p.name.endswith("-demo"))
    if not demos:
        print("no demos/*-demo folders found — is this the repository root?")
        return 1

    report = Report()
    ports = {demo.name: check_demo(demo, report) for demo in demos}
    check_repository(demos, report)
    check_ports(ports, report)
    check_text(report)
    if not allow_todo:
        check_todo(demos, report)

    ui = Terminal()
    if ui.live:  # the logo is for a person at a terminal, not for a CI log
        ui.banner()
    skipped = ui.paint(f"  {TODO_MARKER} not checked", dim=True) if allow_todo else ""
    ui.line(f"  {ui.paint('Conventions', bold=True)}  {len(demos)} demos{skipped}")
    ui.line()
    return report.print(ui, [d.name for d in demos] + ["repository", "links", "text", "secrets"])

if __name__ == "__main__":
    sys.exit(main())
