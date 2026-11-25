"""Start the figures of a new demo in the house style — if you want it.

The house style is optional: a demo must show the C4 model, but may draw it any way it
likes. This script is for a contributor who wants the look of the existing demos.

    python .claude/skills/house-style-figures/new_figures.py <topic>-demo [--postgres] [--mitigated]

Writes demos/<topic>-demo/docs/diagrams.py: the house-style block copied from
.claude/skills/house-style-figures/diagram_style.py, and the four figures every demo's
README carries — C1 context, C2 containers, C3 components, C4 code. They draw the code
scripts/new_demo.py writes, with the same options: a database with `--postgres`, and a
`mitigated` variant instead of `safe` with `--mitigated`. They pass check_figures.py, and
carry a TODO(attack) marker until the figures are redrawn for the demo's own attack; then
run `python demos/<topic>-demo/docs/diagrams.py` to draw them.

figure-kit.svg next to this file shows every part with the call that draws it, and
SKILL.md has the rules. The script never overwrites an existing file.
"""
import argparse
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]

HEAD = '''"""Render this demo's figures to SVG.

    python docs/diagrams.py

Writes c1-context.svg, c2-containers.svg, c3-components.svg and c4-code.svg for the
README, next to this file. Hand-editing generated SVG is no fun, so change it here and
re-run.

Everything between the two markers below is the repository's house style, copied verbatim
from `.claude/skills/house-style-figures/diagram_style.py`; `check_figures.py` there fails when the copies drift
apart.
Only the figures after it belong to this demo.
"""
from pathlib import Path

'''

FIGURES = '''

# TODO(attack): these figures draw the code the generator wrote. Redraw them for your
# attack: change the names, the boxes and the arrows below, run this file, and open the
# SVGs. .claude/skills/house-style-figures/figure-kit.svg shows every part and its call.

W = 1100
SYSTEM = "__NAME__"         # the demo; NAME is taken: the style uses it for a size


# --------------------------------------------------------------------------
# C4 level 1 — who uses it, and what it reaches outside itself
# --------------------------------------------------------------------------
def context():
    a = figure(W, f"System context diagram for {SYSTEM}")
    top, hb = 220, node_h("kind", ["what"])
    node(a, M, top, 230, "you", "learner, attacker", ["Bruno"], dash="4 3")
    node(a, 420, top, 260, SYSTEM, "software system", ["vulnerable and __safe__"], icon="fastapi")
    node(a, 814, top, 230, "Docker Hub", "container registry", ["base images"],
         dash="4 3", icon="docker")
    for x in (360, 740):
        boundary(a, x, top - 20, top + hb + 20)
    mid = top + hb // 2
    arrow(a, [(290, mid), (416, mid)], "attacks", ACCENT, at=(293, mid - 10))
    arrow(a, [(684, mid), (810, mid)], "pulls", at=(692, mid - 10))
    return caption(a, W, 1, "level 1 — the system, its user, and what it pulls from",
                   "compose.yaml, Dockerfile")


# --------------------------------------------------------------------------
# C4 level 2 — what runs, and the one way in
# --------------------------------------------------------------------------
def containers():
    a = figure(W, f"Container diagram for {SYSTEM}")
    under = len(a)                    # the system panel goes beneath everything in it
    top = 232
    hy = node(a, M, top, 180, "you", "Bruno", dash="4 3")
    node(a, 372, top, 300, SYSTEM, "FastAPI, uvicorn", accent=True, docker=True)
    bottom = top + hy
# [postgres]
    low = bottom + 70
    bottom = low + node(a, 372, low, 300, "database", "PostgreSQL 18", store=True, docker=True)
# [/postgres]
    panel = []
    zone(panel, 340, 196, 364, bottom + 36 - 196, SYSTEM)
    a[under:under] = panel
    boundary(a, 268, 176, bottom + 56)
    mid = top + hy // 2
    arrow(a, [(240, mid), (368, mid)], "attacks", ACCENT, at=(276, mid - 10))
# [postgres]
    arrow(a, [(522, top + hy + 4), (522, low - 4)], "SQL", at=(536, top + hy + 38))
# [/postgres]
    return caption(a, W, 2, "level 2 — the containers and the one published port",
                   "compose.yaml")


# --------------------------------------------------------------------------
# C4 level 3 — what one request passes through inside the container
# --------------------------------------------------------------------------
def components():
    a = figure(W, f"Component diagram for the {SYSTEM} container")
    left, centre, right, w = M, 399, 742, 302
    top = 212
    hy = node(a, left, top, w, "you", "Bruno", accent=True, dash="4 3")
    node(a, centre, top, w, "routers.py", "FastAPI")
    node(a, right, top, w, "RunFeatureUseCase", "application")
    mid = top + hy // 2
    arrow(a, [(362, mid), (395, mid)], None, ACCENT)
    arrow(a, [(705, mid), (738, mid)], None)

    port = top + hy + 48
    hp = node(a, right, port, w, "Feature", "port")
    arrow(a, [(893, top + hy + 4), (893, port - 4)], None)

    bus = port + hp + 40
    row = bus + 52
    node(a, left, row, w, "VulnerableFeature", "adapter", accent=True)
    node(a, right, row, w, "__Safe__Feature", "adapter", accent=SAFE)
    fork(a, (893, port + hp), bus, [(207, row - 4), (893, row - 4)], [ACCENT, SAFE], down=True)
    a.append(mono(217, bus + 32, "variant=vulnerable", LABEL, ACCENT))
    right = "variant=__safe__"         # left of its line, so it stays inside the margin
    a.append(mono(883 - mono_w(right, LABEL), bus + 32, right, LABEL, SAFE))
# [postgres]

    level = row + node_h("adapter", []) // 2
    hd = node_h("PostgreSQL 18", []) + 12          # a store is taller by its lid
    node(a, 465, level - hd // 2, 170, "database", "PostgreSQL 18", store=True)
    arrow(a, [(362, level), (461, level)], None, ACCENT)
    a.append(sans(411.5 - sans_w("the flaw", LABEL) / 2, level - 10, "the flaw", LABEL, ACCENT))
    arrow(a, [(738, level), (639, level)], None, SAFE)
    a.append(sans(688.5 - sans_w("the defense", LABEL) / 2, level - 10, "the defense", LABEL,
                  SAFE))
# [/postgres]
    return caption(a, W, 3, "level 3 — the components one request passes through",
                   "app/api/, app/application/, app/infrastructure/")


# --------------------------------------------------------------------------
# C4 level 4 — the port, and the two classes that implement it
# --------------------------------------------------------------------------
def code_level():
    a = figure(W, "Code diagram for the Feature port")
    top = 220
    hp = node(a, 399, top, 302, "Feature", "typing.Protocol", ["run(value, principal)"],
             mono_lines=True)
    low = top + hp + 80
    node(a, M, low, 302, "VulnerableFeature", "infrastructure", accent=True)
    node(a, 742, low, 302, "__Safe__Feature", "infrastructure", accent=SAFE)
    mid = top + hp // 2
    arrow(a, [(207, low - 4), (207, mid), (395, mid)], "implements", at=(217, low - 30))
    arrow(a, [(893, low - 4), (893, mid), (705, mid)], "implements", at=(903, low - 30))
    return caption(a, W, 4, "level 4 — one port, two implementations",
                   "app/domain/ports.py, app/infrastructure/feature/")


if __name__ == "__main__":
    render(Path(__file__).parent, [
        ("c1-context", context()),
        ("c2-containers", containers()),
        ("c3-components", components()),
        ("c4-code", code_level()),
    ])
'''
MARKER = re.compile(r"# \[(/?)([a-z-]+)\]\s*")


def keep_blocks(text: str, flags: set[str]) -> str:
    """Keeps the lines between `# [name]` and `# [/name]` when `name` is in `flags`."""
    out, keep = [], True
    for line in text.splitlines(keepends=True):
        marker = MARKER.fullmatch(line)
        if marker:
            keep = bool(marker[1]) or marker[2] in flags
            continue
        if keep:
            out.append(line)
    return "".join(out)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("demo", help="the demo's folder, e.g. demos/xss-demo")
    parser.add_argument("--postgres", action="store_true",
                        help="the demo has a PostgreSQL database, as new_demo.py --postgres makes")
    parser.add_argument("--mitigated", action="store_true",
                        help="the second variant is `mitigated`, as new_demo.py --mitigated names it")
    args = parser.parse_args()
    name = Path(args.demo.rstrip("/")).name
    if not name.endswith("-demo"):
        parser.error("the demo's folder ends in -demo, e.g. demos/xss-demo")
    target = ROOT / "demos" / name / "docs" / "diagrams.py"
    if target.exists():
        print(f"{target.relative_to(ROOT)} already exists; nothing written.")
        return 1
    style = (HERE / "diagram_style.py").read_text(encoding="utf-8")
    start = style.index("# --- house style")
    end = style.index("\n", style.index("# --- end house style")) + 1
    second = "mitigated" if args.mitigated else "safe"
    figures = keep_blocks(FIGURES, {"postgres"} if args.postgres else set())
    figures = (figures.replace("__NAME__", name)
               .replace("__Safe__", second.capitalize()).replace("__safe__", second))
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(HEAD + style[start:end] + figures, encoding="utf-8", newline="\n")
    print(f"wrote {target.relative_to(ROOT)}")
    print(f"next: python demos/{name}/docs/diagrams.py, then redraw the figures for your attack")
    return 0


if __name__ == "__main__":
    sys.exit(main())
