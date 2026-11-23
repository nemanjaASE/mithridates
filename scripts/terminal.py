"""Terminal output for the repository's scripts: the logo, colors and progress steps.

On an interactive terminal a running step shows a spinner and every line is colored. In CI
or a pipe each step prints one plain line when it ends, and `NO_COLOR` turns colors off.
`FORCE_COLOR` keeps the terminal look in a pipe, which is how docs/assets/terminal.py
records the screenshots in the READMEs.
"""
from __future__ import annotations

import os
import re
import sys
import threading
import time
from pathlib import Path
from types import TracebackType
from typing import TextIO

RED, GREEN, YELLOW, GRAY = "229;83;75", "63;185;80", "210;153;34", "139;148;158"

# The logo in docs/assets/logo.svg: a drop of poison above a Greek eye-cup with one red
# and one green eye. {r}, {g} and {c} open a color (drop, safe eye, cup); {x} closes it.
LOGO = (
    "           {r}▗█▖{x}",
    "          {r}▟███▙{x}",
    "          {r}▜███▛{x}",
    "{c}╭╮━━━━━━━━━━━━━━━━━━━━━╭╮{x}",
    "{c}╰┤     <{x}{r}●{x}{c}>     <{x}{g}●{x}{c}>     ├╯{x}",
    "{c}  ╲                   ╱{x}",
    "{c}   ╲▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁╱{x}",
    "{c}            ┃{x}",
    "{c}        ━━━━┻━━━━{x}",
)
LOGO_CENTER = 12  # the column of the stem, the drop and the space between the eyes
# The same logo beside the text, for the commands that are run often: six lines, not thirteen.
LOGO_COMPACT = (
    "      {r}▗█▖{x}",
    "      {r}▜█▛{x}",
    "{c}╭╮━━━━━━━━━━━╭╮{x}",
    "{c}╰┤ <{x}{r}●{x}{c}>   <{x}{g}●{x}{c}> ├╯{x}",
    "{c}  ╲▁▁▁▁▁▁▁▁▁╱{x}",
    "{c}     ━━┻━━{x}",
)
COMPACT_TEXT_ROW = 2  # the text starts beside the rim
WORDMARK = "M I T H R I D A T E S"
TAGLINE = "Small, controlled doses of real attacks."

FANCY = {"spin": "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏", "ok": "✔", "warn": "▲", "fail": "✘", "dot": "·", "arrow": "→",
         "on": "●", "off": "○"}
PLAIN = {"spin": "|/-\\", "ok": "+", "warn": "!", "fail": "x", "dot": "-", "arrow": "->",
         "on": "*", "off": "-"}


def _ansi_ready(stream: TextIO) -> bool:
    """Whether `stream` is a terminal that understands ANSI escapes, enabling them on Windows."""
    if not stream.isatty():
        return False
    if os.name != "nt":
        return True
    try:
        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)  # standard output
        mode = wintypes.DWORD()
        if not kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            return False
        return bool(kernel32.SetConsoleMode(handle, mode.value | 0x0004))  # virtual terminal
    except (AttributeError, OSError):
        return False


def _encodable(stream: TextIO, text: str) -> bool:
    """Whether `stream` can print `text` in its encoding."""
    try:
        text.encode(stream.encoding or "ascii")
    except (UnicodeEncodeError, LookupError):
        return False
    return True


def _project() -> tuple[str, str]:
    """The version and the repository address, from CITATION.cff; empty when unreadable."""
    try:
        citation = (Path(__file__).resolve().parent.parent / "CITATION.cff").read_text(encoding="utf-8")
    except OSError:
        return "", ""
    version = re.search(r'^version:\s*"?([^"\n]+?)"?\s*$', citation, re.M)
    address = re.search(r'^repository-code:\s*"?([^"\n]+?)"?\s*$', citation, re.M)
    return (version.group(1) if version else "",
            address.group(1).removeprefix("https://") if address else "")


class Terminal:
    """Prints the scripts' output, with color and a spinner where the terminal allows them."""

    def __init__(self, stream: TextIO | None = None) -> None:
        stream = stream or sys.stdout
        # Git Bash's mintty reaches Python through a pipe, so it does not look like a
        # terminal; it does understand ANSI escapes and UTF-8.
        mintty = os.environ.get("TERM_PROGRAM") == "mintty" and not stream.isatty()
        if mintty and hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
        self.stream = stream
        forced = bool(os.environ.get("FORCE_COLOR"))
        self.live = forced or mintty or _ansi_ready(stream)
        self.color = self.live and "NO_COLOR" not in os.environ
        self.unicode = _encodable(stream, "".join(LOGO) + "".join(FANCY.values()))
        self.glyph = FANCY if self.unicode else PLAIN
        self.width = 34  # the label column of a step; the note starts after it

    def paint(self, text: str, rgb: str = "", bold: bool = False, dim: bool = False) -> str:
        """Returns `text` wrapped in the escapes for a color and a weight, if colors are on."""
        if not self.color:
            return text
        codes = [f"38;2;{rgb}"] if rgb else []
        codes += ["1"] if bold else []
        codes += ["2"] if dim else []
        return f"\033[{';'.join(codes)}m{text}\033[0m" if codes else text

    def line(self, text: str = "") -> None:
        """Prints one line, replacing what the stream's encoding cannot show."""
        if not self.unicode:
            encoding = self.stream.encoding or "ascii"
            text = text.encode(encoding, "replace").decode(encoding)
        print(text, file=self.stream, flush=True)

    def banner(self, compact: bool = False, note: str = "") -> None:
        """Prints the logo with the wordmark, the tagline, and the version and address.

        Args:
            compact: Put the logo beside the text instead of above it, for the commands
                that are run often.
            note: A line printed under the rest, in muted red, such as a warning.
        """
        version, address = _project()
        about = f" {self.glyph['dot']} ".join(p for p in (version and f"v{version}", address) if p)
        text = [(WORDMARK, True), (TAGLINE, False), *([(about, False)] if about else [])]
        painted = [self.paint(t, bold=True) if bold else self.paint(t, dim=True) for t, bold in text]
        on = {"r": RED, "g": GREEN, "c": GRAY}
        if self.color:
            colors = {k: f"\033[38;2;{v}m" for k, v in on.items()} | {"x": "\033[0m"}
        else:
            colors = dict.fromkeys([*on, "x"], "")
        self.line()
        if compact and self.unicode:
            plain = [re.sub(r"\{[rgcx]\}", "", row) for row in LOGO_COMPACT]
            width = max(len(row) for row in plain)
            for i, row in enumerate(LOGO_COMPACT):
                at = i - COMPACT_TEXT_ROW
                beside = painted[at] if 0 <= at < len(painted) else ""
                gap = " " * (width - len(plain[i]) + 4)
                self.line(f"  {row.format(**colors)}{gap}{beside}".rstrip())
        else:
            center = 2 + len(TAGLINE) // 2
            if self.unicode:
                for row in LOGO:
                    self.line(" " * (center - LOGO_CENTER) + row.format(**colors))
                self.line()
            for (raw, _), shown in zip(text, painted, strict=True):
                self.line(" " * max(2, center - len(raw) // 2) + shown)
        if note:
            self.line()
            self.line("  " + self.paint(note, RED, dim=True))
        self.line()

    def step(self, running: str, finished: str = "") -> Step:
        """Returns a step to run in a `with` block: a spinner while it runs, a mark when it ends.

        Args:
            running: The label next to the spinner, such as "Copying the template".
            finished: The label next to the mark, such as "Copied the template"; by default
                the running one.
        """
        return Step(self, running, finished or running)


class Step:
    """One unit of work, shown with a spinner while it runs and a mark when it ends."""

    def __init__(self, terminal: Terminal, running: str, finished: str) -> None:
        self.terminal = terminal
        self.running = running
        self.label = finished
        self.detail = ""
        self.problem = ""
        self.failed = False
        self.started = 0.0
        self._stop = threading.Event()
        self._spinner: threading.Thread | None = None

    def done(self, detail: str = "") -> None:
        """Sets the note printed next to the step when it ends."""
        self.detail = detail

    def warn(self, problem: str, detail: str = "") -> None:
        """Marks the step as ended with a problem the user has to fix by hand."""
        self.problem, self.detail = problem, detail

    def fail(self, problem: str, detail: str = "") -> None:
        """Marks the step as failed, and prints `problem` under it."""
        self.problem, self.detail, self.failed = problem, detail, True

    def __enter__(self) -> Step:
        self.started = time.monotonic()
        if self.terminal.live:
            self.terminal.stream.write("\033[?25l")  # hide the cursor
            self._spinner = threading.Thread(target=self._spin, daemon=True)
            self._spinner.start()
        return self

    def _spin(self) -> None:
        frames = self.terminal.glyph["spin"]
        i = 0
        while not self._stop.wait(0.08):
            frame = self.terminal.paint(frames[i % len(frames)], GRAY)
            self.terminal.stream.write(f"\r  {frame} {self.running} ...")
            self.terminal.stream.flush()
            i += 1

    def __exit__(self, kind: type[BaseException] | None, error: BaseException | None,
                 trace: TracebackType | None) -> None:
        if self._spinner:
            self._stop.set()
            self._spinner.join()
            self.terminal.stream.write("\r\033[2K\033[?25h")  # clear the line, show the cursor
        t, g = self.terminal, self.terminal.glyph
        seconds = time.monotonic() - self.started
        timing = f"{seconds:.1f}s" if seconds >= 0.5 else ""
        note = f" {g['dot']} ".join(part for part in (self.detail, timing) if part)
        shown = self.running if error is not None or self.problem else self.label
        if error is not None or self.failed:
            mark, label = t.paint(g["fail"], RED, bold=True), t.paint(shown, RED)
        elif self.problem:
            mark, label = t.paint(g["warn"], YELLOW, bold=True), shown
        else:
            mark, label = t.paint(g["ok"], GREEN, bold=True), shown
        gap = " " * max(1, t.width - len(shown)) if note else ""
        t.line(f"  {mark} {label}{gap}{t.paint(note, dim=True)}")
        if self.problem:
            for row in self.problem.strip().splitlines():
                t.line("      " + t.paint(row, RED if self.failed else YELLOW))
