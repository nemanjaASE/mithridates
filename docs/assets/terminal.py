"""Draws the terminal screenshots in the READMEs from what the scripts really print.

    uv run --no-project --with pyyaml python docs/assets/terminal.py

Every shot runs a command with `FORCE_COLOR` set, so the script prints exactly what it
prints on a terminal, replays that output on a character grid, and has headless Chrome
photograph the grid into `docs/assets/terminal/<name>.png`. Block and box-drawing
characters are drawn as shapes instead of being taken from a font, the way modern
terminals draw them, so the logo comes out the same on every machine.

- `new-demo` and `check-repo` run in a temporary copy of the repository: the generator
  creates a demo there, and check_repo.py then reports the markers it left.
- `lab-status` shows example Docker data, so the picture does not depend on what happens
  to be running on the machine that draws it.
- `demo-up` is the output of a real `docker compose up`, kept below as text.

Needs Chrome, Chromium or Edge (set `CHROME` if it is not found) and the Cascadia Mono font.
"""
from __future__ import annotations

import html
import io
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "terminal"
SKIP = shutil.ignore_patterns(".git", ".venv", "__pycache__", ".ruff_cache", ".mypy_cache",
                              "node_modules")

FONT_PX, LINE_PX, CELL_PX = 16, 20, 9.375  # Cascadia Mono advances 0.586 em per character
TEXT, DIM, BACK = "201,209,217", "139,148,158", "#0d1117"
SGR = re.compile(r"\x1b\[([0-9;?]*)([A-Za-z])")

# docker compose up --build sqli-demo, a real run: the containers' final states and the
# service log, in the order compose printed them.
DEMO_UP = """\
Attaching to sqli-demo-1
 Container mithridates-sqli-db-1 Healthy
 Container mithridates-sqli-seed-1 Exited
 Container mithridates-sqli-demo-1 Started
{p}sqli-demo-1  |{x} INFO:     Started server process [1]
{p}sqli-demo-1  |{x} INFO:     Waiting for application startup.
{p}sqli-demo-1  |{x} INFO:     Application startup complete.
{p}sqli-demo-1  |{x} INFO:     Mithridates · sqli-demo is ready → {b}http://127.0.0.1:8001/docs{x}
"""

# Block and box-drawing characters as shapes on a 10 x 20 cell. Each shape bleeds a little
# into its neighbours, so two cells side by side show no seam between them.
BLEED = 0.4
_Q = {"ul": (0, 0), "ur": (5, 0), "ll": (0, 10), "lr": (5, 10)}


def _rect(x: float, y: float, w: float, h: float) -> str:
    return (f'<rect x="{x - BLEED}" y="{y - BLEED}" width="{w + 2 * BLEED}" '
            f'height="{h + 2 * BLEED}"/>')


def _rects(*parts: str) -> str:
    return "".join(_rect(*_Q[p], 5, 10) for p in parts)


def _path(d: str, heavy: bool = False) -> str:
    width = 2.4 if heavy else 1.2
    return f'<path d="{d}" fill="none" stroke="currentColor" stroke-width="{width}"/>'


SHAPES = {
    "█": _rect(0, 0, 10, 20),
    "▀": _rect(0, 0, 10, 10),
    "▄": _rect(0, 10, 10, 10),
    "▁": _rect(0, 17.5, 10, 2.1),
    "▘": _rects("ul"), "▝": _rects("ur"), "▖": _rects("ll"), "▗": _rects("lr"),
    "▙": _rects("ul", "ll", "lr"), "▟": _rects("ur", "ll", "lr"),
    "▛": _rects("ul", "ur", "ll"), "▜": _rects("ul", "ur", "lr"),
    "━": _path("M-0.5 10H10.5", heavy=True),
    "┃": _path("M5 -0.5V20.5", heavy=True),
    "┻": _path("M-0.5 10H10.5M5 -0.5V10", heavy=True),
    "┤": _path("M5 -0.5V20.5M-0.5 10H5"),
    "├": _path("M5 -0.5V20.5M5 10H10.5"),
    "╭": _path("M10.5 10H10A5 5 0 0 0 5 15V20.5"),
    "╮": _path("M-0.5 10H0A5 5 0 0 1 5 15V20.5"),
    "╰": _path("M5 -0.5V5A5 5 0 0 0 10 10H10.5"),
    "╯": _path("M5 -0.5V5A5 5 0 0 1 0 10H-0.5"),
    "╲": _path("M0 0L10 20"),
    "╱": _path("M10 0L0 20"),
}


def replay(text: str) -> list[list[tuple[str, tuple]]]:
    """Plays terminal output onto a grid: carriage returns overwrite, `ESC[2K` clears a line.

    Args:
        text: The output, with its escape sequences.

    Returns:
        One list of (character, style) cells per line; a style is (rgb, bold, dim).
    """
    lines: list[list[tuple[str, tuple]]] = [[]]
    col, rgb, bold, dim = 0, "", False, False
    at = 0
    for match in [*SGR.finditer(text), None]:
        end = match.start() if match else len(text)
        for ch in text[at:end]:
            if ch == "\n":
                lines.append([])
                col = 0
            elif ch == "\r":
                col = 0
            else:
                row = lines[-1]
                row.extend([(" ", ("", False, False))] * (col + 1 - len(row)))
                row[col] = (ch, (rgb, bold, dim))
                col += 1
        if match is None:
            break
        at = match.end()
        codes, kind = match.group(1), match.group(2)
        if kind == "K" and codes == "2":
            lines[-1] = []
        elif kind == "m":
            parts = codes.split(";") if codes else ["0"]
            i = 0
            while i < len(parts):
                if parts[i] == "0":
                    rgb, bold, dim = "", False, False
                elif parts[i] == "1":
                    bold = True
                elif parts[i] == "2":
                    dim = True
                elif parts[i] == "38" and i + 4 < len(parts):
                    rgb, i = ",".join(parts[i + 2:i + 5]), i + 4
                i += 1
    while lines and not any(ch.strip() for ch, _ in lines[-1]):
        lines.pop()
    return lines


def cell_html(ch: str) -> str:
    """One character: a drawn shape, a fixed-width symbol, or plain text."""
    if ch in SHAPES:
        return (f'<svg class="g" viewBox="0 0 10 20" preserveAspectRatio="none" '
                f'fill="currentColor">{SHAPES[ch]}</svg>')
    if ord(ch) > 0x7E:
        return f'<span class="w">{html.escape(ch)}</span>'
    return html.escape(ch)


def page(title: str, command: str, lines: list[list[tuple[str, tuple]]]) -> tuple[str, int, int]:
    """Lays the grid out in a terminal window.

    Returns:
        The HTML, and the width and height of the window in CSS pixels.
    """
    prompt = [("$", ("63,185,80", True, False)), (" ", ("", False, False))]
    prompt += [(ch, ("", True, False)) for ch in command]
    rows = [prompt, *lines]
    out = []
    for row in rows:
        spans, current, chunk = [], None, []
        for ch, style in [*row, (None, None)]:
            if style != current and chunk:
                rgb, bold, dim = current
                css = [f"color:rgb({rgb or (DIM if dim else TEXT)})"]
                css += ["font-weight:700"] if bold else []
                css += ["opacity:.6"] if dim and rgb else []
                spans.append(f'<span style="{";".join(css)}">{"".join(chunk)}</span>')
                chunk = []
            if ch is None:
                break
            current = style
            chunk.append(cell_html(ch))
        out.append("".join(spans))
    cols = max(len(row) for row in rows)
    width = math.ceil(cols * CELL_PX) + 2 * 22 + 2
    height = len(rows) * LINE_PX + 34 + 16 + 20 + 2
    doc = f"""<!doctype html><meta charset="utf-8"><style>
html,body{{margin:0;background:transparent}}
.win{{width:{width - 2}px;background:{BACK};border:1px solid #30363d;border-radius:10px;overflow:hidden}}
.bar{{height:34px;background:#161b22;border-bottom:1px solid #21262d;position:relative}}
.bar i{{position:absolute;top:12px;width:11px;height:11px;border-radius:50%}}
.bar span{{display:block;text-align:center;font:13px/34px system-ui,sans-serif;color:#8b949e}}
pre{{margin:0;padding:16px 22px 20px;font:{FONT_PX}px/{LINE_PX}px "Cascadia Mono",monospace;color:rgb({TEXT})}}
.g,.w{{display:inline-block;width:1ch;height:{LINE_PX}px;vertical-align:top;overflow:visible}}
.w{{text-align:center;line-height:{LINE_PX}px}}
</style><div class="win"><div class="bar"><i style="left:14px;background:#ff5f57"></i>
<i style="left:32px;background:#febc2e"></i><i style="left:50px;background:#28c840"></i>
<span>{html.escape(title)}</span></div><pre>{chr(10).join(out)}</pre></div>"""
    return doc, width, height


def chrome() -> str:
    """The browser that takes the screenshots."""
    candidates = [os.environ.get("CHROME", ""), "chrome", "google-chrome", "chromium",
                  "chromium-browser", "msedge",
                  r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                  r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"]
    for candidate in candidates:
        if candidate and (shutil.which(candidate) or Path(candidate).exists()):
            return shutil.which(candidate) or candidate
    sys.exit("No Chrome, Chromium or Edge found; set CHROME to the executable.")


def shoot(name: str, title: str, command: str, output: str) -> None:
    """Writes `docs/assets/terminal/<name>.png`."""
    doc, width, height = page(title, command, replay(output))
    with tempfile.TemporaryDirectory() as tmp:
        source = Path(tmp) / f"{name}.html"
        source.write_text(doc, encoding="utf-8")
        target = OUT / f"{name}.png"
        subprocess.run([chrome(), "--headless", "--disable-gpu", "--hide-scrollbars",
                        "--force-device-scale-factor=2", "--default-background-color=00000000",
                        f"--window-size={width},{height}", f"--screenshot={target}",
                        source.as_uri()], check=True, capture_output=True)
    print(f"  {target.relative_to(ROOT).as_posix()}  {width * 2}x{height * 2}")


def run(command: list[str], cwd: Path) -> str:
    """Runs a script as a terminal would see it and returns what it printed."""
    env = os.environ | {"FORCE_COLOR": "1", "PYTHONIOENCODING": "utf-8"}
    env.pop("NO_COLOR", None)
    # Bytes, not text: text mode would turn the spinner's carriage returns into new lines.
    result = subprocess.run(command, cwd=cwd, env=env, capture_output=True)
    return result.stdout.decode("utf-8").replace(chr(13) + chr(10), chr(10))


def lab_status() -> str:
    """`lab.py status` on example data: one demo running, one image left over."""
    sys.path.insert(0, str(ROOT / "scripts"))
    import lab
    import terminal

    lab.ROOT = PurePosixPath("~/mithridates")
    lab.lab_projects = lambda: {"mithridates": [
        {"Names": "mithridates-sqli-demo-1", "State": "running"},
        {"Names": "mithridates-sqli-db-1", "State": "running"},
        {"Names": "mithridates-sqli-seed-1", "State": "exited"},
    ]}
    lab.lab_images = lambda: [
        {"Repository": "mithridates/sqli-demo", "Tag": "local", "Size": "292MB", "leftover": False},
        {"Repository": "mithridates/promptinj-demo", "Tag": "local", "Size": "437MB", "leftover": False},
        {"Repository": "mithridates/xss-demo", "Tag": "local", "Size": "276MB", "leftover": True},
    ]
    lab.model_volumes = lambda: [{"Name": "mithridates-ollama-models"}]

    class Tty(io.TextIOWrapper):
        def isatty(self) -> bool:
            return True

    raw = io.BytesIO()
    stream = Tty(raw, encoding="utf-8", newline="\n", write_through=True)
    os.environ["FORCE_COLOR"] = "1"
    ui = terminal.Terminal(stream)
    ui.banner()
    lab.status(ui)
    return raw.getvalue().decode("utf-8")


def main() -> int:
    OUT.mkdir(exist_ok=True)
    print("Drawing the terminal screenshots:")
    with tempfile.TemporaryDirectory() as tmp:
        copy = Path(tmp) / "mithridates"
        shutil.copytree(ROOT, copy, ignore=SKIP)
        generate = [sys.executable, "scripts/new_demo.py", "xss", "--title", "Cross-site scripting",
                    "--postgres"]
        output = run(generate, copy)
        shoot("new-demo", "~/mithridates", 'python scripts/new_demo.py xss --title "Cross-site scripting" --postgres', output)
        output = run([sys.executable, "scripts/check_repo.py"], copy)
        shoot("check-repo", "~/mithridates", "uv run --no-project --with pyyaml python scripts/check_repo.py", output)
    shoot("lab-status", "~/mithridates", "python scripts/lab.py status", lab_status())
    colors = {"p": "\x1b[38;2;57;197;207m", "b": "\x1b[1m", "x": "\x1b[0m"}
    shoot("demo-up", "~/mithridates", "docker compose up --build sqli-demo", DEMO_UP.format(**colors))
    return 0


if __name__ == "__main__":
    sys.exit(main())
