"""Check the figures drawn in the house style.

    python .claude/skills/house-style-figures/check_figures.py

For every demo whose docs/diagrams.py carries the house-style block: the block is an exact
copy of diagram_style.py next to this file; no label sits on a line, crosses a box edge,
comes within 8px of the edge of the box it sits in or 5px of a box beside it, or runs
into the caption or the 56px margin; every segment is horizontal or vertical; every
arrow ends on a box; boxes keep 16px apart; the drawing ends 40px above the caption; no
demo names another; no figure code redefines a name the style uses; and the palette holds
WCAG contrast. A demo that draws its figures some other way is not looked at.

These used to run in scripts/check_repo.py. The house style is not a rule for
contributors — only the C4 model is — so they live with the style, and run when the
figures that use it change.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent
ROOT = SKILL.parents[2]
STYLE = SKILL / "diagram_style.py"
STYLE_OPEN = "# --- house style"
STYLE_CLOSE = "# --- end house style"


class Report:
    """Failures grouped by the file or demo they belong to."""

    def __init__(self) -> None:
        self.failures: dict[str, list[str]] = {}
        self.count = 0

    def check(self, subject: str, ok: object, message: str) -> bool:
        self.count += 1
        if not ok:
            self.failures.setdefault(subject, []).append(message)
        return bool(ok)

    def print(self, subjects: list[str]) -> int:
        for subject in subjects:
            problems = self.failures.get(subject)
            if problems:
                print(f"  {subject:<18} FAIL")
                for problem in problems:
                    print(f"      - {problem}")
            else:
                print(f"  {subject:<18} ok")
        failed = sum(len(v) for v in self.failures.values())
        print()
        total = f"{self.count} checks"
        print(f"{total}, {failed} failed" if failed else f"{total}, all passed")
        return 1 if failed else 0


def house_style(path: Path) -> str | None:
    """The block every diagrams.py copies from diagram_style.py, markers included."""
    if not path.exists():
        return None
    body = path.read_text(encoding="utf-8")
    start = body.find(STYLE_OPEN)
    end = body.find(STYLE_CLOSE)
    return body[start:end] if start >= 0 and end > start else None


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def _attrs(blob: str) -> dict[str, str]:
    return dict(re.findall(r'([\w-]+)="([^"]*)"', blob))


def check_figures(demos: list[Path], report: Report) -> None:
    """The geometry docs/templates/demo-readme.md promises, measured rather than eyeballed.

    No label on a line, across a box edge, into the caption or off the sheet; every drawn
    segment horizontal or vertical; every arrow ending on a box.
    """
    for demo in demos:
        for svg_path in sorted((demo / "docs").glob("*.svg")):
            svg = svg_path.read_text(encoding="utf-8")
            where = rel(svg_path)
            size = re.search(r'width="(\d+)" height="(\d+)"', svg)
            if not size:
                continue
            width, height = int(size.group(1)), int(size.group(2))

            texts = []
            for raw, body in re.findall(r"<text ([^>]*)>([^<]*)</text>", svg):
                a = _attrs(raw)
                fs = float(a.get("font-size", 12))
                w = float(a["textLength"]) if "textLength" in a else len(body) * fs * 0.55
                x = float(a["x"])
                anchor = a.get("text-anchor", "start")
                x -= w if anchor == "end" else w / 2 if anchor == "middle" else 0
                y = float(a["y"])
                texts.append((x, y - fs * 0.78, x + w, y + fs * 0.22, body.strip()[:30]))
            texts = texts[:-2]                       # the caption's own two lines

            frames = []
            for raw in re.findall(r"<rect ([^>]*)/>", svg):
                a = _attrs(raw)
                if "x" in a and float(a.get("width", 0)) < width - 10:
                    fx, fy = float(a["x"]), float(a["y"])
                    frames.append((fx, fy, fx + float(a["width"]), fy + float(a["height"])))

            segments, arrow_ends = [], []
            for raw in re.findall(r"<polyline ([^>]*)/>", svg):
                a = _attrs(raw)
                pts = [tuple(map(float, pt.split(","))) for pt in a["points"].split()]
                segments += list(zip(pts, pts[1:], strict=False))
                if "marker-end" in a:
                    arrow_ends.append(pts[-1])

            # every drawing ends 40px above the caption rule — boxes and lines too, not only text
            rule = height - 58
            drawn = [y2 for _, _, _, y2, _ in texts] + [f[3] for f in frames] + [
                max(ay, by) for (ax, ay), (bx, by) in segments
                if not (abs(ay - rule) < 1 and abs(by - rule) < 1)]
            lowest = max(drawn, default=0)
            report.check("figures", lowest <= rule - 40 + 1,
                         f"{where}: the drawing comes within {rule - lowest:.0f}px of the"
                         " caption rule; it must end 40px above it")

            # a figure is about its own demo: another demo's name in it is a copy-paste slip
            for other in demos:
                if other != demo:
                    report.check("figures", other.name not in svg,
                                 f"{where}: mentions {other.name}")

            # boxes keep apart: one sits inside another (a panel around its parts) or 16px clear
            for i, (x1, y1, x2, y2) in enumerate(frames):
                for x3, y3, x4, y4 in frames[i + 1:]:
                    inside = (x1 <= x3 and y1 <= y3 and x4 <= x2 and y4 <= y2) or (
                        x3 <= x1 and y3 <= y1 and x2 <= x4 and y2 <= y4)
                    gap = max(x3 - x2, x1 - x4, y3 - y2, y1 - y4)
                    report.check("figures", inside or gap >= 16,
                                 f"{where}: two boxes at ({x1:.0f},{y1:.0f}) and ({x3:.0f},{y3:.0f})"
                                 f" are {gap:.0f}px apart")

            # every arrow arrives at its own point
            for i, (px, py) in enumerate(arrow_ends):
                for qx, qy in arrow_ends[i + 1:]:
                    report.check("figures", abs(px - qx) + abs(py - qy) >= 12,
                                 f"{where}: two arrows end at ({px:.0f},{py:.0f})")

            for (ax, ay), (bx, by) in segments:
                report.check("figures", abs(ax - bx) < 0.5 or abs(ay - by) < 0.5,
                             f"{where}: a line runs at an angle ({ax:.0f},{ay:.0f})"
                             f" → ({bx:.0f},{by:.0f})")

            def near_box(px: float, py: float, frames: list = frames) -> bool:
                for x1, y1, x2, y2 in frames:
                    dx = max(x1 - px, 0, px - x2)
                    dy = max(y1 - py, 0, py - y2)
                    if (dx * dx + dy * dy) ** 0.5 <= 8:
                        return True
                return False

            for px, py in arrow_ends:
                report.check("figures", near_box(px, py),
                             f"{where}: an arrow ends in empty space at ({px:.0f},{py:.0f})")

            for i, (x1, y1, x2, y2, t) in enumerate(texts):
                report.check("figures", x1 >= 56 - 1 and x2 <= width - 56 + 1,
                             f"{where}: {t!r} runs into the 56px margin")
                report.check("figures", y2 <= height - 62, f"{where}: {t!r} runs into the caption")
                for x3, y3, x4, y4, t2 in texts[i + 1:]:
                    report.check("figures",
                                 not (x1 < x4 - 1 and x3 < x2 - 1 and y1 < y4 - 1 and y3 < y2 - 1),
                                 f"{where}: {t!r} overlaps {t2!r}")
                for fx1, fy1, fx2, fy2 in frames:
                    overlaps = x1 < fx2 and fx1 < x2 and y1 < fy2 and fy1 < y2
                    inside = fx1 <= x1 and x2 <= fx2 and fy1 <= y1 and y2 <= fy2
                    report.check("figures", not overlaps or inside,
                                 f"{where}: {t!r} crosses the edge of a box")
                    # beside a box it is not in, it keeps 5px clear of the box
                    gap = max(fx1 - x2, x1 - fx2)
                    report.check("figures", inside or not (y1 < fy2 and fy1 < y2) or not 0 <= gap < 5,
                                 f"{where}: {t!r} comes within 5px of a box beside it")
                # and inside the box it sits in, it keeps 8px clear of the left and right edge
                holders = [f for f in frames
                           if f[0] <= x1 and x2 <= f[2] and f[1] <= y1 and y2 <= f[3]]
                if holders:
                    fx1, _, fx2, _ = min(holders, key=lambda f: (f[2] - f[0]) * (f[3] - f[1]))
                    report.check("figures", x1 >= fx1 + 8 and x2 <= fx2 - 8,
                                 f"{where}: {t!r} comes within 8px of the edge of its box")
                for (ax, ay), (bx, by) in segments:
                    flat = abs(ay - by) < 1 and y1 - 2 < ay < y2 + 2 and min(ax, bx) < x2 and x1 < max(ax, bx)
                    tall = abs(ax - bx) < 1 and x1 - 2 < ax < x2 + 2 and min(ay, by) < y2 and y1 < max(ay, by)
                    report.check("figures", not (flat or tall), f"{where}: {t!r} sits on a line")


def check_shadowing(demos: list[Path], report: Report) -> None:
    """A demo's own figure code must not reuse a name the house style defines: `NAME = ...`
    after the copied block silently replaces the style's text size, and the figures break
    in ways that are hard to trace back."""
    style = STYLE.read_text(encoding="utf-8")
    block = style[style.index("# --- house style"):style.index("# --- end house style")]
    taken = {n for names in re.findall(r"^([A-Za-z_]\w*(?:, [A-Za-z_]\w*)*) = ", block, re.M)
             for n in names.split(", ")}
    taken |= set(re.findall(r"^def (\w+)\(", block, re.M))
    for demo in demos:
        path = demo / "docs" / "diagrams.py"
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        marker = "# --- end house style"
        if marker not in text:
            continue
        own = text[text.index(marker):]
        mine = {n for names in re.findall(r"^([A-Za-z_]\w*(?:, [A-Za-z_]\w*)*) = ", own, re.M)
                for n in names.split(", ")}
        mine |= set(re.findall(r"^def (\w+)\(", own, re.M))
        for name in sorted(mine & taken):
            report.check("figures", False,
                         f"{rel(path)}: `{name}` is already defined by the house style;"
                         " choose another name")
        report.check("figures", True, f"{rel(path)}: no house-style name redefined")


def _luminance(colour: str) -> float:
    def channel(c: float) -> float:
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (int(colour[i:i + 2], 16) / 255 for i in (1, 3, 5))
    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)


def _contrast(a: str, b: str) -> float:
    hi, lo = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def check_palette(report: Report) -> None:
    """The figures' palette promises WCAG contrast: text 4.5:1 and box edges and lines 3:1
    (non-text, 1.4.11) on every ground a figure draws on."""
    style = STYLE.read_text(encoding="utf-8")
    colour = dict(re.findall(r'^([A-Z_]+) = "(#[0-9A-Fa-f]{6})"', style, re.M))
    grounds = ("PAPER", "FILL", "OUT", "ACCENT_FILL", "SAFE_FILL")
    rules = (
        (("INK", "MUTED", "TECH", "ACCENT", "SAFE"), grounds, 4.5, "text"),
        (("EDGE", "LINE"), grounds, 3, "a line"),
    )
    for names, grounds, need, what in rules:
        for name in names:
            for ground in grounds:
                ratio = _contrast(colour[name], colour[ground])
                report.check("figures", ratio >= need,
                             f"diagram_style.py: {name} on {ground} is {ratio:.2f}:1,"
                             f" {what} needs {need}:1")


def check_copies(styled: list[Path], report: Report) -> None:
    """Each demo's copy of the house-style block is the block in diagram_style.py."""
    for demo in styled:
        report.check("figures", house_style(demo / "docs" / "diagrams.py") == house_style(STYLE),
                     f"{demo.name}: the house-style block in docs/diagrams.py differs from"
                     f" {rel(STYLE)} — copy it across again")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    demos = sorted(p for p in (ROOT / "demos").iterdir() if p.is_dir() and p.name.endswith("-demo"))
    styled = [d for d in demos if house_style(d / "docs" / "diagrams.py") is not None]
    report = Report()
    check_copies(styled, report)
    check_figures(styled, report)
    check_palette(report)
    check_shadowing(styled, report)
    print(f"house-style figures ({', '.join(d.name for d in styled) or 'no demo uses the style'})")
    print()
    return report.print(["figures"])


if __name__ == "__main__":
    sys.exit(main())
